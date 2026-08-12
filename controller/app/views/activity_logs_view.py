"""Activity Logs page - GET /activity, genuinely populated (auth events,
etc.) unlike Notifications. Client-side search/filter/export (no backend
query params needed for a list this size).
"""

from __future__ import annotations

import csv

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models import ActivityEntry
from app.services.activity_service import ActivityService
from app.services.app_state import AppState
from app.theme import COLORS, SPACING
from app.utils.formatting import format_relative_time
from app.widgets.card import GlassCard


class ActivityLogsView(QWidget):
    def __init__(self, app_state: AppState, parent: QWidget | None = None):
        super().__init__(parent)
        self.service = ActivityService(app_state)
        self._entries: list[ActivityEntry] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        heading = QLabel("Activity Logs")
        heading.setProperty("cssClass", "heading")
        layout.addWidget(heading)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {COLORS.danger};")
        self.error_label.hide()
        layout.addWidget(self.error_label)

        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search messages...")
        self.search_input.textChanged.connect(self._apply_filters)

        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", None)
        self.category_combo.currentIndexChanged.connect(self._apply_filters)

        export_button = QPushButton("Export CSV")
        export_button.setProperty("cssClass", "ghost")
        export_button.clicked.connect(self._export_csv)

        toolbar.addWidget(self.search_input, stretch=1)
        toolbar.addWidget(self.category_combo)
        toolbar.addWidget(export_button)
        layout.addLayout(toolbar)

        card = GlassCard()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Category", "Type", "Message", "When"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        card.body_layout.addWidget(self.table)
        layout.addWidget(card, stretch=1)

        self.service.activity_updated.connect(self._on_updated)
        self.service.refresh_failed.connect(self._on_refresh_failed)

    def start(self) -> None:
        self.service.start()

    def stop(self) -> None:
        self.service.stop()

    def _on_updated(self, entries: list[ActivityEntry]) -> None:
        self.error_label.hide()
        self._entries = entries

        existing = {self.category_combo.itemData(i) for i in range(self.category_combo.count())}
        for entry in entries:
            if entry.category not in existing:
                self.category_combo.addItem(entry.category.title(), entry.category)
                existing.add(entry.category)

        self._apply_filters()

    def _on_refresh_failed(self, message: str) -> None:
        self.error_label.setText(f"Could not refresh activity: {message}")
        self.error_label.show()

    def _apply_filters(self) -> None:
        query = self.search_input.text().strip().lower()
        category = self.category_combo.currentData()

        filtered = [
            e for e in self._entries
            if (not query or query in e.message.lower())
            and (not category or e.category == category)
        ]

        self.table.setRowCount(len(filtered))
        for row, entry in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(entry.category))
            self.table.setItem(row, 1, QTableWidgetItem(entry.activity_type))
            self.table.setItem(row, 2, QTableWidgetItem(entry.message))
            self.table.setItem(row, 3, QTableWidgetItem(format_relative_time(entry.created_at)))

    def _export_csv(self) -> None:
        if not self._entries:
            QMessageBox.information(self, "Nothing to Export", "There are no activity entries to export.")
            return

        save_path, _filter = QFileDialog.getSaveFileName(self, "Export activity log", "activity_log.csv", "CSV Files (*.csv)")
        if not save_path:
            return

        with open(save_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["category", "activity_type", "message", "created_at"])
            for entry in self._entries:
                writer.writerow([entry.category, entry.activity_type, entry.message, entry.created_at])

        QMessageBox.information(self, "Exported", f"Activity log exported to {save_path}")
