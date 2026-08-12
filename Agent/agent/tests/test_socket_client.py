"""Unit tests for agent.socket.client / agent.socket.events. These test
wiring and behavior without opening a real network connection.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent.socket.client import SocketClient
from agent.socket.events import register_command_handler


def _make_config():
    from agent.config import AgentConfig

    return AgentConfig(backend_url="http://testserver", api_prefix="/api/v1")


def test_socket_client_starts_disconnected():
    client = SocketClient(_make_config(), api_key="prefix.secret")
    assert client.connected is False


def test_connect_passes_api_key_as_auth():
    config = _make_config()
    client = SocketClient(config, api_key="prefix.secret")

    with patch.object(client._sio, "connect") as mock_connect:
        client.connect()

    _args, kwargs = mock_connect.call_args
    assert kwargs["auth"] == {"api_key": "prefix.secret"}


def test_emit_heartbeat_noop_when_disconnected():
    client = SocketClient(_make_config(), api_key="prefix.secret")
    with patch.object(client._sio, "emit") as mock_emit:
        client.emit_heartbeat("online", {"cpu_percent": 5.0})
    mock_emit.assert_not_called()


def test_emit_command_ack_calls_underlying_emit():
    client = SocketClient(_make_config(), api_key="prefix.secret")
    with patch.object(client._sio, "emit") as mock_emit:
        client.emit_command_ack("cmd-1", "delivered")
    mock_emit.assert_called_once_with("command_ack", {"command_id": "cmd-1", "status": "delivered"})


def test_emit_command_result_calls_underlying_emit():
    client = SocketClient(_make_config(), api_key="prefix.secret")
    with patch.object(client._sio, "emit") as mock_emit:
        client.emit_command_result("cmd-1", "success", {"foo": "bar"})
    mock_emit.assert_called_once_with(
        "command_result",
        {"command_id": "cmd-1", "execution_status": "success", "output": {"foo": "bar"}, "raw_payload": {}},
    )


def test_register_command_handler_dispatches_on_background_thread():
    socket_client = MagicMock()
    received = {}

    def handler(command):
        received["command"] = command

    register_command_handler(socket_client, handler)

    # Grab the internal wrapper that was registered with socket_client.on(...)
    registered_event_name, wrapper = socket_client.on.call_args.args
    assert registered_event_name == "command_created"

    wrapper({"id": "cmd-1", "command_type": "LOCK"})

    import time

    time.sleep(0.2)  # let the background thread run
    assert received["command"]["id"] == "cmd-1"


def test_register_command_handler_unwraps_backend_envelope():
    """The backend actually emits command_created as
    {"success": True, "command": {...}} (see backend
    app/api/commands/routes.py) - the handler must receive the unwrapped
    command dict, not the envelope.
    """

    socket_client = MagicMock()
    received = {}

    def handler(command):
        received["command"] = command

    register_command_handler(socket_client, handler)
    _event_name, wrapper = socket_client.on.call_args.args

    wrapper({"success": True, "command": {"id": "cmd-2", "command_type": "RESTART"}})

    import time

    time.sleep(0.2)
    assert received["command"] == {"id": "cmd-2", "command_type": "RESTART"}
