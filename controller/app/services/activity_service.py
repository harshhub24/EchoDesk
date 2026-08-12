"""Activity log polling service - GET /activity, which (unlike
notifications) is genuinely populated by the backend today.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal

from app.api import endpoints
from app.api.client import ApiError
from app.models import ActivityEntry
from app.services.app_state import AppState
from app.utils.workers import run_async


class ActivityService(QObject):
    activity_updated = Signal(list)  # list[ActivityEntry]
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
            on_result=self.activity_updated.emit,
            on_error=lambda error, _tb: self.refresh_failed.emit(
                error.message if isinstance(error, ApiError) else str(error)
            ),
        )

    def _fetch(self) -> list[ActivityEntry]:
        raw = endpoints.list_activity(self.app_state.rest_client)
        entries = [ActivityEntry.from_dict(a) for a in raw]
        entries.sort(key=lambda a: a.created_at or "", reverse=True)
        return entries
