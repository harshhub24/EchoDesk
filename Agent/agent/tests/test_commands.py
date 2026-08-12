"""Unit tests for agent.commands.validator and agent.commands.dispatcher."""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

import pytest

from agent.commands.dispatcher import CommandDispatcher
from agent.commands.validator import InvalidCommandError, is_expired, validate_envelope, validate_payload
from agent.constants import CommandStatus, CommandType


# --- validator ---------------------------------------------------------------------


def test_validate_envelope_accepts_known_type():
    validate_envelope({"id": "cmd-1", "command_type": CommandType.LOCK.value})


def test_validate_envelope_rejects_unknown_type():
    with pytest.raises(InvalidCommandError):
        validate_envelope({"id": "cmd-1", "command_type": "NOT_A_REAL_COMMAND"})


def test_validate_envelope_requires_id():
    with pytest.raises(InvalidCommandError):
        validate_envelope({"command_type": CommandType.LOCK.value})


def test_validate_payload_requires_message_for_message_request():
    with pytest.raises(InvalidCommandError):
        validate_payload(CommandType.MESSAGE_REQUEST.value, {})
    validate_payload(CommandType.MESSAGE_REQUEST.value, {"message": "hi"})


def test_validate_payload_requires_path_for_file_download():
    with pytest.raises(InvalidCommandError):
        validate_payload(CommandType.FILE_DOWNLOAD_REQUEST.value, {})
    validate_payload(CommandType.FILE_DOWNLOAD_REQUEST.value, {"path": "/tmp/x.txt"})


def test_validate_payload_file_upload_needs_destination():
    with pytest.raises(InvalidCommandError):
        validate_payload(CommandType.FILE_UPLOAD_REQUEST.value, {})
    validate_payload(CommandType.FILE_UPLOAD_REQUEST.value, {"destination_path": "/tmp/x.txt"})


def test_is_expired_true_for_past_timestamp():
    past = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=20)).isoformat()
    assert is_expired(past) is True


def test_is_expired_false_for_future_timestamp():
    future = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=20)).isoformat()
    assert is_expired(future) is False


def test_is_expired_false_when_missing():
    assert is_expired(None) is False


def test_is_expired_handles_naive_datetime_as_utc():
    # The backend serializes naive UTC datetimes (no offset suffix) - must
    # not raise TypeError comparing naive vs. aware.
    now_naive = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    naive_past = (now_naive - datetime.timedelta(minutes=20)).isoformat()
    naive_future = (now_naive + datetime.timedelta(minutes=20)).isoformat()
    assert is_expired(naive_past) is True
    assert is_expired(naive_future) is False


# --- dispatcher --------------------------------------------------------------------


def _command(command_type: str = CommandType.LOCK.value, **overrides) -> dict:
    base = {"id": "cmd-123", "command_type": command_type, "payload": {}, "expires_at": None}
    base.update(overrides)
    return base


def test_dispatcher_acks_and_reports_success():
    rest_client = MagicMock()
    socket_client = MagicMock()
    socket_client.connected = True

    dispatcher = CommandDispatcher(rest_client=rest_client, socket_client=socket_client, file_root=None)

    with patch("agent.commands.dispatcher.handlers.execute", return_value={"action": "lock", "initiated": True}) as mock_execute:
        dispatcher.handle(_command())

    mock_execute.assert_called_once()
    ack_calls = [call.args[1] for call in socket_client.emit_command_ack.call_args_list]
    assert ack_calls == [CommandStatus.DELIVERED.value, CommandStatus.EXECUTING.value]
    socket_client.emit_command_result.assert_called_once()
    result_args = socket_client.emit_command_result.call_args.args
    assert result_args[1] == CommandStatus.SUCCESS.value


def test_dispatcher_reports_failure_on_handler_exception():
    rest_client = MagicMock()
    socket_client = MagicMock()
    socket_client.connected = True
    dispatcher = CommandDispatcher(rest_client=rest_client, socket_client=socket_client, file_root=None)

    with patch("agent.commands.dispatcher.handlers.execute", side_effect=RuntimeError("boom")):
        dispatcher.handle(_command())

    result_args = socket_client.emit_command_result.call_args.args
    assert result_args[1] == CommandStatus.FAILED.value


def test_dispatcher_skips_expired_command():
    rest_client = MagicMock()
    socket_client = MagicMock()
    socket_client.connected = True
    dispatcher = CommandDispatcher(rest_client=rest_client, socket_client=socket_client, file_root=None)

    past = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=20)).isoformat()
    with patch("agent.commands.dispatcher.handlers.execute") as mock_execute:
        dispatcher.handle(_command(expires_at=past))

    mock_execute.assert_not_called()
    socket_client.emit_command_ack.assert_not_called()


def test_dispatcher_ignores_duplicate_command_id():
    rest_client = MagicMock()
    socket_client = MagicMock()
    socket_client.connected = True
    dispatcher = CommandDispatcher(rest_client=rest_client, socket_client=socket_client, file_root=None)

    with patch("agent.commands.dispatcher.handlers.execute", return_value={"ok": True}) as mock_execute:
        dispatcher.handle(_command())
        dispatcher.handle(_command())  # same id again

    assert mock_execute.call_count == 1


def test_dispatcher_queues_result_when_socket_disconnected_then_flushes():
    rest_client = MagicMock()
    socket_client = MagicMock()
    socket_client.connected = False
    dispatcher = CommandDispatcher(rest_client=rest_client, socket_client=socket_client, file_root=None)

    with patch("agent.commands.dispatcher.handlers.execute", return_value={"ok": True}):
        dispatcher.handle(_command())

    socket_client.emit_command_result.assert_not_called()
    assert len(dispatcher._pending) >= 1

    socket_client.connected = True
    dispatcher.flush_pending()

    assert socket_client.emit_command_result.called
    assert dispatcher._pending == []


def test_dispatcher_rejects_invalid_payload_without_executing():
    rest_client = MagicMock()
    socket_client = MagicMock()
    socket_client.connected = True
    dispatcher = CommandDispatcher(rest_client=rest_client, socket_client=socket_client, file_root=None)

    with patch("agent.commands.dispatcher.handlers.execute") as mock_execute:
        dispatcher.handle(_command(command_type=CommandType.MESSAGE_REQUEST.value, payload={}))

    mock_execute.assert_not_called()
    result_args = socket_client.emit_command_result.call_args.args
    assert result_args[1] == CommandStatus.FAILED.value
