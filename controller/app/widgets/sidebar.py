"""Sidebar navigation - one checkable button per page, exclusive selection.
Pages are registered by the shell (app/views/shell.py), not hardcoded here,
so later phases just add another `add_item(...)` call.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QPushButton, QVBoxLayout, QWidget

from app.theme import SPACING


class Sidebar(QWidget):
    item_selected = Signal(str)  # page key

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(SPACING.sm, SPACING.md, SPACING.sm, SPACING.md)
        self._layout.setSpacing(SPACING.xs)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}

        self._layout.addStretch()

    def add_item(self, key: str, label: str) -> None:
        button = QPushButton(label)
        button.setCheckable(True)
        button.clicked.connect(lambda: self.item_selected.emit(key))
        self._group.addButton(button)
        self._buttons[key] = button
        # Insert before the trailing stretch.
        self._layout.insertWidget(self._layout.count() - 1, button)

    def set_active(self, key: str) -> None:
        button = self._buttons.get(key)
        if button:
            button.setChecked(True)
