"""Activity schemas."""

from __future__ import annotations

from .common import ApiSchema


class ActivityResponse(ApiSchema):
    id: str
    activity_type: str
    category: str
    message: str
    metadata: dict
