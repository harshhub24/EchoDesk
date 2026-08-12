"""DELETE_FILE_REQUEST handler."""

from __future__ import annotations

import logging
import shutil

from agent.files.browser import resolve_safe_path

logger = logging.getLogger("agent.files.delete")


def execute(file_root: str | None, payload: dict) -> dict:
    requested_path = payload.get("path")
    if not requested_path:
        raise ValueError("payload.path is required for DELETE_FILE_REQUEST")

    target = resolve_safe_path(file_root, requested_path)
    if not target.exists():
        raise FileNotFoundError(f"Path not found: {target}")

    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()

    logger.info("Deleted %s", target)
    return {"action": "delete_file", "deleted_path": str(target)}
