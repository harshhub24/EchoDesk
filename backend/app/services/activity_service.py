"""Activity log helpers."""

from __future__ import annotations

from app.extensions import db
from app.models import ActivityLog


def create_activity_log(**kwargs) -> ActivityLog:
    log_entry = ActivityLog(**kwargs)
    db.session.add(log_entry)
    db.session.commit()
    return log_entry


def list_activity_for_user(user_id: str) -> list[ActivityLog]:
    return ActivityLog.query.filter_by(user_id=user_id).order_by(ActivityLog.created_at.desc()).all()

