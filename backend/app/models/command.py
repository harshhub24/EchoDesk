"""Command model."""

from __future__ import annotations

from app.constants import CommandStatus
from app.extensions import db
from app.models.base import BaseModel


class Command(BaseModel):
    __tablename__ = "commands"

    device_id = db.Column(db.String(36), db.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    command_type = db.Column(db.String(64), nullable=False, index=True)
    payload = db.Column(db.JSON, nullable=False, default=dict)
    status = db.Column(db.String(32), nullable=False, default=CommandStatus.PENDING.value, index=True)
    delivered_at = db.Column(db.DateTime(timezone=True), nullable=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    failure_reason = db.Column(db.String(512), nullable=True)

    device = db.relationship("Device", back_populates="commands")
    creator = db.relationship("User", foreign_keys=[created_by_id])
    result = db.relationship("CommandResult", back_populates="command", uselist=False, cascade="all, delete-orphan")
    files = db.relationship("CommandFile", back_populates="command", cascade="all, delete-orphan")
