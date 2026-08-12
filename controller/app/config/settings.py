"""Controller configuration, loaded from environment variables / a `.env`
file next to the executable (same convention as the Agent). See
.env.example for every supported variable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

_APP_DIR = Path(__file__).resolve().parent.parent  # .../controller/app/config -> .../controller
_ENV_FILE = _APP_DIR / ".env"

if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE)
else:
    load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass
class AppConfig:
    backend_url: str = field(default_factory=lambda: os.getenv("ECHODESK_BACKEND_URL", "http://localhost:5000").rstrip("/"))
    api_prefix: str = field(default_factory=lambda: os.getenv("ECHODESK_API_PREFIX", "/api/v1"))
    verify_tls: bool = field(default_factory=lambda: _env_bool("ECHODESK_VERIFY_TLS", True))

    rest_timeout_seconds: int = field(default_factory=lambda: _env_int("ECHODESK_REST_TIMEOUT", 15))
    device_poll_interval_seconds: int = field(default_factory=lambda: _env_int("ECHODESK_DEVICE_POLL_INTERVAL", 30))
    command_poll_interval_seconds: int = field(default_factory=lambda: _env_int("ECHODESK_COMMAND_POLL_INTERVAL", 5))

    data_dir: Path = field(default_factory=lambda: Path(os.getenv("ECHODESK_DATA_DIR", str(_APP_DIR))))
    log_dir: Path = field(default_factory=lambda: Path(os.getenv("ECHODESK_LOG_DIR", str(_APP_DIR / "logs"))))
    log_level: str = field(default_factory=lambda: os.getenv("ECHODESK_LOG_LEVEL", "INFO"))

    remember_login_default: bool = field(default_factory=lambda: _env_bool("ECHODESK_REMEMBER_LOGIN_DEFAULT", True))
    theme: str = field(default_factory=lambda: os.getenv("ECHODESK_THEME", "dark"))

    @property
    def api_base_url(self) -> str:
        return f"{self.backend_url}{self.api_prefix}"

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


def load_config() -> AppConfig:
    return AppConfig()
