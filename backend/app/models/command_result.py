"""Command execution result model."""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel


class CommandResult(BaseModel):
    __tablename__ = "command_results"

    command_id = db.Column(db.String(36), db.ForeignKey("commands.id", ondelete="CASCADE"), unique=True, nullable=False)
    execution_status = db.Column(db.String(32), nullable=False)
    output = db.Column(db.JSON, nullable=False, default=dict)
    raw_payload = db.Column(db.JSON, nullable=False, default=dict)
    finished_at = db.Column(db.DateTime(timezone=True), nullable=True)

    command = db.relationship("Command", back_populates="result")
