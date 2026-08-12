"""Command file model.

Backs real byte-level file transfer for FILE_DOWNLOAD_REQUEST, FILE_UPLOAD_REQUEST
and SCREENSHOT_REQUEST commands. A row represents one file attached to a command,
travelling in one direction:

  - "device_to_owner": the Agent captured/read a file (or screenshot) and uploaded
    it here so the owner can download it.
  - "owner_to_device": the owner uploaded a file here so the Agent can download and
    write it to the device's filesystem.

Bytes are stored on disk under BaseConfig.UPLOAD_FOLDER / DOWNLOAD_FOLDER (already
provisioned by create_app but never wired to a route); this table only stores
metadata + the relative stored path.
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel


class CommandFile(BaseModel):
    __tablename__ = "command_files"

    command_id = db.Column(db.String(36), db.ForeignKey("commands.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = db.Column(db.String(36), db.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = db.Column(db.String(32), nullable=False)  # "device_to_owner" | "owner_to_device"
    original_filename = db.Column(db.String(512), nullable=False)
    stored_relative_path = db.Column(db.String(1024), nullable=False)
    content_type = db.Column(db.String(128), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=False, default=0)
    checksum_sha256 = db.Column(db.String(64), nullable=True)
    uploaded_by = db.Column(db.String(16), nullable=False)  # "device" | "owner"

    command = db.relationship("Command", back_populates="files")
    device = db.relationship("Device", back_populates="files")
