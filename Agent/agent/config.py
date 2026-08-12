"""Agent configuration.

Loaded from environment variables (and a `.env` file next to the installed
agent, if present, via python-dotenv). See `.env.example` for every supported
variable.

Two ways to authenticate, exactly matching the backend's device-auth options:

1. Pre-provisioned device API key (recommended for production):
   set ECHODESK_API_KEY to a key minted by the owner via
   `POST /devices/{id}/api-key` on the backend. The Agent never needs the
   user's password.

2. One-time bootstrap credentials (first run only):
   set ECHODESK_EMAIL + ECHODESK_PASSWORD. On first run the Agent logs in,
   registers the device, mints its own device API key, and persists that key
   to a local secrets file (see api/auth.py). After that, ECHODESK_API_KEY
   (loaded from the secrets file, not necessarily the .env) is used for every
   subsequent run - the password is only ever used once, in memory, and is
   never written to disk by the Agent itself. You should remove
   ECHODESK_EMAIL/ECHODESK_PASSWORD from .env after the first successful run.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

_AGENT_DIR = Path(__file__).resolve().parent
_ENV_FILE = _AGENT_DIR / ".env"

if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE)
else:
    # Also allow a .env in the current working directory (e.g. project root)
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


@dataclass(frozen=True)
class AgentConfig:
    # --- Backend connection ---
    backend_url: str = field(default_factory=lambda: os.getenv("ECHODESK_BACKEND_URL", "http://localhost:5000").rstrip("/"))
    api_prefix: str = field(default_factory=lambda: os.getenv("ECHODESK_API_PREFIX", "/api/v1"))
    verify_tls: bool = field(default_factory=lambda: _env_bool("ECHODESK_VERIFY_TLS", True))

    # --- Auth ---
    api_key: str | None = field(default_factory=lambda: os.getenv("ECHODESK_API_KEY") or None)
    bootstrap_email: str | None = field(default_factory=lambda: os.getenv("ECHODESK_EMAIL") or None)
    bootstrap_password: str | None = field(default_factory=lambda: os.getenv("ECHODESK_PASSWORD") or None)

    # --- Device identity ---
    device_name: str | None = field(default_factory=lambda: os.getenv("ECHODESK_DEVICE_NAME") or None)
    device_type: str = field(default_factory=lambda: os.getenv("ECHODESK_DEVICE_TYPE", "desktop"))

    # --- Timing ---
    heartbeat_interval_seconds: int = field(default_factory=lambda: _env_int("ECHODESK_HEARTBEAT_INTERVAL", 30))
    rest_timeout_seconds: int = field(default_factory=lambda: _env_int("ECHODESK_REST_TIMEOUT", 15))

    # --- Storage paths ---
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("ECHODESK_DATA_DIR", str(_AGENT_DIR))))
    log_dir: Path = field(default_factory=lambda: Path(os.getenv("ECHODESK_LOG_DIR", str(_AGENT_DIR / "logs"))))
    log_level: str = field(default_factory=lambda: os.getenv("ECHODESK_LOG_LEVEL", "INFO"))

    # --- File manager ---
    file_manager_root: str | None = field(default_factory=lambda: os.getenv("ECHODESK_FILE_ROOT") or None)

    @property
    def api_base_url(self) -> str:
        return f"{self.backend_url}{self.api_prefix}"

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


def load_config() -> AgentConfig:
    return AgentConfig()
