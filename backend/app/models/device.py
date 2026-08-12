"""Device model."""

from __future__ import annotations

from app.constants import DeviceStatus
from app.extensions import db
from app.models.base import BaseModel


class Device(BaseModel):
    __tablename__ = "devices"

    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)
    device_id = db.Column(db.String(128), unique=True, nullable=False, index=True)
    owner_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_name = db.Column(db.String(255), nullable=False)
    device_type = db.Column(db.String(64), nullable=False)
    hostname = db.Column(db.String(255), nullable=True)
    operating_system = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(32), nullable=False, default=DeviceStatus.UNKNOWN.value)
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=True)
    heartbeat_interval_seconds = db.Column(db.Integer, nullable=False, default=30)
    is_registered = db.Column(db.Boolean, nullable=False, default=True)
    telemetry = db.Column(db.JSON, nullable=False, default=dict)
    last_telemetry_at = db.Column(db.DateTime(timezone=True), nullable=True)

    owner = db.relationship("User", back_populates="devices")
    sessions = db.relationship("DeviceSession", back_populates="device", cascade="all, delete-orphan")
    commands = db.relationship("Command", back_populates="device", cascade="all, delete-orphan")
    api_keys = db.relationship("ApiKey", back_populates="device", cascade="all, delete-orphan")
    files = db.relationship("CommandFile", back_populates="device", cascade="all, delete-orphan")
