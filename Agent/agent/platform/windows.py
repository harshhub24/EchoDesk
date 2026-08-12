"""Windows 10/11 platform backend.

Uses built-in shutdown.exe for power actions (no admin prompt needed for the
current user's own session actions), rundll32 for locking, ctypes MessageBox
for on-screen messages, and mss for screenshots.

Imports of Windows-only modules (ctypes.wintypes usage stays stdlib-only; no
pywin32 required for anything in this file, so this module still *imports*
cleanly on non-Windows for static analysis/tests, even though calling its
functions on a non-Windows OS will fail).
"""

from __future__ import annotations

import ctypes
import logging
import platform as stdlib_platform
import subprocess

logger = logging.getLogger("agent.platform.windows")


def _run(command: list[str]) -> subprocess.CompletedProcess:
    logger.info("Running: %s", " ".join(command))
    return subprocess.run(command, capture_output=True, text=True)


def lock() -> None:
    _run(["rundll32.exe", "user32.dll,LockWorkStation"])


def restart() -> None:
    _run(["shutdown.exe", "/r", "/t", "0"])


def shutdown() -> None:
    _run(["shutdown.exe", "/s", "/t", "0"])


def sleep() -> None:
    # rundll32 powrprof.dll,SetSuspendState sleeps; the trailing args disable
    # the "force"/"disable wake events" flags for a normal suspend.
    _run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])


def hibernate() -> None:
    _run(["shutdown.exe", "/h"])


def logout() -> None:
    _run(["shutdown.exe", "/l"])


def show_message(title: str, message: str) -> None:
    # MB_OK | MB_SYSTEMMODAL so it shows even with no console attached.
    MB_OK = 0x0
    MB_SYSTEMMODAL = 0x1000
    ctypes.windll.user32.MessageBoxW(0, message, title, MB_OK | MB_SYSTEMMODAL)


def take_screenshot(destination_path: str) -> str:
    import mss
    import mss.tools

    with mss.mss() as sct:
        monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
        shot = sct.grab(monitor)
        mss.tools.to_png(shot.rgb, shot.size, output=destination_path)
    return destination_path


def kernel_version() -> str:
    return stdlib_platform.version()


def os_version() -> str:
    return f"{stdlib_platform.system()} {stdlib_platform.release()} ({stdlib_platform.version()})"
