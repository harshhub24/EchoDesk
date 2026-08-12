"""Device API key generation utilities.

Key format: "{prefix}.{secret}" where prefix is a short, non-secret lookup value
(stored in plaintext, indexed) and secret is a high-entropy value that is only
ever stored hashed (bcrypt, same scheme as user passwords). The raw key is shown
to the owner exactly once at creation/rotation time and cannot be recovered.
"""

from __future__ import annotations

import secrets

from app.security.passwords import hash_password

KEY_PREFIX_BYTES = 6
KEY_SECRET_BYTES = 32


def generate_api_key() -> tuple[str, str, str]:
    """Return (key_prefix, raw_secret, hashed_secret)."""

    key_prefix = secrets.token_hex(KEY_PREFIX_BYTES)
    raw_secret = secrets.token_urlsafe(KEY_SECRET_BYTES)
    hashed_secret = hash_password(raw_secret)
    return key_prefix, raw_secret, hashed_secret


def format_api_key(key_prefix: str, raw_secret: str) -> str:
    return f"{key_prefix}.{raw_secret}"


def parse_api_key(raw_key: str) -> tuple[str, str] | None:
    if not raw_key or "." not in raw_key:
        return None
    key_prefix, _, secret = raw_key.partition(".")
    if not key_prefix or not secret:
        return None
    return key_prefix, secret
