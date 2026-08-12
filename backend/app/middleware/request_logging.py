"""Request and security logging helpers."""

from __future__ import annotations

from flask import Flask, g, request

from app.extensions import db
from app.models.activity_log import ActivityLog
from app.utils.time import utcnow


def register_request_logging(app: Flask) -> None:
    """Attach lightweight request logging hooks."""

    @app.before_request
    def start_timer() -> None:
        g.request_started_at = utcnow()

    @app.after_request
    def log_request(response):
        if request.path.startswith("/api/"):
            app.logger.info("%s %s %s", request.method, request.path, response.status_code)
        return response


def apply_security_headers(response):
    """Attach a conservative set of security headers."""

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    return response


def log_activity(
    user_id: str | None,
    activity_type: str,
    category: str,
    message: str,
    details: dict | None = None,
    device_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ActivityLog:
    """Persist an audit log entry."""

    entry = ActivityLog(
        user_id=user_id,
        device_id=device_id,
        activity_type=activity_type,
        category=category,
        message=message,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.session.add(entry)
    return entry
