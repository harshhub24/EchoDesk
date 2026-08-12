"""Device session model."""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel


class DeviceSession(BaseModel):
    __tablename__ = "device_sessions"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = db.Column(db.String(36), db.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    socket_session_id = db.Column(db.String(128), nullable=True, index=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    connected_at = db.Column(db.DateTime(timezone=True), nullable=False)
    disconnected_at = db.Column(db.DateTime(timezone=True), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    user = db.relationship("User", back_populates="sessions")
    device = db.relationship("Device", back_populates="sessions")
