"""Command schemas."""

from __future__ import annotations

from pydantic import Field

from app.constants import COMMAND_TYPES

from .common import ApiSchema


class CommandCreateRequest(ApiSchema):
    device_id: str = Field(min_length=1, max_length=36)
    command_type: str = Field(min_length=1, max_length=64)
    payload: dict = Field(default_factory=dict)

    @classmethod
    def validate_command_type(cls, value: str) -> str:
        if value not in COMMAND_TYPES:
            raise ValueError("Unsupported command type")
        return value


class CommandResultRequest(ApiSchema):
    command_id: str = Field(min_length=1, max_length=36)
    execution_status: str = Field(min_length=1, max_length=32)
    output: dict = Field(default_factory=dict)
    raw_payload: dict = Field(default_factory=dict)


class CommandResponse(ApiSchema):
    id: str
    device_id: str
    created_by_id: str
    command_type: str
    payload: dict
    status: str
