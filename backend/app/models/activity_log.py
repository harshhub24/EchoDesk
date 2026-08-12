"""Audit log entries."""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel


class ActivityLog(BaseModel):
    __tablename__ = "activity_logs"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    device_id = db.Column(db.String(36), db.ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
    activity_type = db.Column(db.String(64), nullable=False, index=True)
    category = db.Column(db.String(64), nullable=False, index=True)
    message = db.Column(db.String(512), nullable=False)
    details = db.Column(db.JSON, nullable=False, default=dict)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)

    user = db.relationship("User", back_populates="activity_logs")
