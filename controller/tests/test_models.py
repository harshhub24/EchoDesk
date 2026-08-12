"""Unit tests for app.models.* from_dict conversions."""

from __future__ import annotations

from app.models import ActivityEntry, Command, CommandFile, Device, Notification, Telemetry


def test_device_from_dict_full():
    data = {
        "id": "d1", "uuid": "u1", "device_id": "agent-1", "device_name": "Laptop",
        "device_type": "linux", "hostname": "host1", "operating_system": "Linux Mint 22",
        "status": "online", "last_seen_at": "2026-01-01T00:00:00Z",
        "telemetry": {"cpu_percent": 10.0, "ram_percent": 20.0},
        "last_telemetry_at": "2026-01-01T00:00:00Z",
    }
    device = Device.from_dict(data)
    assert device.device_name == "Laptop"
    assert device.telemetry.cpu_percent == 10.0
    assert device.is_online is True


def test_device_from_dict_minimal():
    data = {"id": "d1", "device_id": "agent-1", "device_name": "Laptop", "device_type": "linux"}
    device = Device.from_dict(data)
    assert device.telemetry == Telemetry()
    assert device.is_online is False


def test_telemetry_from_dict_ignores_unknown_fields():
    telemetry = Telemetry.from_dict({"cpu_percent": 5.0, "unexpected_field": "x"})
    assert telemetry.cpu_percent == 5.0
    assert not hasattr(telemetry, "unexpected_field")


def test_telemetry_from_dict_none():
    assert Telemetry.from_dict(None) == Telemetry()


def test_command_from_dict():
    data = {
        "id": "c1", "device_id": "d1", "created_by_id": "u1", "command_type": "LOCK",
        "payload": {}, "status": "pending", "created_at": "2026-01-01T00:00:00Z",
    }
    command = Command.from_dict(data)
    assert command.command_type == "LOCK"
    assert command.status == "pending"


def test_command_file_from_dict():
    data = {
        "id": "f1", "command_id": "c1", "direction": "device_to_owner",
        "original_filename": "report.txt", "content_type": "text/plain",
        "size_bytes": 100, "checksum_sha256": "abc", "uploaded_by": "device",
    }
    command_file = CommandFile.from_dict(data)
    assert command_file.original_filename == "report.txt"
    assert command_file.direction == "device_to_owner"


def test_activity_entry_from_dict():
    entry = ActivityEntry.from_dict({"id": "a1", "activity_type": "login", "category": "auth", "message": "Logged in", "created_at": "2026-01-01T00:00:00Z"})
    assert entry.message == "Logged in"


def test_notification_from_dict():
    n = Notification.from_dict({"id": "n1", "title": "Hi", "message": "Hello", "category": "general", "is_read": False, "created_at": "2026-01-01T00:00:00Z"})
    assert n.title == "Hi"
    assert n.is_read is False
