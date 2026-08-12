"""Enrollment / credential bootstrap.

Enrollment happens once:
  1. First run with no persisted device API key: log in with
     ECHODESK_EMAIL/ECHODESK_PASSWORD (bearer token), call /devices/register,
     then mint a device API key via /devices/{id}/api-key.
  2. Persist that key locally (device_credentials.json, chmod 600 on POSIX).
  3. Every run after that: load the persisted key and skip straight to
     heartbeat/socket - no login, no re-registration needed. (Re-registering
     on every start is unnecessary: the API key already identifies the
     device, and heartbeat already keeps last_seen_at/status current.)

If you need to update device_name/hostname/operating_system after they
change, delete device_credentials.json and re-run with bootstrap credentials
in .env to re-enroll.
"""

from __future__ import annotations

import json
import logging
import os
import stat
from pathlib import Path

from agent.api import endpoints
from agent.api.client import RestClient
from agent.config import AgentConfig
from agent.constants import API_KEY_FILE_NAME
from agent.platform.common import current_platform
from agent.constants import Platform
from agent.system import device as device_info

logger = logging.getLogger("agent.api.auth")


class EnrollmentError(RuntimeError):
    pass


def _credentials_file(data_dir: Path) -> Path:
    return data_dir / API_KEY_FILE_NAME


def load_persisted_api_key(data_dir: Path) -> str | None:
    path = _credentials_file(data_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("api_key")
    except (json.JSONDecodeError, OSError) as error:
        logger.warning("Could not read persisted credentials (%s)", error)
        return None


def persist_api_key(data_dir: Path, api_key: str, backend_device_row_id: str) -> None:
    path = _credentials_file(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"api_key": api_key, "device_id": backend_device_row_id}), encoding="utf-8")
    if current_platform() != Platform.WINDOWS:
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0600: owner read/write only
        except OSError as error:
            logger.warning("Could not restrict permissions on %s: %s", path, error)


def ensure_authenticated(client: RestClient, config: AgentConfig, data_dir: Path, local_device_id: str) -> str:
    """Return a ready-to-use device API key, bootstrapping enrollment if needed."""

    persisted_key = load_persisted_api_key(data_dir)
    if persisted_key:
        logger.info("Using persisted device API key (no login required)")
        client.set_api_key(persisted_key)
        return persisted_key

    if config.api_key:
        logger.info("Using device API key from configuration")
        client.set_api_key(config.api_key)
        persist_api_key(data_dir, config.api_key, backend_device_row_id="unknown")
        return config.api_key

    if not (config.bootstrap_email and config.bootstrap_password):
        raise EnrollmentError(
            "No device API key available and no ECHODESK_EMAIL/ECHODESK_PASSWORD set for "
            "first-run enrollment. Set one of these in .env - see .env.example."
        )

    logger.info("No device API key found - performing one-time enrollment via login")
    login_response = endpoints.login(client, config.bootstrap_email, config.bootstrap_password)
    access_token = login_response["data"]["access_token"]
    client.set_bearer_token(access_token)

    registration_info = device_info.collect_registration_info(config.device_name, config.device_type)
    registration_info["device_id"] = local_device_id
    register_response = endpoints.register_device(client, **registration_info)
    backend_device_row_id = register_response["data"]["id"]
    device_info.save_backend_device_row_id(data_dir, backend_device_row_id)

    key_response = endpoints.issue_device_api_key(client, backend_device_row_id, key_name="agent")
    api_key = key_response["data"]["api_key"]

    persist_api_key(data_dir, api_key, backend_device_row_id)
    client.set_api_key(api_key)

    logger.info(
        "Enrollment complete for device_id=%s (backend id=%s). "
        "You can now remove ECHODESK_EMAIL/ECHODESK_PASSWORD from .env.",
        local_device_id,
        backend_device_row_id,
    )
    return api_key
