"""Activity routes."""

from __future__ import annotations

from flask import Blueprint
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.activity_service import list_activity_for_user
from app.utils.responses import success_response


activity_bp = Blueprint("activity", __name__)


@activity_bp.get("/activity")
@jwt_required()
def activity_list():
    user_id = str(get_jwt_identity())
    activities = list_activity_for_user(user_id)
    return success_response(
        "Activity retrieved",
        [
            {
                "id": activity.id,
                "activity_type": activity.activity_type,
                "category": activity.category,
                "message": activity.message,
                "details": activity.details,
                "created_at": activity.created_at.isoformat(),
            }
            for activity in activities
        ],
    )
