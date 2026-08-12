"""Profile page. Reuses GET/PUT /profile and POST /change-password exactly."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app.api import endpoints
from app.api.client import ApiError
from app.services.app_state import AppState
from app.theme import COLORS, SPACING
from app.utils.workers import run_async
from app.widgets.card import GlassCard


class ProfileView(QWidget):
    def __init__(self, app_state: AppState, parent: QWidget | None = None):
        super().__init__(parent)
        self.app_state = app_state

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        heading = QLabel("Profile")
        heading.setProperty("cssClass", "heading")
        layout.addWidget(heading)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {COLORS.danger};")
        self.error_label.hide()
        layout.addWidget(self.error_label)

        account_card = GlassCard()
        account_card.setMaximumWidth(480)
        title = QLabel("Account Information")
        title.setProperty("cssClass", "subtitle")
        account_card.body_layout.addWidget(title)

        self.email_label = QLabel("—")
        self.full_name_label = QLabel("—")
        account_card.body_layout.addWidget(QLabel("Email:"))
        account_card.body_layout.addWidget(self.email_label)
        account_card.body_layout.addWidget(QLabel("Name:"))
        account_card.body_layout.addWidget(self.full_name_label)
        layout.addWidget(account_card)

        password_card = GlassCard()
        password_card.setMaximumWidth(480)
        password_title = QLabel("Change Password")
        password_title.setProperty("cssClass", "subtitle")
        password_card.body_layout.addWidget(password_title)

        self.current_password_input = QLineEdit()
        self.current_password_input.setPlaceholderText("Current password")
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("New password")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        change_password_button = QPushButton("Change Password")
        change_password_button.setProperty("cssClass", "primary")
        change_password_button.clicked.connect(self._change_password)

        password_card.body_layout.addWidget(self.current_password_input)
        password_card.body_layout.addWidget(self.new_password_input)
        password_card.body_layout.addWidget(change_password_button)
        layout.addWidget(password_card)

        logout_button = QPushButton("Log Out")
        logout_button.setProperty("cssClass", "danger")
        logout_button.setMaximumWidth(160)
        logout_button.clicked.connect(self.app_state.logout)
        layout.addWidget(logout_button)

        layout.addStretch()

    def start(self) -> None:
        run_async(
            endpoints.get_profile,
            self.app_state.rest_client,
            on_result=self._on_profile_loaded,
            on_error=lambda error, _tb: self._show_error(error.message if isinstance(error, ApiError) else str(error)),
        )

    def stop(self) -> None:
        pass

    def _on_profile_loaded(self, response: dict) -> None:
        data = response.get("data", {})
        self.email_label.setText(data.get("email", "—"))
        self.full_name_label.setText(data.get("full_name", "—"))

    def _change_password(self) -> None:
        current = self.current_password_input.text()
        new = self.new_password_input.text()
        if not current or not new:
            self._show_error("Enter both your current and new password.")
            return

        self.error_label.hide()
        run_async(
            endpoints.change_password,
            self.app_state.rest_client,
            current,
            new,
            on_result=self._on_password_changed,
            on_error=lambda error, _tb: self._show_error(error.message if isinstance(error, ApiError) else str(error)),
        )

    def _on_password_changed(self, _response: dict) -> None:
        self.current_password_input.clear()
        self.new_password_input.clear()
        QMessageBox.information(self, "Password Changed", "Your password was changed successfully.")

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()
