"""Persists the refresh token for "Remember Login", encrypted at rest.

Primary path (Windows, the only OS this app ships for): DPAPI via
`win32crypt.CryptProtectData`, user-scoped (tied to the Windows login),
written to a file in the config data dir. Nothing is recoverable without
being logged in as the same Windows user.

Fallback (non-Windows, source-only dev environments where pywin32 isn't
installed): the `keyring` package's OS-appropriate secret store. Clearly
separated so it's obvious in code review this path is dev convenience, not
what ships.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger("controller.auth.secure_storage")

_SERVICE_NAME = "EchoDeskController"
_ACCOUNT_NAME = "refresh_token"
_DPAPI_FILE_NAME = "refresh_token.bin"


def _is_windows() -> bool:
    return sys.platform == "win32"


def save_refresh_token(data_dir: Path, refresh_token: str) -> None:
    if _is_windows():
        _save_dpapi(data_dir, refresh_token)
    else:
        _save_keyring(refresh_token)


def load_refresh_token(data_dir: Path) -> str | None:
    if _is_windows():
        return _load_dpapi(data_dir)
    return _load_keyring()


def clear_refresh_token(data_dir: Path) -> None:
    if _is_windows():
        _clear_dpapi(data_dir)
    else:
        _clear_keyring()


# --- Windows DPAPI ---------------------------------------------------------------------

def _dpapi_file(data_dir: Path) -> Path:
    return data_dir / _DPAPI_FILE_NAME


def _save_dpapi(data_dir: Path, refresh_token: str) -> None:
    try:
        import win32crypt

        encrypted = win32crypt.CryptProtectData(refresh_token.encode("utf-8"), _SERVICE_NAME, None, None, None, 0)
        data_dir.mkdir(parents=True, exist_ok=True)
        _dpapi_file(data_dir).write_bytes(encrypted)
    except ImportError:
        logger.warning("pywin32 not available - cannot persist refresh token securely on this system")
    except Exception as error:
        logger.warning("Failed to persist refresh token via DPAPI: %s", error)


def _load_dpapi(data_dir: Path) -> str | None:
    path = _dpapi_file(data_dir)
    if not path.exists():
        return None
    try:
        import win32crypt

        encrypted = path.read_bytes()
        _description, decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
        return decrypted.decode("utf-8")
    except ImportError:
        logger.warning("pywin32 not available - cannot read persisted refresh token")
        return None
    except Exception as error:
        logger.warning("Failed to decrypt persisted refresh token (will require re-login): %s", error)
        return None


def _clear_dpapi(data_dir: Path) -> None:
    path = _dpapi_file(data_dir)
    if path.exists():
        path.unlink()


# --- keyring fallback (non-Windows dev only) --------------------------------------------

def _save_keyring(refresh_token: str) -> None:
    try:
        import keyring

        keyring.set_password(_SERVICE_NAME, _ACCOUNT_NAME, refresh_token)
    except Exception as error:
        logger.warning("Failed to persist refresh token via keyring: %s", error)


def _load_keyring() -> str | None:
    try:
        import keyring

        return keyring.get_password(_SERVICE_NAME, _ACCOUNT_NAME)
    except Exception as error:
        logger.warning("Failed to read refresh token via keyring: %s", error)
        return None


def _clear_keyring() -> None:
    try:
        import keyring

        keyring.delete_password(_SERVICE_NAME, _ACCOUNT_NAME)
    except Exception:
        pass  # nothing to clear, or backend unavailable - non-fatal either way
