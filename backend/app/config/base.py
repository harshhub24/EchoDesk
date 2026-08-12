"""Base configuration shared by all environments."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path


class BaseConfig:
    """Common configuration values."""

    BASE_DIR = Path(__file__).resolve().parents[2]
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-change-me-change-me-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///echodesk.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES", "15"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("REFRESH_TOKEN_EXPIRES_DAYS", "30"))
    )
    CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",") if origin.strip()]
    SOCKETIO_CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("SOCKETIO_CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]
    RATELIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "200 per hour")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    DOWNLOAD_FOLDER = str(BASE_DIR / "downloads")
    TEMP_FOLDER = str(BASE_DIR / "temp")
    LOG_FOLDER = str(BASE_DIR / "logs")
    API_TITLE = "EchoDesk API"
    API_VERSION = "v1"
    API_PREFIX = "/api/v1"
    HEALTHCHECK_ENDPOINT = "/api/v1/health"
