"""Command + CommandFile models - mirror backend response shapes exactly
(see docs/PHASE_1_ANALYSIS.md §3-4). Note: the backend's GET /commands
response has NO execution-result fields (no `output`/`execution_status`) -
this dataclass intentionally does not have them either, so nothing pretends
to have data the API doesn't provide.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Command:
    id: str
    device_id: str
    created_by_id: str
    command_type: str
    payload: dict
    status: str
    created_at: str | None = None
    expires_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Command":
        return cls(
            id=data["id"],
            device_id=data["device_id"],
            created_by_id=data.get("created_by_id", ""),
            command_type=data["command_type"],
            payload=data.get("payload") or {},
            status=data.get("status", "pending"),
            created_at=data.get("created_at"),
            expires_at=data.get("expires_at"),
        )


@dataclass
class CommandFile:
    id: str
    command_id: str
    direction: str  # "device_to_owner" | "owner_to_device"
    original_filename: str
    content_type: str | None
    size_bytes: int
    checksum_sha256: str | None
    uploaded_by: str  # "device" | "owner"
    created_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "CommandFile":
        return cls(
            id=data["id"],
            command_id=data["command_id"],
            direction=data["direction"],
            original_filename=data.get("original_filename", "file.bin"),
            content_type=data.get("content_type"),
            size_bytes=data.get("size_bytes", 0),
            checksum_sha256=data.get("checksum_sha256"),
            uploaded_by=data.get("uploaded_by", "device"),
            created_at=data.get("created_at"),
        )
