"""Validates an incoming command dict before dispatch.

Kept intentionally permissive on payload contents (the backend's `payload`
column is a free-form JSON blob with no server-side schema) but strict about
the envelope shape and the command_type being one we actually know about.
"""

from __future__ import annotations

import datetime

from agent.constants import KNOWN_COMMAND_TYPES, CommandType


class InvalidCommandError(ValueError):
    pass


_REQUIRED_PAYLOAD_KEYS: dict[str, tuple[str, ...]] = {
    CommandType.MESSAGE_REQUEST.value: ("message",),
    CommandType.FILE_LIST_REQUEST.value: (),  # path optional, defaults to "."
    CommandType.FILE_DOWNLOAD_REQUEST.value: ("path",),
    CommandType.FILE_UPLOAD_REQUEST.value: (),  # destination_path or path
    CommandType.DELETE_FILE_REQUEST.value: ("path",),
}


def validate_envelope(command: dict) -> None:
    for key in ("id", "command_type"):
        if key not in command:
            raise InvalidCommandError(f"Command is missing required field '{key}': {command}")

    command_type = command["command_type"]
    if command_type not in KNOWN_COMMAND_TYPES:
        raise InvalidCommandError(f"Unknown command_type '{command_type}'")


def validate_payload(command_type: str, payload: dict) -> None:
    required_keys = _REQUIRED_PAYLOAD_KEYS.get(command_type, ())
    missing = [key for key in required_keys if key not in payload]
    if missing:
        raise InvalidCommandError(f"{command_type} payload missing required key(s): {missing}")

    if command_type == CommandType.FILE_UPLOAD_REQUEST.value and not (payload.get("destination_path") or payload.get("path")):
        raise InvalidCommandError("FILE_UPLOAD_REQUEST payload requires 'destination_path' (or 'path')")


def is_expired(expires_at: str | None) -> bool:
    """The backend does not automatically flip expired commands to status
    'expired' (see backend docs/API_REFERENCE.md notes), so the Agent must
    check this itself before executing anything.
    """

    if not expires_at:
        return False
    try:
        expiry = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return False

    # The backend stores/serializes naive UTC datetimes (no offset suffix) -
    # treat a naive value as UTC rather than crashing on the aware/naive
    # comparison below.
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=datetime.timezone.utc)

    now = datetime.datetime.now(datetime.timezone.utc)
    return now > expiry
