"""Activity log + Notification models - mirror backend response shapes
exactly (see docs/PHASE_1_ANALYSIS.md §6).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ActivityEntry:
    id: str
    activity_type: str
    category: str
    message: str
    details: dict
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "ActivityEntry":
        return cls(
            id=data["id"],
            activity_type=data.get("activity_type", ""),
            category=data.get("category", ""),
            message=data.get("message", ""),
            details=data.get("details") or {},
            created_at=data.get("created_at", ""),
        )


@dataclass
class Notification:
    id: str
    title: str
    message: str
    category: str
    is_read: bool
    details: dict
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "Notification":
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            message=data.get("message", ""),
            category=data.get("category", "general"),
            is_read=bool(data.get("is_read", False)),
            details=data.get("details") or {},
            created_at=data.get("created_at", ""),
        )
