"""Unit tests for agent.api.client.RestClient, using httpx.MockTransport so
no real network calls are made.
"""

from __future__ import annotations

import httpx
import pytest

from agent.api.client import ApiError, AuthenticationError, RestClient
from agent.config import AgentConfig


def _client_with_transport(handler) -> RestClient:
    config = AgentConfig(backend_url="http://testserver", api_prefix="/api/v1")
    client = RestClient(config)
    client._client = httpx.Client(
        base_url=config.api_base_url, transport=httpx.MockTransport(handler)
    )
    return client


def test_uses_api_key_header_when_set():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = request.headers
        return httpx.Response(200, json={"success": True, "message": "ok", "data": {}})

    client = _client_with_transport(handler)
    client.set_api_key("prefix123.secretvalue")
    client.get("/devices/heartbeat")

    assert captured["headers"]["X-API-Key"] == "prefix123.secretvalue"
    assert "Authorization" not in captured["headers"]


def test_uses_bearer_token_when_no_api_key():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = request.headers
        return httpx.Response(200, json={"success": True, "message": "ok", "data": {}})

    client = _client_with_transport(handler)
    client.set_bearer_token("access-token-abc")
    client.get("/devices")

    assert captured["headers"]["Authorization"] == "Bearer access-token-abc"


def test_setting_api_key_clears_bearer_token():
    client = _client_with_transport(lambda r: httpx.Response(200, json={}))
    client.set_bearer_token("token")
    client.set_api_key("prefix.secret")

    headers = client._auth_headers()
    assert headers == {"X-API-Key": "prefix.secret"}


def test_4xx_raises_api_error_with_message():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"success": False, "message": "Device not found"})

    client = _client_with_transport(handler)
    with pytest.raises(ApiError) as excinfo:
        client.get("/devices/nope")
    assert excinfo.value.status_code == 404
    assert "Device not found" in str(excinfo.value)


def test_401_raises_authentication_error_subclass():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"success": False, "message": "Invalid or expired API key"})

    client = _client_with_transport(handler)
    with pytest.raises(AuthenticationError):
        client.post("/devices/heartbeat", {"status": "online"})


def test_upload_file_sends_multipart():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["content_type"] = request.headers.get("content-type", "")
        return httpx.Response(201, json={"success": True, "message": "ok", "data": {"id": "file-1"}})

    client = _client_with_transport(handler)
    result = client.upload_file("/commands/cmd-1/files", "test.txt", b"hello world", "text/plain")

    assert "multipart/form-data" in captured["content_type"]
    assert result["data"]["id"] == "file-1"
