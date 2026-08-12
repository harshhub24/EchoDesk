"""Socket-related HTTP helpers and docs-friendly routes."""

from __future__ import annotations

from flask import Blueprint

from app.utils.responses import success_response


websocket_bp = Blueprint("websocket", __name__)


@websocket_bp.get("/websocket")
def websocket_info():
    return success_response(
        "WebSocket transport available",
        {"socketio": True, "events": ["connect", "register_device", "heartbeat", "command_ack", "command_result"]},
    )
