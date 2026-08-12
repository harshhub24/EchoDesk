"""Shared schema utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApiSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class MessageSchema(ApiSchema):
    message: str


class PaginationSchema(ApiSchema):
    items: list[Any] = Field(default_factory=list)
    page: int
    per_page: int
    total: int


class TimestampSchema(ApiSchema):
    created_at: datetime
    updated_at: datetime
