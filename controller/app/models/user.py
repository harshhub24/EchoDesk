"""Session/user model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Session:
    user_id: str
    access_token: str
    refresh_token: str
    email: str | None = None
    full_name: str | None = None
