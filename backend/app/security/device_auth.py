"""Device-facing authentication.

Adds a device API key path (header: X-API-Key: <prefix>.<secret>) alongside the
existing user JWT path, so an unattended Agent process does not need to hold the
owning user's password or refresh token. Nothing about the existing JWT path is
changed - routes decorated with @device_auth_required still work exactly as
before for callers sending a Bearer access token, and gain the new header as an
additional, optional way in.

Resolution result is stashed on flask.g for the view to use:
  g.current_user   -> the owning User (set on both paths)
  g.current_device -> the Device the key is scoped to (API key path only, else None)
"""

from __future__ import annotations

from functools import wraps

from flask import g, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.extensions import db
from app.models import ApiKey, Device, User
from app.security.api_keys import parse_api_key
from app.security.passwords import verify_password
from app.utils.responses import error_response
from app.utils.time import utcnow


def authenticate_device_api_key(raw_key: str) -> tuple[User, Device] | None:
    """Validate a raw 'prefix.secret' API key and return (user, device) or None."""

    parsed = parse_api_key(raw_key)
    if not parsed:
        return None
    key_prefix, secret = parsed

    api_key = ApiKey.query.filter_by(key_prefix=key_prefix, is_active=True).first()
    if not api_key or not api_key.device_id:
        return None
    if api_key.expires_at and api_key.expires_at < utcnow():
        return None
    if not verify_password(secret, api_key.hashed_secret):
        return None

    device = db.session.get(Device, api_key.device_id)
    if not device or not device.is_registered:
        return None
    user = db.session.get(User, api_key.user_id)
    if not user or not user.is_active:
        return None

    api_key.last_used_at = utcnow()
    db.session.commit()
    return user, device


def device_auth_required(view):
    """Accept either a device API key (X-API-Key) or a user access JWT (Bearer)."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        raw_key = request.headers.get("X-API-Key")
        if raw_key:
            resolved = authenticate_device_api_key(raw_key)
            if not resolved:
                return error_response("Invalid or expired API key", status_code=401)
            g.current_user, g.current_device = resolved
            return view(*args, **kwargs)

        verify_jwt_in_request()
        user = db.session.get(User, get_jwt_identity())
        if not user:
            return error_response("User not found", status_code=404)
        g.current_user, g.current_device = user, None
        return view(*args, **kwargs)

    return wrapper
