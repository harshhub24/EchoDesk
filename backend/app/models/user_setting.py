"""User settings model."""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel


class UserSetting(BaseModel):
    __tablename__ = "user_settings"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    timezone = db.Column(db.String(64), nullable=False, default="UTC")
    locale = db.Column(db.String(16), nullable=False, default="en-US")
    notification_preferences = db.Column(db.JSON, nullable=False, default=dict)
    security_preferences = db.Column(db.JSON, nullable=False, default=dict)

    user = db.relationship("User", back_populates="settings")
