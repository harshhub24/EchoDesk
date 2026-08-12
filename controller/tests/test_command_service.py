"""Unit tests for app.services.command_service.CommandService, mocked
network via monkeypatching the endpoints module.
"""

from __future__ import annotations

from app.api.client import RestClient
from app.services.command_service import CommandService


def _service(app_config):
    rest_client = RestClient(app_config)

    class _FakeAppState:
        def __init__(self):
            self.rest_client = rest_client
            self.config = app_config

    return CommandService(_FakeAppState())


def test_send_command_emits_command_created(app_config, monkeypatch, qtbot):
    monkeypatch.setattr(
        "app.services.command_service.endpoints.create_command",
        lambda client, device_id, command_type, payload: {
            "data": {"id": "c1", "device_id": device_id, "created_by_id": "u1", "command_type": command_type, "payload": payload, "status": "pending", "created_at": "2026-01-01T00:00:00Z"}
        },
    )

    service = _service(app_config)
    results = {}
    service.command_created.connect(lambda c: results.setdefault("command", c))

    service.send_command("dev-1", "LOCK", {})

    qtbot.waitUntil(lambda: "command" in results, timeout=2000)
    assert results["command"].command_type == "LOCK"


def test_send_command_emits_failure_on_error(app_config, monkeypatch, qtbot):
    from app.api.client import ApiError

    def raise_error(client, device_id, command_type, payload):
        raise ApiError(404, "Device not found")

    monkeypatch.setattr("app.services.command_service.endpoints.create_command", raise_error)

    service = _service(app_config)
    results = {}
    service.command_create_failed.connect(lambda msg: results.setdefault("error", msg))

    service.send_command("dev-1", "LOCK", {})

    qtbot.waitUntil(lambda: "error" in results, timeout=2000)
    assert "Device not found" in results["error"]


def test_refresh_emits_sorted_commands(app_config, monkeypatch, qtbot):
    monkeypatch.setattr(
        "app.services.command_service.endpoints.list_commands",
        lambda client: [
            {"id": "c1", "device_id": "d1", "created_by_id": "u1", "command_type": "LOCK", "payload": {}, "status": "success", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "c2", "device_id": "d1", "created_by_id": "u1", "command_type": "RESTART", "payload": {}, "status": "pending", "created_at": "2026-01-02T00:00:00Z"},
        ],
    )

    service = _service(app_config)
    results = {}
    service.commands_updated.connect(lambda cmds: results.setdefault("commands", cmds))

    service.refresh()

    qtbot.waitUntil(lambda: "commands" in results, timeout=2000)
    assert [c.id for c in results["commands"]] == ["c2", "c1"]  # newest first
