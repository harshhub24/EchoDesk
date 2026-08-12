"""Thin REST client over httpx.

Handles base URL, timeout, TLS verification, and switching between the two
supported auth modes (device API key preferred, bearer token for the
one-time bootstrap login). Retries transient network failures with backoff;
HTTP-level errors (4xx/5xx) are raised immediately as ApiError, not retried,
since retrying "unauthorized" or "not found" endlessly is never useful.
"""

from __future__ import annotations

import logging
from typing import Any, BinaryIO

import httpx

from agent.config import AgentConfig
from agent.utils.retry import network_retry

logger = logging.getLogger("agent.api.client")


class ApiError(Exception):
    def __init__(self, status_code: int, message: str, payload: Any = None):
        super().__init__(f"API error {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.payload = payload


class AuthenticationError(ApiError):
    pass


class RestClient:
    def __init__(self, config: AgentConfig):
        self.config = config
        self._client = httpx.Client(
            base_url=config.api_base_url,
            timeout=config.rest_timeout_seconds,
            verify=config.verify_tls,
        )
        self._bearer_token: str | None = None
        self._api_key: str | None = config.api_key

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "RestClient":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    # --- Credential management -------------------------------------------------

    def set_bearer_token(self, token: str | None) -> None:
        self._bearer_token = token

    def set_api_key(self, api_key: str | None) -> None:
        self._api_key = api_key
        if api_key:
            # Once a device API key is available, prefer it over any bearer
            # token so the user's session token stops being used/renewed.
            self._bearer_token = None

    def has_credentials(self) -> bool:
        return bool(self._api_key or self._bearer_token)

    def _auth_headers(self) -> dict:
        if self._api_key:
            return {"X-API-Key": self._api_key}
        if self._bearer_token:
            return {"Authorization": f"Bearer {self._bearer_token}"}
        return {}

    # --- Low-level request wrapper ---------------------------------------------

    @network_retry(5, httpx.TransportError, httpx.TimeoutException)
    def _send(self, method: str, path: str, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", {}) or {}
        headers.update(self._auth_headers())
        response = self._client.request(method, path, headers=headers, **kwargs)
        if response.status_code >= 400:
            try:
                payload = response.json()
                message = payload.get("message", response.text)
            except Exception:
                payload = None
                message = response.text
            error_cls = AuthenticationError if response.status_code in (401, 403) else ApiError
            raise error_cls(response.status_code, message, payload)
        return response

    # --- Convenience verbs -------------------------------------------------------

    def get(self, path: str, params: dict | None = None) -> dict:
        return self._send("GET", path, params=params).json()

    def post(self, path: str, json_body: dict | None = None) -> dict:
        return self._send("POST", path, json=json_body).json()

    def delete(self, path: str, json_body: dict | None = None) -> dict:
        return self._send("DELETE", path, json=json_body).json()

    def upload_file(
        self,
        path: str,
        filename: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> dict:
        files = {"file": (filename, content, content_type)}
        return self._send("POST", path, files=files).json()

    def upload_file_stream(
        self,
        path: str,
        filename: str,
        stream: BinaryIO,
        content_type: str = "application/octet-stream",
    ) -> dict:
        files = {"file": (filename, stream, content_type)}
        return self._send("POST", path, files=files).json()

    def download_file(self, path: str) -> bytes:
        return self._send("GET", path).content
