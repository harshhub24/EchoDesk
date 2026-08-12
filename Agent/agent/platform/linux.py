"""Linux (primary target: Linux Mint) platform backend.

Uses standard command-line tools available on virtually every systemd-based
distro (Linux Mint / Ubuntu / Debian family): systemctl for power actions,
loginctl for locking the session, notify-send for messages, and scrot/import
(via mss, cross-platform) for screenshots.
"""

from __future__ import annotations

import logging
import os
import platform as stdlib_platform
import subprocess

logger = logging.getLogger("agent.platform.linux")


def _run(command: list[str], check: bool = False) -> subprocess.CompletedProcess | None:
    logger.info("Running: %s", " ".join(command))
    try:
        return subprocess.run(command, check=check, capture_output=True, text=True)
    except FileNotFoundError:
        logger.warning("Command not found: %s (is it installed on this system?)", command[0])
        return None


def lock() -> None:
    # loginctl works across most systemd-based session managers (Cinnamon on
    # Linux Mint included) without needing a desktop-specific lock command.
    result = _run(["loginctl", "lock-session"])
    if result is None or result.returncode != 0:
        # Fall back to a common Cinnamon/GNOME screensaver command.
        _run(["cinnamon-screensaver-command", "--lock"])


def restart() -> None:
    _run(["systemctl", "reboot"])


def shutdown() -> None:
    _run(["systemctl", "poweroff"])


def sleep() -> None:
    _run(["systemctl", "suspend"])


def hibernate() -> None:
    _run(["systemctl", "hibernate"])


def logout() -> None:
    # loginctl terminate-session requires a session ID; terminate-user is the
    # broadly-applicable equivalent for "log this user out everywhere".
    user = os.environ.get("USER") or os.environ.get("LOGNAME")
    if user:
        _run(["loginctl", "terminate-user", user])
    else:
        _run(["loginctl", "terminate-session", os.environ.get("XDG_SESSION_ID", "")])


def show_message(title: str, message: str) -> None:
    result = _run(["notify-send", title, message])
    if result is None or result.returncode != 0:
        logger.warning("notify-send unavailable or failed; message not shown on-screen: %s - %s", title, message)


def take_screenshot(destination_path: str) -> str:
    # mss is cross-platform and does not require a screenshot CLI tool to be
    # installed, which keeps this reliable on minimal/headless-adjacent Mint
    # installs.
    import mss
    import mss.tools

    with mss.mss() as sct:
        monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
        shot = sct.grab(monitor)
        mss.tools.to_png(shot.rgb, shot.size, output=destination_path)
    return destination_path


def kernel_version() -> str:
    return stdlib_platform.release()


def os_version() -> str:
    try:
        with open("/etc/os-release", encoding="utf-8") as handle:
            values = dict(
                line.strip().split("=", 1) for line in handle if "=" in line and not line.startswith("#")
            )
        pretty_name = values.get("PRETTY_NAME", "").strip('"')
        if pretty_name:
            return pretty_name
    except OSError:
        pass
    return f"{stdlib_platform.system()} {stdlib_platform.release()}"
