"""Command dispatcher.

Delivered/executing acks and success/failed results only travel over
Socket.IO (the backend has no REST equivalent for command_ack/command_result
- see backend docs/API_REFERENCE.md). If the socket happens to be
disconnected at the moment a command finishes, we queue the ack/result
in-memory and flush it on the next opportunity (call `flush_pending()`
periodically - main.py wires this into the heartbeat loop's tick).
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field

from agent.api.client import RestClient
from agent.commands import handlers, validator
from agent.commands.validator import InvalidCommandError
from agent.constants import CommandStatus
from agent.socket.client import SocketClient

logger = logging.getLogger("agent.commands.dispatcher")


@dataclass
class _PendingMessage:
    kind: str  # "ack" | "result"
    command_id: str
    status: str
    output: dict | None = None
    raw_payload: dict | None = None


@dataclass
class CommandDispatcher:
    rest_client: RestClient
    socket_client: SocketClient | None
    file_root: str | None
    _pending: list[_PendingMessage] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _seen_command_ids: set[str] = field(default_factory=set)
    _seen_lock: threading.Lock = field(default_factory=threading.Lock)

    def handle(self, command: dict) -> None:
        """Process one command end-to-end. Safe to call from multiple threads
        (e.g. one polled via REST, one pushed via socket) for the same
        command - duplicates are ignored.
        """

        try:
            validator.validate_envelope(command)
        except InvalidCommandError as error:
            logger.error("Rejecting invalid command envelope: %s", error)
            return

        command_id = command["id"]
        with self._seen_lock:
            if command_id in self._seen_command_ids:
                logger.debug("Command %s already handled/handling, skipping duplicate delivery", command_id)
                return
            self._seen_command_ids.add(command_id)

        command_type = command["command_type"]
        payload = command.get("payload") or {}

        if validator.is_expired(command.get("expires_at")):
            logger.warning("Command %s (%s) expired before execution, skipping", command_id, command_type)
            return

        try:
            validator.validate_payload(command_type, payload)
        except InvalidCommandError as error:
            logger.error("Command %s payload invalid: %s", command_id, error)
            self._send_result(command_id, CommandStatus.FAILED.value, {"error": str(error)})
            return

        self._send_ack(command_id, CommandStatus.DELIVERED.value)
        self._send_ack(command_id, CommandStatus.EXECUTING.value)

        try:
            output = handlers.execute(command_type, self.rest_client, command_id, self.file_root, payload)
            logger.info("Command %s (%s) succeeded", command_id, command_type)
            self._send_result(command_id, CommandStatus.SUCCESS.value, output)
        except Exception as error:
            logger.exception("Command %s (%s) failed", command_id, command_type)
            self._send_result(command_id, CommandStatus.FAILED.value, {"error": str(error)})

    # --- Ack/result delivery with retry-on-reconnect ----------------------------------

    def _send_ack(self, command_id: str, status: str) -> None:
        if not self._try_emit_ack(command_id, status):
            with self._lock:
                self._pending.append(_PendingMessage(kind="ack", command_id=command_id, status=status))

    def _send_result(self, command_id: str, execution_status: str, output: dict) -> None:
        if not self._try_emit_result(command_id, execution_status, output):
            with self._lock:
                self._pending.append(
                    _PendingMessage(kind="result", command_id=command_id, status=execution_status, output=output)
                )

    def _try_emit_ack(self, command_id: str, status: str) -> bool:
        if not self.socket_client or not self.socket_client.connected:
            return False
        try:
            self.socket_client.emit_command_ack(command_id, status)
            return True
        except Exception as error:
            logger.warning("Failed to emit command_ack for %s: %s", command_id, error)
            return False

    def _try_emit_result(self, command_id: str, execution_status: str, output: dict) -> bool:
        if not self.socket_client or not self.socket_client.connected:
            return False
        try:
            self.socket_client.emit_command_result(command_id, execution_status, output)
            return True
        except Exception as error:
            logger.warning("Failed to emit command_result for %s: %s", command_id, error)
            return False

    def flush_pending(self) -> None:
        """Retry any queued acks/results. Call this periodically (e.g. from
        the heartbeat loop) and whenever the socket reconnects.
        """

        if not self._pending:
            return
        with self._lock:
            still_pending: list[_PendingMessage] = []
            for message in self._pending:
                delivered = (
                    self._try_emit_ack(message.command_id, message.status)
                    if message.kind == "ack"
                    else self._try_emit_result(message.command_id, message.status, message.output or {})
                )
                if not delivered:
                    still_pending.append(message)
            if len(still_pending) != len(self._pending):
                logger.info("Flushed %d queued command message(s)", len(self._pending) - len(still_pending))
            self._pending = still_pending
