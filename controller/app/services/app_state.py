"""Central application state. Views subscribe to its signals; nobody calls
`api`/`socket` directly - everything routes through here or through a
Phase 6+ service that itself only talks to AppState's `rest_client`.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QThreadPool, Signal

from app.api.client import ApiError, RestClient
from app.auth.token_manager import TokenManager
from app.config import AppConfig
from app.models import Session
from app.socket.bridge import SocketBridge
from app.utils.workers import run_async

logger = logging.getLogger("controller.services.app_state")


class AppState(QObject):
    # Auth lifecycle
    session_restored = Signal(Session)
    session_restore_failed = Signal()  # no valid stored session - show Login
    login_succeeded = Signal(Session)
    login_failed = Signal(str)
    logged_out = Signal()

    # Socket lifecycle (see app/socket/bridge.py docstring re: current scope)
    socket_connected = Signal()
    socket_disconnected = Signal()

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.thread_pool = QThreadPool.globalInstance()

        self.rest_client = RestClient(config)
        self.token_manager = TokenManager(config, self.rest_client)
        self.token_manager.session_started.connect(self._on_session_started)
        self.token_manager.session_ended.connect(self._on_session_ended)
        self.token_manager.refresh_failed.connect(self._on_refresh_failed)

        self.socket_bridge: SocketBridge | None = None

    # --- Startup -----------------------------------------------------------------------

    def try_restore_session(self) -> None:
        """Attempt silent login from a persisted refresh token. Network
        call runs off-thread; the result callback (which Qt marshals back
        to the main thread - see app/utils/workers.py) applies it.
        """

        run_async(
            self.token_manager.restore_session,
            on_result=self._handle_restore_result,
            on_error=lambda _err, _tb: self.session_restore_failed.emit(),
        )

    def _handle_restore_result(self, result: tuple | None) -> None:
        if result is None:
            self.session_restore_failed.emit()
            return
        session, remember = result
        self.token_manager.activate_session(session, remember)
        self.session_restored.emit(session)

    # --- Login/logout ---------------------------------------------------------------------

    def login(self, email: str, password: str, remember: bool) -> None:
        run_async(
            self.token_manager.login,
            email,
            password,
            remember,
            on_result=self._handle_login_result,
            on_error=lambda error, _tb: self.login_failed.emit(
                error.message if isinstance(error, ApiError) else str(error)
            ),
        )

    def _handle_login_result(self, result: tuple) -> None:
        session, remember = result
        self.token_manager.activate_session(session, remember)
        self.login_succeeded.emit(session)

    def logout(self) -> None:
        self._stop_socket()
        run_async(
            self.token_manager.logout,
            on_result=lambda _r: self.token_manager.deactivate_session(),
            on_error=lambda _err, _tb: self.token_manager.deactivate_session(),
        )

    # --- Internal --------------------------------------------------------------------------

    def _on_session_started(self, session: Session) -> None:
        self._start_socket(session.access_token)

    def _on_session_ended(self) -> None:
        self._stop_socket()
        self.logged_out.emit()

    def _on_refresh_failed(self, _message: str) -> None:
        # Refresh token is dead - treat exactly like a logout from the UI's
        # perspective (force back to Login). No need to call the backend
        # logout endpoint for an already-invalid session.
        self.token_manager.deactivate_session()

    def _start_socket(self, access_token: str) -> None:
        self._stop_socket()
        self.socket_bridge = SocketBridge(self.config, access_token, parent=self)
        self.socket_bridge.connected.connect(self.socket_connected)
        self.socket_bridge.disconnected.connect(self.socket_disconnected)
        self.socket_bridge.start()

    def _stop_socket(self) -> None:
        if self.socket_bridge:
            self.socket_bridge.stop()
            self.socket_bridge = None

    def shutdown(self) -> None:
        self._stop_socket()
        self.rest_client.close()
