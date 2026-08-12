"""Heartbeat loop.

REST is the source of truth (works even if the socket is temporarily down);
if the socket happens to be connected we also emit a lightweight heartbeat
over it, which is harmless (the backend just updates the same fields) and
keeps the realtime connection visibly alive.
"""

from __future__ import annotations

import logging
import threading

from agent.api import endpoints
from agent.api.client import ApiError, RestClient
from agent.constants import DeviceStatus
from agent.socket.client import SocketClient
from agent.system import device as device_info

logger = logging.getLogger("agent.heartbeat")


class HeartbeatLoop:
    def __init__(self, rest_client: RestClient, interval_seconds: int, socket_client: SocketClient | None = None):
        self._rest_client = rest_client
        self._socket_client = socket_client
        self._interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="heartbeat", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        # Send one immediately on startup, then on the configured interval.
        while not self._stop_event.is_set():
            self._send_once()
            self._stop_event.wait(self._interval_seconds)

    def _send_once(self) -> None:
        telemetry = device_info.collect_telemetry()
        try:
            endpoints.send_heartbeat(self._rest_client, DeviceStatus.ONLINE.value, telemetry)
            logger.debug("Heartbeat sent (cpu=%.1f%% ram=%.1f%%)", telemetry.get("cpu_percent", 0), telemetry.get("ram_percent", 0))
        except ApiError as error:
            logger.error("Heartbeat failed: %s", error)

        if self._socket_client is not None and self._socket_client.connected:
            try:
                self._socket_client.emit_heartbeat(DeviceStatus.ONLINE.value, telemetry)
            except Exception as error:  # socket emit failures shouldn't kill the loop
                logger.warning("Socket heartbeat emit failed (non-fatal): %s", error)
