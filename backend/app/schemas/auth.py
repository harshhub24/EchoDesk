"""Authentication schemas."""

from __future__ import annotations

from pydantic import Field, field_validator

from .common import ApiSchema


class SignupRequest(ApiSchema):
    email: str
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or value.count("@") != 1:
            raise ValueError("Invalid email address")
        return value.strip().lower()


class LoginRequest(ApiSchema):
    email: str
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or value.count("@") != 1:
            raise ValueError("Invalid email address")
        return value.strip().lower()


class RefreshRequest(ApiSchema):
    refresh_token: str


class LogoutRequest(ApiSchema):
    refresh_token: str | None = None


class ChangePasswordRequest(ApiSchema):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
