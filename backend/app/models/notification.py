"""Notification model."""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.String(512), nullable=False)
    category = db.Column(db.String(64), nullable=False, index=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    read_at = db.Column(db.DateTime(timezone=True), nullable=True)
    details = db.Column(db.JSON, nullable=False, default=dict)

    user = db.relationship("User", back_populates="notifications")
