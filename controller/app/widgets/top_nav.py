"""Top navigation bar - current page title + a logout action. Per-page
extra actions (e.g. "New Command" on Command Center) are added later by
having the page itself expose a widget the shell can dock here if needed;
kept minimal for now.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from app.theme import SPACING


class TopNav(QWidget):
    logout_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("topNav")
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, 0, SPACING.md, 0)

        self.title_label = QLabel("")
        self.title_label.setProperty("cssClass", "subtitle")

        self.connection_label = QLabel("")
        self.connection_label.setProperty("cssClass", "muted")

        logout_button = QPushButton("Log Out")
        logout_button.setProperty("cssClass", "ghost")
        logout_button.clicked.connect(self.logout_requested)

        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.connection_label)
        layout.addWidget(logout_button)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_connection_status(self, connected: bool) -> None:
        self.connection_label.setText("● Connected" if connected else "○ Reconnecting...")
