"""User profile operations."""

from __future__ import annotations

from app.extensions import db
from app.models import User


def get_profile(user: User) -> User:
    return user


def update_profile(user: User, full_name: str) -> User:
    user.full_name = full_name
    db.session.commit()
    return user

