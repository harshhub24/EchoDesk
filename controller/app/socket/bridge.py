"""Bridges Socket.IO's own background-thread callbacks into Qt signals, and
owns the background thread that keeps the connection alive/reconnecting so
the Qt main thread is never blocked by `connect()`'s handshake.
"""

from __future__ import annotations

import logging
import threading

from PySide6.QtCore import QObject, Signal

from app.config import AppConfig
from app.socket.client import SocketClient

logger = logging.getLogger("controller.socket.bridge")

_CONNECT_RETRY_DELAY_SECONDS = 10


class SocketBridge(QObject):
    """Qt-signal-emitting wrapper around SocketClient. Safe to `connect()`
    a slot to these signals normally - PySide6 marshals cross-thread
    emissions to the receiving QObject's thread (the Qt main thread here)
    automatically via a queued connection.
    """

    connected = Signal()
    disconnected = Signal()
    connection_error = Signal(str)

    def __init__(self, config: AppConfig, access_token: str, parent: QObject | None = None):
        super().__init__(parent)
        self.config = config
        self.client = SocketClient(config, access_token)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self.client.on("connect", self._on_connect)
        self.client.on("disconnect", self._on_disconnect)
        self.client.on("connected", lambda _data: None)  # server ack, nothing to do
        self.client.on("error", self._on_error)

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._connection_loop, name="controller-socket", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self.client.disconnect()
        if self._thread:
            self._thread.join(timeout=5)

    def update_access_token(self, access_token: str) -> None:
        self.client.set_access_token(access_token)

    # --- Internal --------------------------------------------------------------------

    def _connection_loop(self) -> None:
        while not self._stop_event.is_set():
            if not self.client.connected:
                try:
                    self.client.connect()
                except Exception as error:
                    logger.warning("Socket connect attempt failed, will retry: %s", error)
                    self.connection_error.emit(str(error))
            self._stop_event.wait(_CONNECT_RETRY_DELAY_SECONDS)

    def _on_connect(self) -> None:
        logger.info("Socket connected")
        self.connected.emit()

    def _on_disconnect(self) -> None:
        logger.warning("Socket disconnected")
        self.client.mark_disconnected()
        self.disconnected.emit()

    def _on_error(self, data) -> None:
        message = data.get("message", str(data)) if isinstance(data, dict) else str(data)
        logger.error("Socket error event: %s", message)
        self.connection_error.emit(message)
