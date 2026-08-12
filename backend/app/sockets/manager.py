"""Connection and room management for Socket.IO."""

from __future__ import annotations

from dataclasses import dataclass, field

from flask_socketio import join_room, leave_room


@dataclass(slots=True)
class SocketConnectionManager:
    """Track logical user and device rooms."""

    active_connections: dict[str, dict[str, str]] = field(default_factory=dict)

    def connect_user(self, user_id: str, sid: str) -> None:
        # merge rather than overwrite so a connection can be tied to both a
        # user room and a device room at once (device API-key connections)
        self.active_connections.setdefault(sid, {})["user_id"] = user_id
        join_room(f"user:{user_id}")

    def connect_device(self, device_id: str, sid: str) -> None:
        self.active_connections.setdefault(sid, {})["device_id"] = device_id
        join_room(f"device:{device_id}")

    def disconnect(self, sid: str) -> None:
        data = self.active_connections.pop(sid, {})
        if user_id := data.get("user_id"):
            leave_room(f"user:{user_id}")
        if device_id := data.get("device_id"):
            leave_room(f"device:{device_id}")


connection_manager = SocketConnectionManager()

