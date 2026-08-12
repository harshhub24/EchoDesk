"""Socket.IO client wrapper.

Connects using the device API key (auth: {"api_key": ...}), matching the
backend's device-auth path added in v0.2.0 - no separate register_device
call is needed on this path, the backend auto-registers the device room on
connect.

python-socketio's Client already handles reconnection with backoff when
constructed with reconnection=True; we just configure sane bounds and wire
up logging + our own event handlers.
"""

from __future__ import annotations

import logging
from typing import Callable

import socketio

from agent.config import AgentConfig
from agent.constants import (
    DEFAULT_SOCKET_RECONNECT_DELAY_MAX_SECONDS,
    DEFAULT_SOCKET_RECONNECT_DELAY_SECONDS,
)

logger = logging.getLogger("agent.socket.client")


class SocketClient:
    def __init__(self, config: AgentConfig, api_key: str):
        self.config = config
        self._api_key = api_key
        self._sio = socketio.Client(
            reconnection=True,
            reconnection_delay=DEFAULT_SOCKET_RECONNECT_DELAY_SECONDS,
            reconnection_delay_max=DEFAULT_SOCKET_RECONNECT_DELAY_MAX_SECONDS,
            logger=False,
            engineio_logger=False,
        )
        self._connected = False
        self._register_lifecycle_handlers()

    # --- Lifecycle -----------------------------------------------------------------

    def _register_lifecycle_handlers(self) -> None:
        @self._sio.event
        def connect():
            self._connected = True
            logger.info("Socket connected")

        @self._sio.event
        def disconnect():
            self._connected = False
            logger.warning("Socket disconnected")

        @self._sio.event
        def connected(data):
            logger.info("Server ack: %s", data)

        @self._sio.event
        def registered(data):
            logger.info("Device registered on socket: %s", data)

        @self._sio.event
        def error(data):
            logger.error("Socket error event: %s", data)

    def on(self, event_name: str, handler: Callable) -> None:
        self._sio.on(event_name, handler)

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        url = self.config.backend_url
        logger.info("Connecting to socket at %s", url)
        self._sio.connect(
            url,
            auth={"api_key": self._api_key},
            transports=["websocket", "polling"],
            wait_timeout=self.config.rest_timeout_seconds,
        )

    def disconnect(self) -> None:
        if self._connected:
            self._sio.disconnect()

    def wait(self) -> None:
        """Block the calling thread, servicing socket events, until disconnected."""

        self._sio.wait()

    # --- Emitters --------------------------------------------------------------------

    def emit_heartbeat(self, status: str, telemetry: dict) -> None:
        if not self._connected:
            return
        self._sio.emit("heartbeat", {"status": status, "telemetry": telemetry})

    def emit_command_ack(self, command_id: str, status: str) -> None:
        self._sio.emit("command_ack", {"command_id": command_id, "status": status})

    def emit_command_result(self, command_id: str, execution_status: str, output: dict | None = None, raw_payload: dict | None = None) -> None:
        self._sio.emit(
            "command_result",
            {
                "command_id": command_id,
                "execution_status": execution_status,
                "output": output or {},
                "raw_payload": raw_payload or {},
            },
        )
