"""Compiles the design tokens into a QSS stylesheet string, applied once at
`app.setStyleSheet(...)` in main.py. Widget-specific rules added in later
phases should extend this function rather than setting inline styles on
individual widgets, so the theme stays centrally editable.

Qt/QSS has no native backdrop blur - the "glassmorphism" look here is a
practical approximation: semi-transparent panel backgrounds
(`COLORS.bg_glass`), a soft border, and (applied per-widget in Python, not
QSS) a `QGraphicsDropShadowEffect` for elevation. See
docs/PHASE_2_ARCHITECTURE.md for why.
"""

from __future__ import annotations

from app.theme.tokens import COLORS, FONTS, RADIUS, SPACING


def build_stylesheet() -> str:
    return f"""
    QWidget {{
        background-color: {COLORS.bg_base};
        color: {COLORS.text_primary};
        font-family: "{FONTS.family}";
        font-size: {FONTS.size_base}pt;
    }}

    QMainWindow, #centralWidget {{
        background-color: {COLORS.bg_base};
    }}

    /* --- Sidebar --- */
    #sidebar {{
        background-color: {COLORS.bg_surface};
        border-right: 1px solid {COLORS.border_subtle};
    }}
    #sidebar QPushButton {{
        text-align: left;
        padding: {SPACING.sm}px {SPACING.md}px;
        border-radius: {RADIUS.medium}px;
        border: none;
        background-color: transparent;
        color: {COLORS.text_secondary};
        font-size: {FONTS.size_base}pt;
    }}
    #sidebar QPushButton:hover {{
        background-color: {COLORS.bg_elevated};
        color: {COLORS.text_primary};
    }}
    #sidebar QPushButton:checked {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS.purple_primary}, stop:1 {COLORS.blue_accent});
        color: {COLORS.text_on_accent};
        font-weight: 600;
    }}

    /* --- Top nav / header bar --- */
    #topNav {{
        background-color: {COLORS.bg_surface};
        border-bottom: 1px solid {COLORS.border_subtle};
    }}

    /* --- Cards (glass panels) --- */
    .Card, QFrame[cssClass="card"] {{
        background-color: {COLORS.bg_glass};
        border: 1px solid {COLORS.bg_glass_border};
        border-radius: {RADIUS.large}px;
    }}

    /* --- Headings --- */
    QLabel[cssClass="heading"] {{
        font-size: {FONTS.size_heading}pt;
        font-weight: 700;
        color: {COLORS.text_primary};
    }}
    QLabel[cssClass="display"] {{
        font-size: {FONTS.size_display}pt;
        font-weight: 700;
    }}
    QLabel[cssClass="muted"] {{
        color: {COLORS.text_muted};
        font-size: {FONTS.size_small}pt;
    }}
    QLabel[cssClass="subtitle"] {{
        color: {COLORS.text_secondary};
    }}

    /* --- Buttons --- */
    QPushButton {{
        background-color: {COLORS.bg_elevated};
        color: {COLORS.text_primary};
        border: 1px solid {COLORS.border_subtle};
        border-radius: {RADIUS.medium}px;
        padding: {SPACING.sm}px {SPACING.md}px;
    }}
    QPushButton:hover {{
        border-color: {COLORS.border_strong};
    }}
    QPushButton:pressed {{
        background-color: {COLORS.bg_surface};
    }}
    QPushButton:disabled {{
        color: {COLORS.text_muted};
        border-color: {COLORS.border_subtle};
    }}
    QPushButton[cssClass="primary"] {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS.purple_primary}, stop:1 {COLORS.blue_accent});
        color: {COLORS.text_on_accent};
        border: none;
        font-weight: 600;
    }}
    QPushButton[cssClass="primary"]:hover {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS.purple_light}, stop:1 {COLORS.blue_light});
    }}
    QPushButton[cssClass="danger"] {{
        background-color: {COLORS.danger};
        color: {COLORS.text_on_accent};
        border: none;
    }}
    QPushButton[cssClass="ghost"] {{
        background-color: transparent;
        border: 1px solid {COLORS.border_subtle};
    }}

    /* --- Inputs --- */
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {{
        background-color: {COLORS.bg_surface};
        border: 1px solid {COLORS.border_subtle};
        border-radius: {RADIUS.small}px;
        padding: {SPACING.sm}px;
        color: {COLORS.text_primary};
        selection-background-color: {COLORS.purple_primary};
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border-color: {COLORS.purple_light};
    }}
    QCheckBox {{
        color: {COLORS.text_secondary};
        spacing: {SPACING.sm}px;
    }}

    /* --- Tables / lists --- */
    QTableView, QListView, QTreeView {{
        background-color: {COLORS.bg_surface};
        border: 1px solid {COLORS.border_subtle};
        border-radius: {RADIUS.medium}px;
        gridline-color: {COLORS.border_subtle};
        selection-background-color: {COLORS.purple_dark};
        selection-color: {COLORS.text_on_accent};
    }}
    QHeaderView::section {{
        background-color: {COLORS.bg_elevated};
        color: {COLORS.text_secondary};
        border: none;
        border-bottom: 1px solid {COLORS.border_subtle};
        padding: {SPACING.sm}px;
    }}

    /* --- Scrollbars --- */
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS.bg_elevated};
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLORS.purple_dark};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    /* --- Tabs --- */
    QTabWidget::pane {{
        border: 1px solid {COLORS.border_subtle};
        border-radius: {RADIUS.medium}px;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {COLORS.text_secondary};
        padding: {SPACING.sm}px {SPACING.md}px;
    }}
    QTabBar::tab:selected {{
        color: {COLORS.text_primary};
        border-bottom: 2px solid {COLORS.purple_primary};
    }}

    /* --- Status pill (used for device status / command status) --- */
    QLabel[cssClass="statusOnline"] {{
        color: {COLORS.status_online};
        font-weight: 600;
    }}
    QLabel[cssClass="statusOffline"] {{
        color: {COLORS.status_offline};
        font-weight: 600;
    }}
    QLabel[cssClass="statusWarning"] {{
        color: {COLORS.warning};
        font-weight: 600;
    }}

    /* --- Progress bars --- */
    QProgressBar {{
        background-color: {COLORS.bg_surface};
        border: 1px solid {COLORS.border_subtle};
        border-radius: {RADIUS.small}px;
        text-align: center;
        color: {COLORS.text_primary};
    }}
    QProgressBar::chunk {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS.purple_primary}, stop:1 {COLORS.blue_accent});
        border-radius: {RADIUS.small}px;
    }}

    /* --- Tooltips --- */
    QToolTip {{
        background-color: {COLORS.bg_elevated};
        color: {COLORS.text_primary};
        border: 1px solid {COLORS.border_strong};
        border-radius: {RADIUS.small}px;
        padding: {SPACING.xs}px {SPACING.sm}px;
    }}
    """


def apply_theme(app) -> None:
    app.setStyleSheet(build_stylesheet())
