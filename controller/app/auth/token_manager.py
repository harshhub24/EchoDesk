"""Session lifecycle: login, logout, proactive access-token refresh, and
"Remember Login" persistence. A QObject so it can own a QTimer and emit
signals views subscribe to.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer, Signal

from app.api import endpoints
from app.api.client import ApiError, RestClient
from app.auth import secure_storage
from app.config import AppConfig
from app.constants import ACCESS_TOKEN_REFRESH_MARGIN_SECONDS
from app.models import Session

logger = logging.getLogger("controller.auth.token_manager")

# Matches the backend's configured access token TTL (see PHASE_1_ANALYSIS.md
# §1) - used only to schedule the proactive refresh timer, not enforced
# client-side otherwise.
_ACCESS_TOKEN_TTL_SECONDS = 15 * 60


class TokenManager(QObject):
    session_started = Signal(Session)
    session_ended = Signal()
    refresh_failed = Signal(str)  # message - session is no longer valid, caller should show Login

    def __init__(self, config: AppConfig, rest_client: RestClient):
        super().__init__()
        self.config = config
        self.rest_client = rest_client
        self.session: Session | None = None

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._proactive_refresh)

        # Wire the REST client's reactive 401 handler to a synchronous
        # refresh (this runs on whatever thread issued the failing request -
        # typically a worker thread, which is fine, this is just an HTTP
        # call, not a UI operation).
        self.rest_client.on_unauthorized = self._synchronous_refresh

    # --- Public API ----------------------------------------------------------------

    def login(self, email: str, password: str, remember: bool) -> tuple[Session, bool]:
        """Pure network call, safe to run on a worker thread - does NOT
        touch any QObject (no QTimer start, no SocketBridge construction).
        Returns (session, remember) for the caller to hand to
        `activate_session` back on the Qt main thread.
        """

        response = endpoints.login(self.rest_client, email, password)
        data = response["data"]
        session = Session(user_id=data["user_id"], access_token=data["access_token"], refresh_token=data["refresh_token"], email=email)
        return session, remember

    def restore_session(self) -> tuple[Session, bool] | None:
        """Pure network call (see `login` docstring re: thread-safety).
        Called at startup: if a refresh token was persisted, use it to get
        a fresh access token without prompting for a password again.
        """

        stored_refresh_token = secure_storage.load_refresh_token(self.config.data_dir)
        if not stored_refresh_token:
            return None

        self.rest_client.set_tokens(None, stored_refresh_token)
        try:
            response = endpoints.refresh_tokens(self.rest_client)
        except ApiError as error:
            logger.info("Stored refresh token is no longer valid: %s", error)
            secure_storage.clear_refresh_token(self.config.data_dir)
            return None

        data = response["data"]
        session = Session(user_id="", access_token=data["access_token"], refresh_token=data["refresh_token"])
        return session, True

    def activate_session(self, session: Session, remember: bool) -> None:
        """Applies a session: sets REST client tokens, persists the refresh
        token if requested, starts the proactive-refresh QTimer, and emits
        `session_started`. MUST be called on the Qt main thread - it starts
        a QTimer and (via the connected `session_started` slot in
        AppState) constructs a QObject (SocketBridge). Callers get here via
        `login`/`restore_session`'s worker-thread result being delivered
        through a Qt signal (see app/utils/workers.py), which Qt marshals
        back to the main thread automatically - see AppState._activate for
        the call site.
        """

        self.session = session
        self.rest_client.set_tokens(session.access_token, session.refresh_token)

        if remember:
            secure_storage.save_refresh_token(self.config.data_dir, session.refresh_token)
        else:
            secure_storage.clear_refresh_token(self.config.data_dir)

        self._schedule_refresh()
        self.session_started.emit(session)

    def logout(self) -> None:
        """Pure network call (best-effort), safe on a worker thread. Local
        state cleanup that touches the QTimer happens in
        `deactivate_session`, called separately on the main thread - see
        AppState.logout.
        """

        try:
            endpoints.logout(self.rest_client, self.session.refresh_token if self.session else None)
        except ApiError as error:
            logger.warning("Logout call failed (clearing local session anyway): %s", error)

    def deactivate_session(self) -> None:
        """Stops the refresh QTimer and clears session state. MUST be
        called on the Qt main thread (see `activate_session` docstring for
        why).
        """

        self._refresh_timer.stop()
        self.session = None
        self.rest_client.clear_tokens()
        secure_storage.clear_refresh_token(self.config.data_dir)
        self.session_ended.emit()

    # --- Internal --------------------------------------------------------------------

    def _schedule_refresh(self) -> None:
        delay_ms = max((_ACCESS_TOKEN_TTL_SECONDS - ACCESS_TOKEN_REFRESH_MARGIN_SECONDS), 5) * 1000
        self._refresh_timer.start(delay_ms)

    def _proactive_refresh(self) -> None:
        if not self.session:
            return
        try:
            response = endpoints.refresh_tokens(self.rest_client)
        except ApiError as error:
            logger.warning("Proactive token refresh failed: %s", error)
            self.refresh_failed.emit(str(error))
            return

        data = response["data"]
        self.session.access_token = data["access_token"]
        self.session.refresh_token = data["refresh_token"]
        self.rest_client.set_tokens(self.session.access_token, self.session.refresh_token)

        stored = secure_storage.load_refresh_token(self.config.data_dir)
        if stored is not None:
            secure_storage.save_refresh_token(self.config.data_dir, self.session.refresh_token)

        self._schedule_refresh()

    def _synchronous_refresh(self) -> bool:
        """Called by RestClient on a 401, potentially from a worker thread.
        Pure HTTP + in-memory state update, safe off the Qt main thread.
        """

        if not self.rest_client.refresh_token:
            return False
        try:
            response = endpoints.refresh_tokens(self.rest_client)
        except ApiError as error:
            logger.warning("Reactive token refresh (on 401) failed: %s", error)
            return False

        data = response["data"]
        if self.session:
            self.session.access_token = data["access_token"]
            self.session.refresh_token = data["refresh_token"]
        self.rest_client.set_tokens(data["access_token"], data["refresh_token"])
        return True
