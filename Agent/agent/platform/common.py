"""Platform detection + dispatch.

This is the only module (besides platform/linux.py and platform/windows.py
themselves) that should ever branch on OS. Everything else in the codebase
calls the functions here.
"""

from __future__ import annotations

import platform as stdlib_platform
import sys

from agent.constants import Platform


def current_platform() -> Platform:
    system = stdlib_platform.system().lower()
    if system == "linux":
        return Platform.LINUX
    if system == "windows":
        return Platform.WINDOWS
    return Platform.UNKNOWN


def _backend():
    plat = current_platform()
    if plat == Platform.LINUX:
        from agent.platform import linux as backend
    elif plat == Platform.WINDOWS:
        from agent.platform import windows as backend
    else:
        raise RuntimeError(f"Unsupported platform: {stdlib_platform.system()}")
    return backend


def lock() -> None:
    _backend().lock()


def restart() -> None:
    _backend().restart()


def shutdown() -> None:
    _backend().shutdown()


def sleep() -> None:
    _backend().sleep()


def hibernate() -> None:
    _backend().hibernate()


def logout() -> None:
    _backend().logout()


def show_message(title: str, message: str) -> None:
    _backend().show_message(title, message)


def take_screenshot(destination_path: str) -> str:
    """Capture the primary display to destination_path, return the path used."""

    return _backend().take_screenshot(destination_path)


def kernel_version() -> str:
    return _backend().kernel_version()


def os_version() -> str:
    return _backend().os_version()


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))
