"""Notification routes."""

from __future__ import annotations

from flask import Blueprint
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.notification_service import list_notifications
from app.utils.responses import success_response


notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("/notifications")
@jwt_required()
def notifications_list():
    user_id = str(get_jwt_identity())
    notifications = list_notifications(user_id)
    return success_response(
        "Notifications retrieved",
        [
            {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "category": notification.category,
                "is_read": notification.is_read,
                "details": notification.details,
                "created_at": notification.created_at.isoformat(),
            }
            for notification in notifications
        ],
    )
