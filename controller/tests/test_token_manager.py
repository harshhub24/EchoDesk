"""Unit tests for app.auth.token_manager.TokenManager. Mocks the network
(endpoints module) and secure storage so these run without a real backend
or OS keyring/DPAPI.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.api.client import ApiError, RestClient
from app.auth.token_manager import TokenManager
from app.models import Session


@pytest.fixture()
def token_manager(app_config, monkeypatch):
    rest_client = RestClient(app_config)
    manager = TokenManager(app_config, rest_client)

    monkeypatch.setattr("app.auth.token_manager.secure_storage.save_refresh_token", MagicMock())
    monkeypatch.setattr("app.auth.token_manager.secure_storage.load_refresh_token", MagicMock(return_value=None))
    monkeypatch.setattr("app.auth.token_manager.secure_storage.clear_refresh_token", MagicMock())

    return manager


def test_login_returns_session_without_touching_timer(token_manager, monkeypatch):
    monkeypatch.setattr(
        "app.auth.token_manager.endpoints.login",
        lambda client, email, password: {"data": {"user_id": "u1", "access_token": "acc", "refresh_token": "ref"}},
    )

    session, remember = token_manager.login("a@b.com", "pw", True)

    assert isinstance(session, Session)
    assert session.access_token == "acc"
    assert remember is True
    # Timer must NOT have been started by login() itself (thread-safety
    # contract - see token_manager.py docstrings).
    assert not token_manager._refresh_timer.isActive()


def test_activate_session_sets_tokens_and_starts_timer_and_emits(token_manager, qtbot):
    session = Session(user_id="u1", access_token="acc", refresh_token="ref")

    with qtbot.waitSignal(token_manager.session_started, timeout=1000) as blocker:
        token_manager.activate_session(session, remember=True)

    assert blocker.args[0] is session
    assert token_manager.rest_client.access_token == "acc"
    assert token_manager._refresh_timer.isActive()


def test_activate_session_remember_false_clears_storage(token_manager):
    session = Session(user_id="u1", access_token="acc", refresh_token="ref")
    token_manager.activate_session(session, remember=False)

    from app.auth import token_manager as tm_module

    tm_module.secure_storage.clear_refresh_token.assert_called_once()
    tm_module.secure_storage.save_refresh_token.assert_not_called()


def test_deactivate_session_stops_timer_and_emits(token_manager, qtbot):
    session = Session(user_id="u1", access_token="acc", refresh_token="ref")
    token_manager.activate_session(session, remember=True)
    assert token_manager._refresh_timer.isActive()

    with qtbot.waitSignal(token_manager.session_ended, timeout=1000):
        token_manager.deactivate_session()

    assert not token_manager._refresh_timer.isActive()
    assert token_manager.session is None
    assert token_manager.rest_client.access_token is None


def test_restore_session_returns_none_when_no_stored_token(token_manager):
    result = token_manager.restore_session()
    assert result is None


def test_restore_session_returns_session_on_valid_stored_token(token_manager, monkeypatch):
    monkeypatch.setattr("app.auth.token_manager.secure_storage.load_refresh_token", MagicMock(return_value="stored-refresh"))
    monkeypatch.setattr(
        "app.auth.token_manager.endpoints.refresh_tokens",
        lambda client: {"data": {"access_token": "new-acc", "refresh_token": "new-ref"}},
    )

    result = token_manager.restore_session()

    assert result is not None
    session, remember = result
    assert session.access_token == "new-acc"
    assert remember is True


def test_restore_session_clears_storage_on_invalid_token(token_manager, monkeypatch):
    monkeypatch.setattr("app.auth.token_manager.secure_storage.load_refresh_token", MagicMock(return_value="stale-refresh"))

    def raise_api_error(client):
        raise ApiError(401, "invalid refresh token")

    monkeypatch.setattr("app.auth.token_manager.endpoints.refresh_tokens", raise_api_error)

    result = token_manager.restore_session()

    assert result is None
    from app.auth import token_manager as tm_module

    tm_module.secure_storage.clear_refresh_token.assert_called_once()


def test_logout_network_call_is_pure_and_does_not_touch_timer(token_manager, monkeypatch):
    session = Session(user_id="u1", access_token="acc", refresh_token="ref")
    token_manager.activate_session(session, remember=True)

    called = {}
    monkeypatch.setattr(
        "app.auth.token_manager.endpoints.logout",
        lambda client, refresh_token=None: called.setdefault("refresh_token", refresh_token) or {"success": True},
    )

    token_manager.logout()

    assert called["refresh_token"] == "ref"
    # logout() (network part) must not have stopped the timer itself.
    assert token_manager._refresh_timer.isActive()
