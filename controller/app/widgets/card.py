"""Base "glass card" widget used throughout the app (Dashboard stat cards,
Device tiles, Command Center panels, etc.). Later phases subclass or
compose this rather than re-styling QFrame from scratch each time.
"""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget

from app.theme import SPACING
from app.widgets.shadow import apply_elevation


class GlassCard(QFrame):
    def __init__(self, parent: QWidget | None = None, elevated: bool = True):
        super().__init__(parent)
        self.setProperty("cssClass", "card")
        self.setFrameShape(QFrame.Shape.NoFrame)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        self._layout.setSpacing(SPACING.sm)

        if elevated:
            apply_elevation(self)

    @property
    def body_layout(self) -> QVBoxLayout:
        return self._layout
