"""Notification schemas."""

from __future__ import annotations

from .common import ApiSchema


class NotificationResponse(ApiSchema):
    id: str
    title: str
    message: str
    category: str
    is_read: bool
