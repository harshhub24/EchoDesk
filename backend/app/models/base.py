"""Base model mixins."""

from __future__ import annotations

import uuid

from app.extensions import db
from app.utils.time import utcnow


class BaseModel(db.Model):
    """Common fields for persisted models."""

    __abstract__ = True

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
