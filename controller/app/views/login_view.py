"""Login page. Reuses the backend's JWT auth exactly via AppState/TokenManager
(see docs/PHASE_1_ANALYSIS.md §1) - this view only handles presentation and
input validation, never touches app/api or app/auth directly.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.constants import APP_NAME
from app.services import AppState
from app.theme import COLORS, SPACING
from app.widgets.card import GlassCard


class LoginView(QWidget):
    # Emitted purely for other views/tests to observe - MainWindow drives
    # the actual page switch off AppState's own signals, not this one.
    login_attempted = Signal()

    def __init__(self, app_state: AppState, parent: QWidget | None = None):
        super().__init__(parent)
        self.app_state = app_state

        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = GlassCard()
        card.setFixedWidth(420)
        layout = card.body_layout
        layout.setSpacing(SPACING.md)

        title = QLabel(APP_NAME)
        title.setProperty("cssClass", "heading")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Sign in to manage your devices")
        subtitle.setProperty("cssClass", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setClearButtonEnabled(True)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.remember_checkbox = QCheckBox("Remember me")
        self.remember_checkbox.setChecked(app_state.config.remember_login_default)

        self.error_label = QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet(f"color: {COLORS.danger};")
        self.error_label.hide()

        self.login_button = QPushButton("Log In")
        self.login_button.setProperty("cssClass", "primary")
        self.login_button.setDefault(True)
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(SPACING.sm)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.remember_checkbox)
        layout.addWidget(self.error_label)
        layout.addWidget(self.login_button)

        outer_layout.addWidget(card)

        self.login_button.clicked.connect(self._on_submit)
        self.email_input.returnPressed.connect(self._on_submit)
        self.password_input.returnPressed.connect(self._on_submit)

        self.app_state.login_failed.connect(self._on_login_failed)
        self.app_state.login_succeeded.connect(self._on_login_succeeded)

    def _on_submit(self) -> None:
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            self._show_error("Enter both email and password.")
            return

        self.error_label.hide()
        self._set_loading(True)
        self.login_attempted.emit()
        self.app_state.login(email, password, self.remember_checkbox.isChecked())

    def _on_login_failed(self, message: str) -> None:
        self._set_loading(False)
        self._show_error(message)

    def _on_login_succeeded(self, _session) -> None:
        self._set_loading(False)
        self.password_input.clear()
        self.error_label.hide()

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()

    def _set_loading(self, loading: bool) -> None:
        self.login_button.setEnabled(not loading)
        self.login_button.setText("Signing in..." if loading else "Log In")
        self.email_input.setEnabled(not loading)
        self.password_input.setEnabled(not loading)
