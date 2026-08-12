"""Thin REST client over `requests`. Sync by design - always invoked through
`app/utils/workers.py::run_async` from services, never called directly from
a Qt view/widget.

Auth is always a user Bearer token (never `X-API-Key` - that's the Agent's
credential type, see docs/PHASE_1_ANALYSIS.md §1). A 401 triggers exactly
one silent refresh-and-retry; the caller only ever sees the error if that
also fails (meaning the refresh token itself is dead - full re-login
needed).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

import requests

from app.config import AppConfig

logger = logging.getLogger("controller.api.client")

_TRANSIENT_EXCEPTIONS = (requests.ConnectionError, requests.Timeout)
_MAX_TRANSIENT_RETRIES = 3


class ApiError(Exception):
    def __init__(self, status_code: int, message: str, payload: Any = None):
        super().__init__(f"API error {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.payload = payload


class AuthenticationError(ApiError):
    pass


class RestClient:
    def __init__(self, config: AppConfig):
        self.config = config
        self._session = requests.Session()
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        # Called (without args) when a request gets a 401 - should perform
        # the refresh and return True on success. Wired up by
        # app/auth/token_manager.py once the session exists, avoiding a
        # circular import between the two modules.
        self.on_unauthorized: Callable[[], bool] | None = None

    def set_tokens(self, access_token: str | None, refresh_token: str | None = None) -> None:
        self._access_token = access_token
        if refresh_token is not None:
            self._refresh_token = refresh_token

    def clear_tokens(self) -> None:
        self._access_token = None
        self._refresh_token = None

    @property
    def access_token(self) -> str | None:
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        return self._refresh_token

    def _headers(self, use_refresh_token: bool = False) -> dict:
        token = self._refresh_token if use_refresh_token else self._access_token
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    def _url(self, path: str) -> str:
        return f"{self.config.api_base_url}{path}"

    def _request(self, method: str, path: str, *, use_refresh_token: bool = False, retry_on_401: bool = True, **kwargs) -> requests.Response:
        last_error: Exception | None = None
        for attempt in range(1, _MAX_TRANSIENT_RETRIES + 1):
            try:
                response = self._session.request(
                    method,
                    self._url(path),
                    headers=self._headers(use_refresh_token),
                    timeout=self.config.rest_timeout_seconds,
                    verify=self.config.verify_tls,
                    **kwargs,
                )
                break
            except _TRANSIENT_EXCEPTIONS as error:
                last_error = error
                logger.warning("Transient network error (attempt %d/%d): %s", attempt, _MAX_TRANSIENT_RETRIES, error)
                time.sleep(min(2 ** attempt, 8))
        else:
            raise ApiError(0, f"Network error after {_MAX_TRANSIENT_RETRIES} attempts: {last_error}")

        if response.status_code == 401 and retry_on_401 and not use_refresh_token and self.on_unauthorized:
            if self.on_unauthorized():
                return self._request(method, path, use_refresh_token=use_refresh_token, retry_on_401=False, **kwargs)

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
        return self._request("GET", path, params=params).json()

    def post(self, path: str, json_body: dict | None = None, use_refresh_token: bool = False) -> dict:
        return self._request("POST", path, json=json_body, use_refresh_token=use_refresh_token).json()

    def put(self, path: str, json_body: dict | None = None) -> dict:
        return self._request("PUT", path, json=json_body).json()

    def delete(self, path: str, json_body: dict | None = None) -> dict:
        return self._request("DELETE", path, json=json_body).json()

    def upload_file(self, path: str, filename: str, content: bytes, content_type: str = "application/octet-stream") -> dict:
        files = {"file": (filename, content, content_type)}
        return self._request("POST", path, files=files).json()

    def download_file(self, path: str) -> bytes:
        return self._request("GET", path).content

    def close(self) -> None:
        self._session.close()
