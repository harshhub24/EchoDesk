"""Command file transfer routes.

Gives FILE_DOWNLOAD_REQUEST / FILE_UPLOAD_REQUEST / SCREENSHOT_REQUEST commands
a real byte-transport channel, which previously did not exist - results could
only travel inside the JSON `output` field of a command_result.

Auth: both the device (via X-API-Key) and the owner (via user JWT) can call
these, exactly like /devices/heartbeat and /commands/pending. Direction and
uploader identity are derived from *which* auth path was used, not from a
client-supplied field, so a caller cannot spoof who uploaded a file.
"""

from __future__ import annotations

from flask import Blueprint, g, request, send_file

from app.extensions import db
from app.models import Command, Device
from app.security.device_auth import device_auth_required
from app.services.file_service import (
    FileTooLargeError,
    delete_command_file,
    get_command_file,
    list_command_files,
    resolve_file_path,
    save_command_file,
)
from app.utils.responses import error_response, success_response


files_bp = Blueprint("files", __name__)


def _file_to_dict(command_file) -> dict:
    return {
        "id": command_file.id,
        "command_id": command_file.command_id,
        "direction": command_file.direction,
        "original_filename": command_file.original_filename,
        "content_type": command_file.content_type,
        "size_bytes": command_file.size_bytes,
        "checksum_sha256": command_file.checksum_sha256,
        "uploaded_by": command_file.uploaded_by,
        "created_at": command_file.created_at.isoformat(),
    }


def _authorize_command(command_id: str):
    """Return (command, device) if the caller may act on this command, else None."""

    command = db.session.get(Command, command_id)
    if not command:
        return None
    device = db.session.get(Device, command.device_id)
    if not device:
        return None

    if g.current_device is not None:
        if device.id != g.current_device.id:
            return None
    else:
        if device.owner_id != str(g.current_user.id):
            return None
    return command, device


@files_bp.post("/commands/<string:command_id>/files")
@device_auth_required
def upload_command_file_route(command_id: str):
    authorized = _authorize_command(command_id)
    if not authorized:
        return error_response("Command not found", status_code=404)
    command, device = authorized

    if "file" not in request.files:
        return error_response("Multipart field 'file' is required", status_code=400)
    upload = request.files["file"]
    if not upload.filename:
        return error_response("Uploaded file has no filename", status_code=400)

    if g.current_device is not None:
        direction, uploaded_by = "device_to_owner", "device"
    else:
        direction, uploaded_by = "owner_to_device", "owner"

    try:
        record = save_command_file(
            command=command,
            device_id=device.id,
            direction=direction,
            uploaded_by=uploaded_by,
            filename=upload.filename,
            content_type=upload.content_type,
            stream=upload.stream,
        )
    except FileTooLargeError as error:
        return error_response(str(error), status_code=413)
    except ValueError as error:
        return error_response(str(error), status_code=400)

    return success_response("File uploaded", _file_to_dict(record), 201)


@files_bp.get("/commands/<string:command_id>/files")
@device_auth_required
def list_command_files_route(command_id: str):
    authorized = _authorize_command(command_id)
    if not authorized:
        return error_response("Command not found", status_code=404)
    command, _device = authorized

    files = list_command_files(command.id)
    return success_response("Command files retrieved", [_file_to_dict(f) for f in files])


@files_bp.get("/commands/<string:command_id>/files/<string:file_id>/download")
@device_auth_required
def download_command_file_route(command_id: str, file_id: str):
    authorized = _authorize_command(command_id)
    if not authorized:
        return error_response("Command not found", status_code=404)
    command, _device = authorized

    command_file = get_command_file(file_id)
    if not command_file or command_file.command_id != command.id:
        return error_response("File not found", status_code=404)

    # A device may only download files staged *for* it (owner_to_device), never
    # files it uploaded itself; an owner may download either direction.
    if g.current_device is not None and command_file.direction != "owner_to_device":
        return error_response("File not found", status_code=404)

    path = resolve_file_path(command_file)
    if not path.exists():
        return error_response("File no longer available", status_code=410)

    return send_file(
        path,
        mimetype=command_file.content_type or "application/octet-stream",
        as_attachment=True,
        download_name=command_file.original_filename,
    )


@files_bp.delete("/commands/<string:command_id>/files/<string:file_id>")
@device_auth_required
def delete_command_file_route(command_id: str, file_id: str):
    authorized = _authorize_command(command_id)
    if not authorized:
        return error_response("Command not found", status_code=404)
    command, _device = authorized

    command_file = get_command_file(file_id)
    if not command_file or command_file.command_id != command.id:
        return error_response("File not found", status_code=404)

    delete_command_file(command_file)
    return success_response("File deleted")
