"""JWT and token helper utilities."""

from __future__ import annotations

from typing import Any

from flask_jwt_extended import create_access_token, create_refresh_token


def build_token_pair(identity: str, additional_claims: dict[str, Any] | None = None) -> dict[str, str]:
    access_token = create_access_token(identity=identity, additional_claims=additional_claims or {})
    refresh_token = create_refresh_token(identity=identity, additional_claims=additional_claims or {})
    return {"access_token": access_token, "refresh_token": refresh_token}
