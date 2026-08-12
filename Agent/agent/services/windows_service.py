"""Windows Service wrapper (pywin32).

Usage (elevated/Administrator PowerShell or cmd):

    python agent\\services\\windows_service.py install
    python agent\\services\\windows_service.py start
    python agent\\services\\windows_service.py stop
    python agent\\services\\windows_service.py remove

This module imports pywin32 at call time, not at module import time, so it
can still be imported (for tests, static analysis, PyInstaller dependency
scanning) on non-Windows platforms without pywin32 installed. Calling any of
its functions on a non-Windows OS will raise RuntimeError.
"""

from __future__ import annotations

import logging
import sys

logger = logging.getLogger("agent.services.windows_service")

SERVICE_NAME = "EchoDeskAgent"
SERVICE_DISPLAY_NAME = "EchoDesk Device Agent"
SERVICE_DESCRIPTION = (
    "Registers this device with EchoDesk and executes authorized remote "
    "management commands (lock/restart/shutdown, messages, file transfer, "
    "screenshots) issued by the device owner."
)


def _require_pywin32():
    try:
        import servicemanager
        import win32event
        import win32service
        import win32serviceutil
    except ImportError as error:
        raise RuntimeError(
            "pywin32 is required for Windows service support. Install it with "
            "`pip install pywin32` (see agent/requirements.txt)."
        ) from error
    return servicemanager, win32event, win32service, win32serviceutil


def _build_service_class():
    servicemanager, win32event, win32service, win32serviceutil = _require_pywin32()

    class EchoDeskAgentService(win32serviceutil.ServiceFramework):
        _svc_name_ = SERVICE_NAME
        _svc_display_name_ = SERVICE_DISPLAY_NAME
        _svc_description_ = SERVICE_DESCRIPTION

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self._agent = None

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            if self._agent is not None:
                try:
                    self._agent.stop()
                except Exception:
                    logger.exception("Error while stopping Agent from service SvcStop")
            win32event.SetEvent(self.stop_event)

        def SvcDoRun(self):
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )
            self._run_agent()

        def _run_agent(self):
            from agent.main import Agent

            self._agent = Agent()
            self._agent.start()
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

    return EchoDeskAgentService


def handle_command_line(argv: list[str] | None = None) -> None:
    """Entry point for `python windows_service.py <install|start|stop|remove>`."""

    _servicemanager, _win32event, _win32service, win32serviceutil = _require_pywin32()
    service_class = _build_service_class()
    win32serviceutil.HandleCommandLine(service_class, argv=argv)


if __name__ == "__main__":
    handle_command_line(sys.argv)
