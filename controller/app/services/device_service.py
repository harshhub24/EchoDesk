"""Device polling services - list (Devices page) and single-device detail
(Device Details / Telemetry pages). Both are pure polling, per
docs/PHASE_1_ANALYSIS.md (no realtime device push exists on the backend).
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer, Signal

from app.api import endpoints
from app.api.client import ApiError
from app.models import Device
from app.services.app_state import AppState
from app.utils.workers import run_async

logger = logging.getLogger("controller.services.device_service")


class DeviceListService(QObject):
    devices_updated = Signal(list)  # list[Device]
    refresh_failed = Signal(str)

    def __init__(self, app_state: AppState, poll_interval_seconds: int | None = None):
        super().__init__()
        self.app_state = app_state
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._interval_ms = (poll_interval_seconds or app_state.config.device_poll_interval_seconds) * 1000

    def start(self) -> None:
        self.refresh()
        self._timer.start(self._interval_ms)

    def stop(self) -> None:
        self._timer.stop()

    def refresh(self) -> None:
        run_async(
            self._fetch,
            on_result=self.devices_updated.emit,
            on_error=lambda error, _tb: self.refresh_failed.emit(
                error.message if isinstance(error, ApiError) else str(error)
            ),
        )

    def _fetch(self) -> list[Device]:
        raw_devices = endpoints.list_devices(self.app_state.rest_client)
        return [Device.from_dict(d) for d in raw_devices]


class DeviceDetailService(QObject):
    device_updated = Signal(Device)
    device_not_found = Signal()
    refresh_failed = Signal(str)

    def __init__(self, app_state: AppState, poll_interval_seconds: int | None = None):
        super().__init__()
        self.app_state = app_state
        self.device_identifier: str | None = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._interval_ms = (poll_interval_seconds or app_state.config.device_poll_interval_seconds) * 1000

    def set_device(self, device_identifier: str) -> None:
        self.device_identifier = device_identifier

    def start(self) -> None:
        if not self.device_identifier:
            return
        self.refresh()
        self._timer.start(self._interval_ms)

    def stop(self) -> None:
        self._timer.stop()

    def refresh(self) -> None:
        if not self.device_identifier:
            return
        run_async(
            self._fetch,
            self.device_identifier,
            on_result=self._handle_result,
            on_error=self._handle_error,
        )

    def _fetch(self, device_identifier: str) -> Device:
        raw = endpoints.get_device(self.app_state.rest_client, device_identifier)
        return Device.from_dict(raw)

    def _handle_result(self, device: Device) -> None:
        self.device_updated.emit(device)

    def _handle_error(self, error: Exception, _tb: str) -> None:
        if isinstance(error, ApiError) and error.status_code == 404:
            self.device_not_found.emit()
            return
        self.refresh_failed.emit(error.message if isinstance(error, ApiError) else str(error))
