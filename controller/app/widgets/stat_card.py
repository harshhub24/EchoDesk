"""Small stat-display card (used on the Dashboard for Total/Online/Offline
device counts and similar single-number metrics).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from app.theme import COLORS
from app.widgets.card import GlassCard


class StatCard(GlassCard):
    def __init__(self, title: str, accent_color: str = COLORS.purple_light, parent=None):
        super().__init__(parent)

        self._title_label = QLabel(title)
        self._title_label.setProperty("cssClass", "muted")

        self._value_label = QLabel("—")
        self._value_label.setProperty("cssClass", "display")
        self._value_label.setStyleSheet(f"color: {accent_color};")

        self.body_layout.addWidget(self._title_label)
        self.body_layout.addWidget(self._value_label)
        self.body_layout.addStretch()

    def set_value(self, value) -> None:
        self._value_label.setText(str(value))
