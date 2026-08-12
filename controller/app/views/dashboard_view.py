"""Dashboard page: device counts, recent commands, recent activity. Polling-
driven (DashboardService), not realtime - see docs/PHASE_1_ANALYSIS.md.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.constants import COMMAND_TYPE_LABELS
from app.services.app_state import AppState
from app.services.dashboard_service import DashboardService, DashboardSummary
from app.theme import COLORS, SPACING, command_status_color
from app.utils.formatting import format_relative_time
from app.widgets.card import GlassCard
from app.widgets.stat_card import StatCard


class DashboardView(QWidget):
    def __init__(self, app_state: AppState, parent: QWidget | None = None):
        super().__init__(parent)
        self.app_state = app_state
        self.service = DashboardService(app_state)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        heading = QLabel("Dashboard")
        heading.setProperty("cssClass", "heading")
        layout.addWidget(heading)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {COLORS.danger};")
        self.error_label.hide()
        layout.addWidget(self.error_label)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(SPACING.md)
        self.total_card = StatCard("Total Devices", COLORS.purple_light)
        self.online_card = StatCard("Online", COLORS.success)
        self.offline_card = StatCard("Offline", COLORS.text_muted)
        for card in (self.total_card, self.online_card, self.offline_card):
            stats_row.addWidget(card)
        layout.addLayout(stats_row)

        content_row = QHBoxLayout()
        content_row.setSpacing(SPACING.md)

        commands_card = GlassCard()
        commands_title = QLabel("Recent Commands")
        commands_title.setProperty("cssClass", "subtitle")
        self.commands_table = QTableWidget(0, 3)
        self.commands_table.setHorizontalHeaderLabels(["Command", "Status", "Sent"])
        self.commands_table.horizontalHeader().setStretchLastSection(True)
        self.commands_table.verticalHeader().setVisible(False)
        self.commands_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.commands_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        commands_card.body_layout.addWidget(commands_title)
        commands_card.body_layout.addWidget(self.commands_table)

        activity_card = GlassCard()
        activity_title = QLabel("Recent Activity")
        activity_title.setProperty("cssClass", "subtitle")
        self.activity_table = QTableWidget(0, 2)
        self.activity_table.setHorizontalHeaderLabels(["Event", "When"])
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        activity_card.body_layout.addWidget(activity_title)
        activity_card.body_layout.addWidget(self.activity_table)

        content_row.addWidget(commands_card)
        content_row.addWidget(activity_card)
        layout.addLayout(content_row)

        self.service.summary_updated.connect(self._on_summary_updated)
        self.service.refresh_failed.connect(self._on_refresh_failed)

    def start(self) -> None:
        self.service.start()

    def stop(self) -> None:
        self.service.stop()

    def _on_summary_updated(self, summary: DashboardSummary) -> None:
        self.error_label.hide()
        self.total_card.set_value(summary.total_devices)
        self.online_card.set_value(summary.online_devices)
        self.offline_card.set_value(summary.offline_devices)
        self._populate_commands(summary.recent_commands)
        self._populate_activity(summary.recent_activity)

    def _on_refresh_failed(self, message: str) -> None:
        self.error_label.setText(f"Could not refresh dashboard: {message}")
        self.error_label.show()

    def _populate_commands(self, commands) -> None:
        self.commands_table.setRowCount(len(commands))
        for row, command in enumerate(commands):
            label = COMMAND_TYPE_LABELS.get(command.command_type, command.command_type)
            self.commands_table.setItem(row, 0, QTableWidgetItem(label))

            status_item = QTableWidgetItem(command.status.capitalize())
            status_item.setForeground(QColor(command_status_color(command.status)))
            self.commands_table.setItem(row, 1, status_item)

            self.commands_table.setItem(row, 2, QTableWidgetItem(format_relative_time(command.created_at)))

    def _populate_activity(self, entries) -> None:
        self.activity_table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self.activity_table.setItem(row, 0, QTableWidgetItem(entry.message or entry.activity_type))
            self.activity_table.setItem(row, 1, QTableWidgetItem(format_relative_time(entry.created_at)))
