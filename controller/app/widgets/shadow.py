"""Drop-shadow helper - Qt's practical stand-in for backdrop blur/elevation
(see app/theme/qss.py's module docstring). One shared function so every
"glass card" across the app gets a consistent elevation look.
"""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget


def apply_elevation(widget: QWidget, blur_radius: int = 32, y_offset: int = 8, alpha: int = 140) -> QGraphicsDropShadowEffect:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur_radius)
    effect.setOffset(0, y_offset)
    effect.setColor(QColor(124, 58, 237, alpha))  # purple_primary, semi-transparent
    widget.setGraphicsEffect(effect)
    return effect
