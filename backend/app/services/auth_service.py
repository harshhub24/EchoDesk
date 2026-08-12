"""Authentication and session management services."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from flask_jwt_extended import decode_token, get_jti

from app.constants import DeviceStatus
from app.extensions import db
from app.models import DeviceSession, RefreshToken, User, UserSetting
from app.security.passwords import hash_password, verify_password
from app.security.tokens import build_token_pair
from app.utils.time import utcnow


def create_user(email: str, password: str, full_name: str) -> User:
    existing_user = User.query.filter_by(email=email.lower()).first()
    if existing_user:
        raise ValueError("An account with this email already exists")

    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        full_name=full_name,
        is_active=True,
        is_verified=False,
    )
    settings = UserSetting(user=user)
    db.session.add(user)
    db.session.add(settings)
    db.session.commit()
    return user


def authenticate_user(email: str, password: str) -> User:
    user = User.query.filter_by(email=email.lower()).first()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    if not user.is_active:
        raise ValueError("User account is disabled")
    user.last_login_at = utcnow()
    db.session.commit()
    return user


def issue_tokens_for_user(user: User) -> dict[str, str]:
    return build_token_pair(str(user.id), {"email": user.email, "full_name": user.full_name})


def revoke_refresh_token_from_jti(jti: str) -> RefreshToken | None:
    token = RefreshToken.query.filter_by(jti=jti).first()
    if token and not token.is_revoked:
        token.is_revoked = True
        token.revoked_at = utcnow()
        db.session.commit()
    return token


def is_refresh_token_revoked(jti: str) -> bool:
    token = RefreshToken.query.filter_by(jti=jti).first()
    return bool(token and token.is_revoked)


def store_refresh_token(user_id: str, refresh_token: str, device_session_id: str | None = None) -> RefreshToken:
    token_data = decode_token(refresh_token)
    refresh_row = RefreshToken(
        user_id=user_id,
        jti=get_jti(refresh_token),
        token_type=token_data.get("type", "refresh"),
        expires_at=datetime.fromtimestamp(token_data["exp"], tz=utcnow().tzinfo),
        device_session_id=device_session_id,
    )
    db.session.add(refresh_row)
    db.session.commit()
    return refresh_row


def revoke_user_sessions(user_id: str) -> int:
    sessions = DeviceSession.query.filter_by(user_id=user_id, is_active=True).all()
    for session in sessions:
        session.is_active = False
        session.disconnected_at = utcnow()
        if session.device:
            session.device.status = DeviceStatus.OFFLINE.value
    db.session.commit()
    return len(sessions)

