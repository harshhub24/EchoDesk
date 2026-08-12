"""Main window shell.

Wires session lifecycle (Login <-> Shell) - the Shell itself (sidebar +
top nav + pages) is built in app/views/shell.py, extended with a new page
each phase from here on.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from app.constants import APP_NAME
from app.models import Session
from app.services import AppState
from app.views.login_view import LoginView
from app.views.shell import Shell
from app.widgets.card import GlassCard

logger = logging.getLogger("controller.views.main_window")


def _placeholder_page(text: str) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    card = GlassCard()
    label = QLabel(text)
    label.setProperty("cssClass", "heading")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    card.body_layout.addWidget(label)
    card.setFixedWidth(420)

    layout.addWidget(card)
    return page


class MainWindow(QMainWindow):
    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state

        self.setWindowTitle(APP_NAME)
        self.resize(1280, 800)
        self.setMinimumSize(1024, 640)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._checking_page = _placeholder_page("Checking session...")
        self._login_page = LoginView(app_state)
        self._shell = Shell(app_state)

        for page in (self._checking_page, self._login_page, self._shell):
            self._stack.addWidget(page)

        self._stack.setCurrentWidget(self._checking_page)

        self.app_state.session_restored.connect(self._on_session_ready)
        self.app_state.session_restore_failed.connect(self._on_logged_out)
        self.app_state.login_succeeded.connect(self._on_session_ready)
        self.app_state.logged_out.connect(self._on_logged_out)

    def _on_session_ready(self, session: Session) -> None:
        logger.info("Session ready for user_id=%s", session.user_id or "(restored)")
        self._stack.setCurrentWidget(self._shell)
        self._shell.activate()

    def _on_logged_out(self) -> None:
        self._shell.stop_all()
        self._stack.setCurrentWidget(self._login_page)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override naming
        self._shell.stop_all()
        self.app_state.shutdown()
        super().closeEvent(event)


