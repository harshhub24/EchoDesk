"""Settings page. Backend URL / polling intervals / theme are read from and
written back to the local `.env` file (same convention as the Agent) -
there's no backend endpoint for app preferences, nor should there be, these
are purely local. Restart-required changes are labeled as such.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.services.app_state import AppState
from app.theme import SPACING
from app.widgets.card import GlassCard

_ENV_KEYS_ORDER = [
    "ECHODESK_BACKEND_URL",
    "ECHODESK_API_PREFIX",
    "ECHODESK_VERIFY_TLS",
    "ECHODESK_REST_TIMEOUT",
    "ECHODESK_DEVICE_POLL_INTERVAL",
    "ECHODESK_COMMAND_POLL_INTERVAL",
    "ECHODESK_REMEMBER_LOGIN_DEFAULT",
    "ECHODESK_THEME",
]


class SettingsView(QWidget):
    def __init__(self, app_state: AppState, parent: QWidget | None = None):
        super().__init__(parent)
        self.app_state = app_state

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        heading = QLabel("Settings")
        heading.setProperty("cssClass", "heading")
        layout.addWidget(heading)

        note = QLabel("Changes here apply after you restart the app.")
        note.setProperty("cssClass", "muted")
        layout.addWidget(note)

        card = GlassCard()
        card.setMaximumWidth(560)

        self.backend_url_input = QLineEdit(app_state.config.backend_url)
        self.backend_url_input.setPlaceholderText("https://your-echodesk-backend.example.com")

        self.verify_tls_checkbox = QCheckBox("Verify TLS certificates")
        self.verify_tls_checkbox.setChecked(app_state.config.verify_tls)

        self.device_poll_spin = QSpinBox()
        self.device_poll_spin.setRange(5, 600)
        self.device_poll_spin.setSuffix(" s")
        self.device_poll_spin.setValue(app_state.config.device_poll_interval_seconds)

        self.command_poll_spin = QSpinBox()
        self.command_poll_spin.setRange(2, 300)
        self.command_poll_spin.setSuffix(" s")
        self.command_poll_spin.setValue(app_state.config.command_poll_interval_seconds)

        self.remember_login_checkbox = QCheckBox("Default 'Remember me' to checked on Login")
        self.remember_login_checkbox.setChecked(app_state.config.remember_login_default)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.addItem("Light (not yet available)", "light")
        index = self.theme_combo.findData(app_state.config.theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        for label_text, widget in [
            ("Backend URL", self.backend_url_input),
            ("", self.verify_tls_checkbox),
            ("Device poll interval", self.device_poll_spin),
            ("Command poll interval", self.command_poll_spin),
            ("", self.remember_login_checkbox),
            ("Theme", self.theme_combo),
        ]:
            if label_text:
                field_label = QLabel(label_text)
                field_label.setProperty("cssClass", "subtitle")
                card.body_layout.addWidget(field_label)
            card.body_layout.addWidget(widget)

        save_button = QPushButton("Save Settings")
        save_button.setProperty("cssClass", "primary")
        save_button.clicked.connect(self._save)
        card.body_layout.addWidget(save_button)

        layout.addWidget(card)
        layout.addStretch()

    def _env_file_path(self) -> Path:
        # Matches app/config/settings.py's own lookup: a `.env` next to the
        # `app/` package (i.e. next to main.py).
        return Path(__file__).resolve().parent.parent.parent / ".env"

    def _save(self) -> None:
        values = {
            "ECHODESK_BACKEND_URL": self.backend_url_input.text().strip(),
            "ECHODESK_VERIFY_TLS": "true" if self.verify_tls_checkbox.isChecked() else "false",
            "ECHODESK_DEVICE_POLL_INTERVAL": str(self.device_poll_spin.value()),
            "ECHODESK_COMMAND_POLL_INTERVAL": str(self.command_poll_spin.value()),
            "ECHODESK_REMEMBER_LOGIN_DEFAULT": "true" if self.remember_login_checkbox.isChecked() else "false",
            "ECHODESK_THEME": self.theme_combo.currentData(),
        }

        env_path = self._env_file_path()
        existing_lines: list[str] = []
        if env_path.exists():
            existing_lines = env_path.read_text(encoding="utf-8").splitlines()

        written_keys = set()
        new_lines = []
        for line in existing_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                new_lines.append(line)
                continue
            key = stripped.split("=", 1)[0]
            if key in values:
                new_lines.append(f"{key}={values[key]}")
                written_keys.add(key)
            else:
                new_lines.append(line)

        for key in _ENV_KEYS_ORDER:
            if key in values and key not in written_keys:
                new_lines.append(f"{key}={values[key]}")

        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        QMessageBox.information(self, "Settings Saved", "Settings saved. Restart the app for changes to take effect.")
