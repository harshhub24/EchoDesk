"""FILE_DOWNLOAD_REQUEST handler.

Named `downloader` to match the owner's perspective (they are downloading a
file *from* the device) even though, mechanically, the Agent's job here is
to *upload* the bytes to the backend so the owner's client can then GET them.
"""

from __future__ import annotations

import logging
import mimetypes

from agent.api import endpoints
from agent.api.client import RestClient
from agent.constants import MAX_TRANSFERABLE_FILE_SIZE_BYTES
from agent.files.browser import resolve_safe_path

logger = logging.getLogger("agent.files.downloader")


def execute(client: RestClient, command_id: str, file_root: str | None, payload: dict) -> dict:
    requested_path = payload.get("path")
    if not requested_path:
        raise ValueError("payload.path is required for FILE_DOWNLOAD_REQUEST")

    target = resolve_safe_path(file_root, requested_path)
    if not target.is_file():
        raise FileNotFoundError(f"File not found: {target}")

    size_bytes = target.stat().st_size
    if size_bytes > MAX_TRANSFERABLE_FILE_SIZE_BYTES:
        raise ValueError(
            f"File is {size_bytes} bytes, exceeds the {MAX_TRANSFERABLE_FILE_SIZE_BYTES}-byte transfer limit"
        )

    content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    content = target.read_bytes()

    logger.info("Uploading %s (%d bytes) for command %s", target, size_bytes, command_id)
    response = endpoints.upload_command_file(client, command_id, target.name, content, content_type)
    file_meta = response.get("data", {})

    return {
        "action": "file_download",
        "source_path": str(target),
        "filename": target.name,
        "size_bytes": size_bytes,
        "file_id": file_meta.get("id"),
    }
