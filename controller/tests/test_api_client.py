"""Unit tests for app.api.client.RestClient. Mocks requests.Session.request
directly so no real network calls are made.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.api.client import ApiError, AuthenticationError, RestClient


def _fake_response(status_code=200, json_body=None, content=b""):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_body or {"success": True, "message": "ok", "data": {}}
    response.text = str(json_body)
    response.content = content
    return response


def test_bearer_header_sent_when_access_token_set(app_config):
    client = RestClient(app_config)
    client.set_tokens("access-abc", "refresh-xyz")
    client._session.request = MagicMock(return_value=_fake_response())

    client.get("/devices")

    _args, kwargs = client._session.request.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer access-abc"


def test_refresh_token_used_when_use_refresh_token_flag_set(app_config):
    client = RestClient(app_config)
    client.set_tokens("access-abc", "refresh-xyz")
    client._session.request = MagicMock(return_value=_fake_response())

    client.post("/refresh", use_refresh_token=True)

    _args, kwargs = client._session.request.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer refresh-xyz"


def test_4xx_raises_api_error(app_config):
    client = RestClient(app_config)
    client._session.request = MagicMock(return_value=_fake_response(404, {"success": False, "message": "Not found"}))

    with pytest.raises(ApiError) as excinfo:
        client.get("/devices/nope")
    assert excinfo.value.status_code == 404
    assert "Not found" in str(excinfo.value)


def test_401_triggers_on_unauthorized_and_retries(app_config):
    client = RestClient(app_config)
    client.set_tokens("expired-token", "refresh-xyz")

    responses = [_fake_response(401, {"success": False, "message": "expired"}), _fake_response(200)]
    client._session.request = MagicMock(side_effect=responses)

    refresh_calls = []

    def fake_refresh():
        refresh_calls.append(1)
        client.set_tokens("new-access-token", "refresh-xyz")
        return True

    client.on_unauthorized = fake_refresh

    result = client.get("/devices")

    assert refresh_calls == [1]
    assert client._session.request.call_count == 2
    assert result["success"] is True


def test_401_without_successful_refresh_raises_authentication_error(app_config):
    client = RestClient(app_config)
    client.set_tokens("expired-token", "refresh-xyz")
    client._session.request = MagicMock(return_value=_fake_response(401, {"success": False, "message": "expired"}))
    client.on_unauthorized = lambda: False

    with pytest.raises(AuthenticationError):
        client.get("/devices")


def test_upload_file_sends_multipart(app_config):
    client = RestClient(app_config)
    client._session.request = MagicMock(return_value=_fake_response(201, {"success": True, "message": "ok", "data": {"id": "file-1"}}))

    result = client.upload_file("/commands/cmd-1/files", "test.txt", b"hello", "text/plain")

    _args, kwargs = client._session.request.call_args
    assert "files" in kwargs
    assert result["data"]["id"] == "file-1"


def test_clear_tokens_removes_auth_header(app_config):
    client = RestClient(app_config)
    client.set_tokens("access-abc", "refresh-xyz")
    client.clear_tokens()
    assert client._headers() == {}
