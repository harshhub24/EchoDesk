"""Centralized application error handlers."""

from __future__ import annotations

from typing import Any

from flask import Flask, request
from flask_jwt_extended.exceptions import JWTExtendedException
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.utils.responses import error_response


def register_error_handlers(app: Flask) -> None:
    """Register global JSON error handlers."""

    @app.errorhandler(400)
    def bad_request(error: Any):
        return error_response("Bad request", {"detail": str(error)}, 400)

    @app.errorhandler(401)
    def unauthorized(error: Any):
        return error_response("Unauthorized", {"detail": str(error)}, 401)

    @app.errorhandler(403)
    def forbidden(error: Any):
        return error_response("Forbidden", {"detail": str(error)}, 403)

    @app.errorhandler(404)
    def not_found(error: Any):
        return error_response("Resource not found", {"detail": str(error)}, 404)

    @app.errorhandler(409)
    def conflict(error: Any):
        return error_response("Conflict", {"detail": str(error)}, 409)

    @app.errorhandler(422)
    def unprocessable(error: Any):
        return error_response("Validation failed", {"detail": str(error)}, 422)

    @app.errorhandler(500)
    def internal_error(error: Any):
        return error_response("Internal server error", {"detail": str(error)}, 500)

    @app.errorhandler(ValidationError)
    def pydantic_validation_error(error: ValidationError):
        return error_response("Validation failed", error.errors(), 422)

    @app.errorhandler(SQLAlchemyError)
    def database_error(error: SQLAlchemyError):
        app.logger.exception("Database error during %s %s", request.method, request.path)
        return error_response("Database error", {"detail": "A database error occurred"}, 500)

    @app.errorhandler(JWTExtendedException)
    def jwt_error(error: JWTExtendedException):
        return error_response("Authentication token error", {"detail": str(error)}, 401)
