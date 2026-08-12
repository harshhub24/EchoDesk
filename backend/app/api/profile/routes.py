"""Profile routes."""

from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import User
from app.schemas.profile import ProfileUpdateRequest
from app.services.profile_service import get_profile, update_profile
from app.utils.responses import error_response, success_response


profile_bp = Blueprint("profile", __name__)


@profile_bp.get("/profile")
@jwt_required()
def profile_detail():
    user = db.session.get(User, get_jwt_identity())
    if not user:
        return error_response("User not found", status_code=404)
    profile = get_profile(user)
    return success_response(
        "Profile retrieved",
        {
            "id": profile.id,
            "email": profile.email,
            "full_name": profile.full_name,
            "is_active": profile.is_active,
            "is_verified": profile.is_verified,
        },
    )


@profile_bp.put("/profile")
@jwt_required()
def profile_update():
    user = db.session.get(User, get_jwt_identity())
    if not user:
        return error_response("User not found", status_code=404)
    payload = ProfileUpdateRequest.model_validate(request.get_json(force=True)).model_dump()
    updated_user = update_profile(user, payload["full_name"])
    return success_response(
        "Profile updated",
        {"id": updated_user.id, "email": updated_user.email, "full_name": updated_user.full_name},
    )

