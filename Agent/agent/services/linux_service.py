"""Linux systemd service installation.

Generates and installs a systemd unit that runs the Agent via the repo-root
`run.py` launcher (never `agent/main.py` directly - see run.py's docstring).
Intended to be run with root privileges (sudo) since it writes to
/etc/systemd/system and calls systemctl.
"""

from __future__ import annotations

import getpass
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("agent.services.linux_service")

SERVICE_NAME = "echodesk-agent"
SYSTEMD_UNIT_PATH = Path(f"/etc/systemd/system/{SERVICE_NAME}.service")


def render_unit_file(install_dir: Path, run_as_user: str | None, python_executable: str | None) -> str:
    python_bin = python_executable or sys.executable
    user = run_as_user or getpass.getuser()

    return f"""[Unit]
Description=EchoDesk Device Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={user}
WorkingDirectory={install_dir}
ExecStart={python_bin} {install_dir}/run.py
Restart=always
RestartSec=10
StandardOutput=append:{install_dir}/agent/logs/service-stdout.log
StandardError=append:{install_dir}/agent/logs/service-stderr.log

[Install]
WantedBy=multi-user.target
"""


def install(install_dir: Path, run_as_user: str | None = None, python_executable: str | None = None) -> None:
    unit_contents = render_unit_file(install_dir, run_as_user, python_executable)
    SYSTEMD_UNIT_PATH.write_text(unit_contents, encoding="utf-8")
    logger.info("Wrote systemd unit to %s", SYSTEMD_UNIT_PATH)

    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", SERVICE_NAME], check=True)
    subprocess.run(["systemctl", "start", SERVICE_NAME], check=True)
    logger.info("Service '%s' installed, enabled, and started", SERVICE_NAME)


def uninstall() -> None:
    subprocess.run(["systemctl", "stop", SERVICE_NAME], check=False)
    subprocess.run(["systemctl", "disable", SERVICE_NAME], check=False)
    if SYSTEMD_UNIT_PATH.exists():
        SYSTEMD_UNIT_PATH.unlink()
    subprocess.run(["systemctl", "daemon-reload"], check=False)
    logger.info("Service '%s' stopped, disabled, and unit file removed", SERVICE_NAME)


def status() -> str:
    result = subprocess.run(["systemctl", "is-active", SERVICE_NAME], capture_output=True, text=True)
    return result.stdout.strip() or result.stderr.strip()
