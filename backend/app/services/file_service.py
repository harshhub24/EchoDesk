"""Byte-level file storage for command-attached files (transfers/screenshots).

Files are stored on local disk under the existing UPLOAD_FOLDER (device -> owner
direction) / DOWNLOAD_FOLDER (owner -> device direction) config paths, which were
already provisioned by create_app() but previously unused by any route. Only
metadata lives in the database (app.models.command_file.CommandFile).
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import BinaryIO

from flask import current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Command, CommandFile

# Conservative ceiling for this JSON/command-oriented transport. Large media
# should not be pushed through this path; it exists for file-manager-scale
# transfers and screenshots, not bulk backups.
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024


class FileTooLargeError(ValueError):
    pass


def _storage_root(direction: str) -> Path:
    config_key = "UPLOAD_FOLDER" if direction == "device_to_owner" else "DOWNLOAD_FOLDER"
    root = Path(current_app.config[config_key])
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_command_file(
    command: Command,
    device_id: str,
    direction: str,
    uploaded_by: str,
    filename: str,
    content_type: str | None,
    stream: BinaryIO,
) -> CommandFile:
    if direction not in ("device_to_owner", "owner_to_device"):
        raise ValueError("Invalid transfer direction")
    if uploaded_by not in ("device", "owner"):
        raise ValueError("Invalid uploader type")

    safe_name = secure_filename(filename) or "file.bin"
    stored_name = f"{command.id}_{uuid.uuid4().hex}_{safe_name}"
    dest = _storage_root(direction) / stored_name

    sha256 = hashlib.sha256()
    size = 0
    try:
        with open(dest, "wb") as handle:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_FILE_SIZE_BYTES:
                    raise FileTooLargeError(f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES} bytes")
                sha256.update(chunk)
                handle.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise

    record = CommandFile(
        command_id=command.id,
        device_id=device_id,
        direction=direction,
        original_filename=filename[:512] if filename else "file.bin",
        stored_relative_path=stored_name,
        content_type=content_type,
        size_bytes=size,
        checksum_sha256=sha256.hexdigest(),
        uploaded_by=uploaded_by,
    )
    db.session.add(record)
    db.session.commit()
    return record


def list_command_files(command_id: str) -> list[CommandFile]:
    return CommandFile.query.filter_by(command_id=command_id).order_by(CommandFile.created_at.asc()).all()


def get_command_file(file_id: str) -> CommandFile | None:
    return db.session.get(CommandFile, file_id)


def resolve_file_path(command_file: CommandFile) -> Path:
    return _storage_root(command_file.direction) / command_file.stored_relative_path


def delete_command_file(command_file: CommandFile) -> None:
    resolve_file_path(command_file).unlink(missing_ok=True)
    db.session.delete(command_file)
    db.session.commit()
