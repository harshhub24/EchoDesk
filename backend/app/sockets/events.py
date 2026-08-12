"""Socket.IO event handlers."""

from __future__ import annotations

from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import emit

from app.constants import CommandStatus, DeviceStatus
from app.extensions import db, socketio
from app.models import Command, Device, DeviceSession, User
from app.security.device_auth import authenticate_device_api_key
from app.services.command_service import mark_command_delivered, mark_command_executing, record_command_result, validate_ack_status, validate_result_status
from app.services.device_service import record_heartbeat
from app.sockets.manager import connection_manager
from app.utils.time import utcnow

# sid -> device.id, populated only for connections authenticated with a device
# API key (as opposed to a user JWT). Lets heartbeat/command events work without
# the caller having to keep re-sending owner_id/device_id on every message.
_device_sessions: dict[str, str] = {}


def _resolve_user_from_token(token: str | None) -> User:
    if not token:
        raise ValueError("Missing authentication token")
    decoded = decode_token(token)
    user = db.session.get(User, decoded["sub"])
    if not user:
        raise ValueError("User not found")
    return user


def _register_device_session(device: Device, sid: str) -> None:
    connection_manager.connect_device(device.id, sid)
    _device_sessions[sid] = device.id
    session = DeviceSession(
        user_id=device.owner_id,
        device_id=device.id,
        socket_session_id=sid,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
        connected_at=utcnow(),
        is_active=True,
    )
    device.status = DeviceStatus.ONLINE.value
    device.last_seen_at = utcnow()
    db.session.add(session)
    db.session.commit()


def register_socket_events() -> None:
    """Register Socket.IO events."""

    @socketio.on("connect")
    def handle_connect(auth):
        try:
            auth = auth or {}
            api_key = auth.get("api_key")
            if api_key:
                # Device-credential path: no user login needed by the Agent.
                resolved = authenticate_device_api_key(api_key)
                if not resolved:
                    raise ValueError("Invalid or expired API key")
                user, device = resolved
                connection_manager.connect_user(user.id, request.sid)
                _register_device_session(device, request.sid)
                emit("connected", {"success": True, "message": "Connected"})
                emit("registered", {"success": True, "device_id": device.id})
            else:
                # Legacy path: user access token (used by controller apps, and
                # by an Agent that still calls register_device separately).
                token = auth.get("token")
                user = _resolve_user_from_token(token)
                connection_manager.connect_user(user.id, request.sid)
                emit("connected", {"success": True, "message": "Connected"})
        except Exception as error:
            emit("error", {"success": False, "message": str(error)})
            return False

    @socketio.on("register_device")
    def handle_register_device(data):
        try:
            device = Device.query.filter_by(device_id=data["device_id"]).first()
            if not device:
                raise ValueError("Device not found")
            _register_device_session(device, request.sid)
            emit("registered", {"success": True, "device_id": device.id})
        except Exception as error:
            emit("error", {"success": False, "message": str(error)})

    @socketio.on("heartbeat")
    def handle_heartbeat(data):
        try:
            data = data or {}
            device_row_id = _device_sessions.get(request.sid)
            if device_row_id:
                # This socket authenticated with a device API key (or already
                # called register_device) - device is already known.
                device = db.session.get(Device, device_row_id)
                if not device:
                    raise ValueError("Device not found")
                device = record_heartbeat(device, data.get("status"), data.get("telemetry"))
            else:
                # Legacy path: caller must tell us who it is on every heartbeat.
                from app.services.device_service import heartbeat_device

                device = heartbeat_device(data["owner_id"], data["device_id"], data.get("status"), data.get("telemetry"))
            emit("heartbeat_ack", {"success": True, "device_id": device.id})
        except Exception as error:
            emit("error", {"success": False, "message": str(error)})

    @socketio.on("command_ack")
    def handle_command_ack(data):
        try:
            command = db.session.get(Command, data["command_id"])
            if not command:
                raise ValueError("Command not found")
            status = validate_ack_status(data.get("status", CommandStatus.DELIVERED.value))
            if status == CommandStatus.DELIVERED.value:
                mark_command_delivered(command)
            elif status == CommandStatus.EXECUTING.value:
                mark_command_executing(command)
            emit("command_ack_received", {"success": True, "command_id": command.id})
        except Exception as error:
            emit("error", {"success": False, "message": str(error)})

    @socketio.on("command_result")
    def handle_command_result(data):
        try:
            command = db.session.get(Command, data["command_id"])
            if not command:
                raise ValueError("Command not found")
            result = record_command_result(
                command,
                validate_result_status(data["execution_status"]),
                output=data.get("output"),
                raw_payload=data.get("raw_payload"),
            )
            emit("command_result_received", {"success": True, "result_id": result.id})
        except Exception as error:
            emit("error", {"success": False, "message": str(error)})

    @socketio.on("disconnect")
    def handle_disconnect():
        _device_sessions.pop(request.sid, None)
        connection_manager.disconnect(request.sid)

