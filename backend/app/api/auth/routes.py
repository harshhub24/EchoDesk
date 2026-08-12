"""Authentication routes."""

from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.extensions import db, jwt, limiter
from app.middleware.request_logging import log_activity
from app.models import RefreshToken, User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LogoutRequest, SignupRequest
from app.security.passwords import hash_password, verify_password
from app.services.auth_service import (
    authenticate_user,
    create_user,
    issue_tokens_for_user,
    is_refresh_token_revoked,
    revoke_refresh_token_from_jti,
    revoke_user_sessions,
    store_refresh_token,
)
from app.utils.responses import error_response, success_response
from app.utils.time import utcnow
from app.extensions import db


auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/signup")
@limiter.limit("10 per minute")
def signup():
    payload = SignupRequest.model_validate(request.get_json(force=True)).model_dump()
    user = create_user(**payload)
    tokens = issue_tokens_for_user(user)
    store_refresh_token(user.id, tokens["refresh_token"])
    log_activity(user.id, "signup", "authentication", "User signed up", {"email": user.email})
    return success_response("Signup successful", {"user_id": user.id, **tokens}, 201)


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    payload = LoginRequest.model_validate(request.get_json(force=True)).model_dump()
    user = authenticate_user(**payload)
    tokens = issue_tokens_for_user(user)
    store_refresh_token(user.id, tokens["refresh_token"])
    log_activity(user.id, "login", "authentication", "User logged in", {"email": user.email})
    return success_response("Login successful", {"user_id": user.id, **tokens})


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = get_jwt()
    user = db.session.get(User, identity)
    if not user:
        return error_response("User not found", status_code=404)
    token_row = RefreshToken.query.filter_by(jti=claims["jti"]).first()
    if token_row and token_row.is_revoked:
        return error_response("Refresh token has been revoked", status_code=401)
    if token_row:
        revoke_refresh_token_from_jti(token_row.jti)
    tokens = issue_tokens_for_user(user)
    store_refresh_token(user.id, tokens["refresh_token"])
    return success_response("Token refreshed", tokens)


@auth_bp.post("/logout")
@jwt_required(optional=True)
def logout():
    request_data = request.get_json(silent=True) or {}
    try:
        payload = LogoutRequest.model_validate(request_data)
    except Exception:
        payload = LogoutRequest()

    jwt_payload = get_jwt() if get_jwt_identity() else {}
    current_jti = jwt_payload.get("jti")
    if payload.refresh_token:
        from flask_jwt_extended import decode_token

        decoded = decode_token(payload.refresh_token)
        revoke_refresh_token_from_jti(decoded["jti"])
    elif current_jti:
        revoke_refresh_token_from_jti(current_jti)

    identity = get_jwt_identity()
    if identity:
        revoke_user_sessions(str(identity))
        log_activity(str(identity), "logout", "authentication", "User logged out")
    return success_response("Logged out successfully")


@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    payload = ChangePasswordRequest.model_validate(request.get_json(force=True)).model_dump()
    user = db.session.get(User, get_jwt_identity())
    if not user or not verify_password(payload["current_password"], user.password_hash):
        return error_response("Current password is invalid", status_code=400)
    user.password_hash = hash_password(payload["new_password"])
    db.session.commit()
    log_activity(user.id, "password_change", "authentication", "Password changed")
    return success_response("Password updated")


@jwt.token_in_blocklist_loader
def is_token_revoked(jwt_header: dict, jwt_payload: dict) -> bool:
    if jwt_payload.get("type") != "refresh":
        return False
    return is_refresh_token_revoked(jwt_payload["jti"])

