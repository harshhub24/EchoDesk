"""Top-level service installer: dispatches to linux_service or
windows_service based on the current OS. Invoked by the shell/PowerShell
scripts under agent/installer/, or directly:

    python -m agent.services.installer install
    python -m agent.services.installer uninstall
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from agent.constants import Platform
from agent.platform.common import current_platform

logger = logging.getLogger("agent.services.installer")


def install() -> None:
    plat = current_platform()
    install_dir = Path(__file__).resolve().parent.parent.parent  # .../agent/services/.. .. -> repo root

    if plat == Platform.LINUX:
        from agent.services import linux_service

        linux_service.install(install_dir)
    elif plat == Platform.WINDOWS:
        from agent.services import windows_service

        windows_service.handle_command_line(["", "install"])
        windows_service.handle_command_line(["", "start"])
    else:
        raise RuntimeError(f"No service installer available for this platform: {plat}")


def uninstall() -> None:
    plat = current_platform()

    if plat == Platform.LINUX:
        from agent.services import linux_service

        linux_service.uninstall()
    elif plat == Platform.WINDOWS:
        from agent.services import windows_service

        windows_service.handle_command_line(["", "stop"])
        windows_service.handle_command_line(["", "remove"])
    else:
        raise RuntimeError(f"No service installer available for this platform: {plat}")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("install", "uninstall"):
        print("Usage: python -m agent.services.installer <install|uninstall>")
        sys.exit(2)

    if sys.argv[1] == "install":
        install()
    else:
        uninstall()


if __name__ == "__main__":
    main()
