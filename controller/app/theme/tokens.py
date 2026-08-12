"""Design tokens for the dark / royal-purple / blue-accent glassmorphism
theme. Single source of truth - `theme/qss.py` reads these, and any widget
needing a color outside plain QSS (e.g. pyqtgraph curve colors, drop shadow
colors) imports from here too, so the palette never drifts between the
stylesheet and hand-drawn widgets.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorTokens:
    # Backgrounds
    bg_base: str = "#0F0B1E"
    bg_surface: str = "#171129"
    bg_elevated: str = "#1E1836"
    bg_glass: str = "rgba(30, 24, 54, 0.65)"
    bg_glass_border: str = "rgba(168, 130, 255, 0.18)"

    # Brand
    purple_primary: str = "#7C3AED"
    purple_light: str = "#A855F7"
    purple_dark: str = "#5B21B6"
    blue_accent: str = "#3B82F6"
    blue_light: str = "#60A5FA"

    # Semantic
    success: str = "#22C55E"
    warning: str = "#F59E0B"
    danger: str = "#EF4444"
    info: str = "#3B82F6"

    # Text
    text_primary: str = "#F3F1FA"
    text_secondary: str = "#B8B0D6"
    text_muted: str = "#7A7296"
    text_on_accent: str = "#FFFFFF"

    # Status dots
    status_online: str = "#22C55E"
    status_offline: str = "#6B7280"
    status_unknown: str = "#F59E0B"

    # Borders/dividers
    border_subtle: str = "rgba(168, 130, 255, 0.12)"
    border_strong: str = "rgba(168, 130, 255, 0.30)"


@dataclass(frozen=True)
class FontTokens:
    family: str = "Segoe UI"
    family_mono: str = "Cascadia Mono"
    size_base: int = 10
    size_small: int = 9
    size_large: int = 13
    size_heading: int = 18
    size_display: int = 24


@dataclass(frozen=True)
class RadiusTokens:
    small: int = 6
    medium: int = 12
    large: int = 18
    pill: int = 999


@dataclass(frozen=True)
class SpacingTokens:
    xs: int = 4
    sm: int = 8
    md: int = 16
    lg: int = 24
    xl: int = 32


COLORS = ColorTokens()
FONTS = FontTokens()
RADIUS = RadiusTokens()
SPACING = SpacingTokens()


def status_color(status: str) -> str:
    return {
        "online": COLORS.status_online,
        "offline": COLORS.status_offline,
    }.get(status, COLORS.status_unknown)


def command_status_color(status: str) -> str:
    return {
        "success": COLORS.success,
        "failed": COLORS.danger,
        "expired": COLORS.text_muted,
        "pending": COLORS.warning,
        "delivered": COLORS.blue_accent,
        "executing": COLORS.blue_light,
    }.get(status, COLORS.text_muted)
