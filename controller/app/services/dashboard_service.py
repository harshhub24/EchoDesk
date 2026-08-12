"""Dashboard service: polls the endpoints the Dashboard needs and exposes
computed summary stats via Qt signals. Per docs/PHASE_1_ANALYSIS.md, there
is no realtime push for any of this - polling via QTimer is the only path.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from PySide6.QtCore import QObject, QTimer, Signal

from app.api import endpoints
from app.api.client import ApiError
from app.models import ActivityEntry, Command, Device
from app.services.app_state import AppState
from app.utils.workers import run_async

logger = logging.getLogger("controller.services.dashboard_service")


@dataclass
class DashboardSummary:
    devices: list[Device] = field(default_factory=list)
    recent_commands: list[Command] = field(default_factory=list)
    recent_activity: list[ActivityEntry] = field(default_factory=list)

    @property
    def total_devices(self) -> int:
        return len(self.devices)

    @property
    def online_devices(self) -> int:
        return sum(1 for d in self.devices if d.is_online)

    @property
    def offline_devices(self) -> int:
        return self.total_devices - self.online_devices


class DashboardService(QObject):
    summary_updated = Signal(DashboardSummary)
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
            on_result=self.summary_updated.emit,
            on_error=lambda error, _tb: self.refresh_failed.emit(
                error.message if isinstance(error, ApiError) else str(error)
            ),
        )

    def _fetch(self) -> DashboardSummary:
        # Pure network calls - safe on the worker thread (no QObject touched).
        raw_devices = endpoints.list_devices(self.app_state.rest_client)
        devices = [Device.from_dict(d) for d in raw_devices]

        raw_commands = endpoints.list_commands(self.app_state.rest_client)
        commands = [Command.from_dict(c) for c in raw_commands]
        commands.sort(key=lambda c: c.created_at or "", reverse=True)

        raw_activity = endpoints.list_activity(self.app_state.rest_client)
        activity = [ActivityEntry.from_dict(a) for a in raw_activity]
        activity.sort(key=lambda a: a.created_at or "", reverse=True)

        return DashboardSummary(devices=devices, recent_commands=commands[:10], recent_activity=activity[:10])
