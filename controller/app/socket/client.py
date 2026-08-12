"""Socket.IO client wrapper for the Controller.

Connects using the owner's access token (`auth: {token}}`), joining the
`user:{id}` room - the only path a Controller (as opposed to an Agent) is
meant to use (see docs/PHASE_1_ANALYSIS.md §1 and §5).

Per the Phase 1 finding, the backend does not currently broadcast any
device/command updates to that room - so, practically, this connection is
kept alive for session presence and forward-compatibility, not as the
Controller's data source (that's `app/services/*` polling via QTimer,
Phase 6+). If the backend ever adds owner-room broadcasts, only this file
and `app/socket/bridge.py` would need new event handlers - no other layer
of the app assumes anything about realtime delivery today.
"""

from __future__ import annotations

import logging
from typing import Callable

import socketio

from app.config import AppConfig
from app.constants import DEFAULT_REST_TIMEOUT_SECONDS

logger = logging.getLogger("controller.socket.client")

_RECONNECT_DELAY_SECONDS = 5
_RECONNECT_DELAY_MAX_SECONDS = 60


class SocketClient:
    def __init__(self, config: AppConfig, access_token: str):
        self.config = config
        self._access_token = access_token
        self._sio = socketio.Client(
            reconnection=True,
            reconnection_delay=_RECONNECT_DELAY_SECONDS,
            reconnection_delay_max=_RECONNECT_DELAY_MAX_SECONDS,
            logger=False,
            engineio_logger=False,
        )
        self._connected = False

    def set_access_token(self, access_token: str) -> None:
        """Called after a token refresh - takes effect on the next
        (re)connect, since Socket.IO auth only happens at connect time.
        """

        self._access_token = access_token

    def on(self, event_name: str, handler: Callable) -> None:
        self._sio.on(event_name, handler)

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        self._sio.connect(
            self.config.backend_url,
            auth={"token": self._access_token},
            transports=["websocket", "polling"],
            wait_timeout=DEFAULT_REST_TIMEOUT_SECONDS,
        )
        self._connected = True

    def disconnect(self) -> None:
        if self._connected:
            self._sio.disconnect()
        self._connected = False

    def mark_disconnected(self) -> None:
        """Called by the bridge's disconnect handler to keep `.connected`
        accurate even when the disconnect was server/network-initiated
        rather than us calling disconnect() ourselves.
        """

        self._connected = False
