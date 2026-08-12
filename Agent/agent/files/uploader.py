"""FILE_UPLOAD_REQUEST handler.

Named `uploader` to match the owner's perspective (they are uploading a file
*to* the device). The Agent's job is to fetch the bytes the owner already
attached to this command (direction=owner_to_device) and write them to the
requested local destination.
"""

from __future__ import annotations

import logging

from agent.api import endpoints
from agent.api.client import RestClient
from agent.files.browser import resolve_safe_path

logger = logging.getLogger("agent.files.uploader")


def execute(client: RestClient, command_id: str, file_root: str | None, payload: dict) -> dict:
    destination = payload.get("destination_path") or payload.get("path")
    if not destination:
        raise ValueError("payload.destination_path is required for FILE_UPLOAD_REQUEST")

    files = endpoints.list_command_files(client, command_id)
    staged = [f for f in files if f.get("direction") == "owner_to_device"]
    if not staged:
        raise FileNotFoundError(f"No file has been attached to command {command_id} by the owner yet")

    # Most recently attached wins if there's more than one.
    file_meta = sorted(staged, key=lambda f: f.get("created_at", ""))[-1]
    content = endpoints.download_command_file(client, command_id, file_meta["id"])

    target = resolve_safe_path(file_root, destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)

    logger.info("Wrote %s (%d bytes) from command %s", target, len(content), command_id)
    return {
        "action": "file_upload",
        "written_to": str(target),
        "size_bytes": len(content),
        "source_file_id": file_meta["id"],
    }
