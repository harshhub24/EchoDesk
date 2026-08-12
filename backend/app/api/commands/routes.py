"""Command routes."""

from __future__ import annotations

from flask import Blueprint, g, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_socketio import emit

from app.constants import COMMAND_TYPES
from app.extensions import db, socketio
from app.models import Command, Device, User
from app.schemas.commands import CommandCreateRequest
from app.security.device_auth import device_auth_required
from app.services.command_service import create_command, list_commands, list_pending_commands_for_device
from app.utils.responses import error_response, success_response


commands_bp = Blueprint("commands", __name__)


@commands_bp.post("/commands")
@jwt_required()
def create_command_route():
    user = db.session.get(User, get_jwt_identity())
    if not user:
        return error_response("User not found", status_code=404)
    payload = CommandCreateRequest.model_validate(request.get_json(force=True)).model_dump()
    if payload["command_type"] not in COMMAND_TYPES:
        return error_response("Unsupported command type", status_code=400)
    device = Device.query.filter_by(id=payload["device_id"], owner_id=user.id).first()
    if not device:
        return error_response("Device not found or not owned by user", status_code=404)
    command = create_command(user, device, payload["command_type"], payload.get("payload"))
    socketio.emit(
        "command_created",
        {
            "success": True,
            "command": {
                "id": command.id,
                "device_id": command.device_id,
                "created_by_id": command.created_by_id,
                "command_type": command.command_type,
                "payload": command.payload,
                "status": command.status,
                "expires_at": command.expires_at.isoformat() if command.expires_at else None,
            },
        },
        room=f"device:{device.id}",
    )
    return success_response(
        "Command created",
        {
            "id": command.id,
            "device_id": command.device_id,
            "created_by_id": command.created_by_id,
            "command_type": command.command_type,
            "payload": command.payload,
            "status": command.status,
        },
        201,
    )


@commands_bp.get("/commands")
@jwt_required()
def list_commands_route():
    user_id = str(get_jwt_identity())
    commands = list_commands(user_id)
    return success_response(
        "Commands retrieved",
        [
            {
                "id": command.id,
                "device_id": command.device_id,
                "created_by_id": command.created_by_id,
                "command_type": command.command_type,
                "payload": command.payload,
                "status": command.status,
                "created_at": command.created_at.isoformat(),
            }
            for command in commands
        ],
    )


@commands_bp.get("/commands/pending")
@device_auth_required
def list_pending_commands_route():
    if g.current_device is not None:
        # Device API key: scoped to exactly this device, already filtered.
        devices = [g.current_device]
    else:
        # Legacy user-JWT path: all of the caller's devices, as before.
        devices = Device.query.filter_by(owner_id=str(g.current_user.id)).all()

    pending_commands = []
    for device in devices:
        pending_commands.extend(list_pending_commands_for_device(device.id))
    return success_response(
        "Pending commands retrieved",
        [
            {
                "id": command.id,
                "device_id": command.device_id,
                "command_type": command.command_type,
                "payload": command.payload,
                "status": command.status,
                "expires_at": command.expires_at.isoformat() if command.expires_at else None,
            }
            for command in pending_commands
        ],
    )

