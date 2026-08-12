"""Flask application factory."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify
from dotenv import load_dotenv

from app.api.auth import auth_bp
from app.api.activity import activity_bp
from app.api.commands import commands_bp
from app.api.devices import devices_bp
from app.api.files import files_bp
from app.api.health import health_bp
from app.api.notifications import notifications_bp
from app.api.profile import profile_bp
from app.api.websocket.routes import websocket_bp
from app.config import DevelopmentConfig, ProductionConfig, TestingConfig
from app.extensions import cors, db, jwt, limiter, migrate, socketio
from app.middleware.error_handlers import register_error_handlers
from app.middleware.request_logging import register_request_logging
from app.middleware.security_headers import register_security_headers
from app.sockets.events import register_socket_events


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def _load_config_name() -> str:
    return os.getenv("FLASK_ENV", "development").lower()


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application."""

    load_dotenv()
    app = Flask(__name__)
    config_key = (config_name or _load_config_name()).lower()
    app.config.from_object(CONFIG_MAP.get(config_key, DevelopmentConfig))

    for folder_name in ["UPLOAD_FOLDER", "DOWNLOAD_FOLDER", "TEMP_FOLDER", "LOG_FOLDER"]:
        Path(app.config[folder_name]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config.get("CORS_ORIGINS", ["*"]))
    limiter.init_app(app)
    limiter.default_limits = [app.config.get("RATELIMIT_DEFAULT", "200 per hour")]
    socketio.init_app(app, cors_allowed_origins=app.config.get("SOCKETIO_CORS_ORIGINS", ["*"]))

    register_error_handlers(app)
    register_request_logging(app)
    register_security_headers(app)
    register_socket_events()

    app.register_blueprint(auth_bp, url_prefix=app.config["API_PREFIX"])
    app.register_blueprint(profile_bp, url_prefix=app.config["API_PREFIX"])
    app.register_blueprint(devices_bp, url_prefix=app.config["API_PREFIX"])
    app.register_blueprint(commands_bp, url_prefix=app.config["API_PREFIX"])
    app.register_blueprint(files_bp, url_prefix=app.config["API_PREFIX"])
    app.register_blueprint(activity_bp, url_prefix=app.config["API_PREFIX"])
    app.register_blueprint(notifications_bp, url_prefix=app.config["API_PREFIX"])
    app.register_blueprint(websocket_bp, url_prefix=app.config["API_PREFIX"])
    app.register_blueprint(health_bp, url_prefix=app.config["API_PREFIX"])

    @app.get("/")
    def index():
        return jsonify({"success": True, "message": "EchoDesk backend is running"})

    return app

