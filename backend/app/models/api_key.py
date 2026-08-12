"""API key model.

Originally scaffolded for future integrations and unused. Now backs device-level
authentication: a key is minted for one specific device (device_id) so an Agent
process can authenticate without holding the owning user's password/refresh token.
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel


class ApiKey(BaseModel):
    __tablename__ = "api_keys"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = db.Column(db.String(36), db.ForeignKey("devices.id", ondelete="CASCADE"), nullable=True, index=True)
    key_name = db.Column(db.String(255), nullable=False)
    key_prefix = db.Column(db.String(16), nullable=False, index=True)
    hashed_secret = db.Column(db.String(255), nullable=False)
    last_used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    user = db.relationship("User", back_populates="api_keys")
    device = db.relationship("Device", back_populates="api_keys")
