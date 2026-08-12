"""Standard JSON response helpers."""

from __future__ import annotations

from typing import Any

from flask import jsonify


def success_response(message: str, data: Any = None, status_code: int = 200):
    payload = {"success": True, "message": message, "data": data if data is not None else {}}
    return jsonify(payload), status_code


def error_response(message: str, error: Any = None, status_code: int = 400):
    payload = {"success": False, "message": message, "error": error if error is not None else {}}
    return jsonify(payload), status_code
