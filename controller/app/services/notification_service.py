"""Notifications polling service. Wired to the real GET /notifications
endpoint - which, per docs/PHASE_1_ANALYSIS.md, is currently always empty
since no backend code path creates a notification yet. This will start
showing real data automatically the moment the backend does, with zero
Controller changes needed.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal

from app.api import endpoints
from app.api.client import ApiError
from app.models import Notification
from app.services.app_state import AppState
from app.utils.workers import run_async


class NotificationService(QObject):
    notifications_updated = Signal(list)  # list[Notification]
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
            on_result=self.notifications_updated.emit,
            on_error=lambda error, _tb: self.refresh_failed.emit(
                error.message if isinstance(error, ApiError) else str(error)
            ),
        )

    def _fetch(self) -> list[Notification]:
        raw = endpoints.list_notifications(self.app_state.rest_client)
        notifications = [Notification.from_dict(n) for n in raw]
        notifications.sort(key=lambda n: n.created_at or "", reverse=True)
        return notifications
