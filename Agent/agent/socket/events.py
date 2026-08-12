"""Wires the `command_created` realtime event to a caller-supplied handler.

Kept separate from client.py so main.py can inject the actual command
dispatcher without socket/client.py needing to know anything about the
commands package (keeps module boundaries clean per the requested project
structure).
"""

from __future__ import annotations

import logging
import threading
from typing import Callable

from agent.socket.client import SocketClient

logger = logging.getLogger("agent.socket.events")


def register_command_handler(socket_client: SocketClient, handler: Callable[[dict], None]) -> None:
    """handler receives the full command dict pushed by `command_created`.

    Runs the handler on a background thread so a slow command (e.g. a large
    file transfer) never blocks the Socket.IO event loop / heartbeat.
    """

    def _on_command_created(data: dict) -> None:
        # Backend wraps the payload as {"success": True, "command": {...}}
        # (see backend app/api/commands/routes.py) - unwrap it here so every
        # downstream consumer (the dispatcher) only ever sees a bare command
        # dict, same shape as what /commands/pending returns.
        command = data.get("command") if isinstance(data, dict) and "command" in data else data
        if not command:
            logger.warning("Received command_created event with no command payload: %s", data)
            return

        logger.info("Realtime command received: %s (%s)", command.get("id"), command.get("command_type"))
        thread = threading.Thread(
            target=handler, args=(command,), daemon=True, name=f"cmd-{command.get('id', 'unknown')}"
        )
        thread.start()

    socket_client.on("command_created", _on_command_created)
