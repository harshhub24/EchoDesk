"""Security header middleware registration."""

from __future__ import annotations

from flask import Flask

from app.middleware.request_logging import apply_security_headers


def register_security_headers(app: Flask) -> None:
    """Attach security headers to every response."""

    app.after_request(apply_security_headers)
