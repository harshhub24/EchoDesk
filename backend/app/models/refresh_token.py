"""Refresh token revocation tracking."""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel


class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(32), nullable=False, default="refresh")
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    is_revoked = db.Column(db.Boolean, nullable=False, default=False)
    device_session_id = db.Column(db.String(36), db.ForeignKey("device_sessions.id", ondelete="SET NULL"), nullable=True)

    user = db.relationship("User", back_populates="refresh_tokens")
