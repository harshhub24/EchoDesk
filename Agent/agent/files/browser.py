"""Directory browsing (FILE_LIST_REQUEST) + the shared path-safety helper
used by every other module in this package.
"""

from __future__ import annotations

import datetime
import logging
from pathlib import Path

logger = logging.getLogger("agent.files.browser")


def resolve_safe_path(root: str | None, requested_path: str) -> Path:
    """Resolve `requested_path` to an absolute Path, enforcing that it stays
    inside `root` when a root is configured (ECHODESK_FILE_ROOT).

    Raises PermissionError if the resolved path would escape the configured
    root (e.g. via "../../etc/passwd").
    """

    if not requested_path:
        raise ValueError("path is required")

    candidate = Path(requested_path).expanduser()
    if root:
        root_resolved = Path(root).expanduser().resolve()
        target = (root_resolved / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
        if target != root_resolved and root_resolved not in target.parents:
            raise PermissionError(f"'{requested_path}' resolves outside the allowed root")
        return target

    return candidate.resolve()


def _entry_metadata(path: Path) -> dict:
    try:
        stat_result = path.stat()
        modified_at = datetime.datetime.fromtimestamp(stat_result.st_mtime, tz=datetime.timezone.utc).isoformat()
        size_bytes = stat_result.st_size if path.is_file() else None
    except OSError:
        modified_at = None
        size_bytes = None

    return {
        "name": path.name,
        "path": str(path),
        "is_directory": path.is_dir(),
        "size_bytes": size_bytes,
        "modified_at": modified_at,
    }


def list_directory(root: str | None, requested_path: str) -> dict:
    target = resolve_safe_path(root, requested_path or ".")
    if not target.exists():
        raise FileNotFoundError(f"Path not found: {target}")
    if not target.is_dir():
        raise NotADirectoryError(f"Not a directory: {target}")

    entries = []
    for child in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        try:
            entries.append(_entry_metadata(child))
        except OSError as error:
            logger.warning("Skipping unreadable entry %s: %s", child, error)

    return {"path": str(target), "entries": entries}
