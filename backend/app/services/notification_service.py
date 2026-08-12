"""Notification operations."""

from __future__ import annotations

from app.extensions import db
from app.models import Notification, User
from app.utils.time import utcnow


def create_notification(user: User, title: str, message: str, category: str, details: dict | None = None) -> Notification:
    notification = Notification(user_id=user.id, title=title, message=message, category=category, details=details or {})
    db.session.add(notification)
    db.session.commit()
    return notification


def list_notifications(user_id: str) -> list[Notification]:
    return Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()


def mark_notification_read(notification: Notification) -> Notification:
    notification.is_read = True
    notification.read_at = utcnow()
    db.session.commit()
    return notification

