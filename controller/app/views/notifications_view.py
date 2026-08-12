"""Notifications page. Correctly wired to GET /notifications - see
app/services/notification_service.py docstring for why this shows an
honest empty state today rather than fake data.
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.models import Notification
from app.services.app_state import AppState
from app.services.notification_service import NotificationService
from app.theme import COLORS, SPACING
from app.utils.formatting import format_relative_time
from app.widgets.card import GlassCard


class NotificationsView(QWidget):
    def __init__(self, app_state: AppState, parent: QWidget | None = None):
        super().__init__(parent)
        self.service = NotificationService(app_state)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        heading = QLabel("Notifications")
        heading.setProperty("cssClass", "heading")
        layout.addWidget(heading)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {COLORS.danger};")
        self.error_label.hide()
        layout.addWidget(self.error_label)

        self.empty_label = QLabel(
            "No notifications yet. (The backend doesn't currently generate device-online/offline or "
            "command-result notifications - this page will populate automatically once it does.)"
        )
        self.empty_label.setProperty("cssClass", "muted")
        self.empty_label.setWordWrap(True)
        layout.addWidget(self.empty_label)

        card = GlassCard()
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Title", "Message", "When"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        card.body_layout.addWidget(self.table)
        layout.addWidget(card, stretch=1)

        self.service.notifications_updated.connect(self._on_updated)
        self.service.refresh_failed.connect(self._on_refresh_failed)

    def start(self) -> None:
        self.service.start()

    def stop(self) -> None:
        self.service.stop()

    def _on_updated(self, notifications: list[Notification]) -> None:
        self.error_label.hide()
        self.empty_label.setVisible(len(notifications) == 0)
        self.table.setRowCount(len(notifications))
        for row, n in enumerate(notifications):
            self.table.setItem(row, 0, QTableWidgetItem(n.title))
            self.table.setItem(row, 1, QTableWidgetItem(n.message))
            self.table.setItem(row, 2, QTableWidgetItem(format_relative_time(n.created_at)))

    def _on_refresh_failed(self, message: str) -> None:
        self.error_label.setText(f"Could not refresh notifications: {message}")
        self.error_label.show()
