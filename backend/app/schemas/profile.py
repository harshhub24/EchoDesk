"""Profile schemas."""

from __future__ import annotations

from pydantic import Field

from .common import ApiSchema


class ProfileUpdateRequest(ApiSchema):
    full_name: str = Field(min_length=1, max_length=255)


class ProfileResponse(ApiSchema):
    id: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
