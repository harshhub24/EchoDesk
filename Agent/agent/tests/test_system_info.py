"""Unit tests for agent.system.* collectors - run against the real local
machine via psutil (no mocking needed, these are cheap and side-effect-free).
"""

from __future__ import annotations

from agent.system import battery, cpu, device, disk, network, ram
from agent.system.hostname import get_hostname


def test_get_hostname_returns_nonempty_string():
    assert isinstance(get_hostname(), str)
    assert get_hostname()


def test_cpu_info_has_expected_keys():
    info = cpu.get_cpu_info()
    for key in ("processor", "physical_cores", "logical_cores", "architecture"):
        assert key in info


def test_cpu_percent_is_a_float_in_range():
    value = cpu.get_cpu_percent(interval=0.1)
    assert isinstance(value, float)
    assert 0.0 <= value <= 100.0


def test_ram_info_has_expected_keys_and_ranges():
    info = ram.get_ram_info()
    assert 0 <= info["ram_percent"] <= 100
    assert info["ram_used_mb"] >= 0
    assert info["ram_total_mb"] > 0


def test_disk_info_has_expected_keys_and_ranges():
    info = disk.get_disk_info()
    assert 0 <= info["disk_percent"] <= 100
    assert info["disk_total_gb"] > 0


def test_battery_info_returns_none_or_values():
    info = battery.get_battery_info()
    assert "battery_percent" in info
    assert "battery_charging" in info
    if info["battery_percent"] is not None:
        assert 0 <= info["battery_percent"] <= 100


def test_network_info_has_expected_keys():
    info = network.get_network_info()
    assert info["network_status"] in ("connected", "disconnected")
    assert "ip_address" in info
    assert "mac_address" in info


def test_collect_telemetry_matches_backend_schema_field_names():
    telemetry = device.collect_telemetry()
    # These must match app/schemas/devices.py::TelemetryPayload on the
    # backend exactly, or the backend will reject the heartbeat (extra="forbid").
    expected_fields = {
        "cpu_percent",
        "ram_percent",
        "ram_used_mb",
        "ram_total_mb",
        "disk_percent",
        "disk_used_gb",
        "disk_total_gb",
        "battery_percent",
        "battery_charging",
        "network_status",
        "ip_address",
        "mac_address",
        "uptime_seconds",
    }
    assert expected_fields.issubset(telemetry.keys())


def test_load_or_create_device_id_is_stable_across_calls(tmp_path):
    first = device.load_or_create_device_id(tmp_path)
    second = device.load_or_create_device_id(tmp_path)
    assert first == second


def test_load_or_create_device_id_generates_valid_uuid(tmp_path):
    import uuid

    device_id = device.load_or_create_device_id(tmp_path)
    uuid.UUID(device_id)  # raises ValueError if not a valid UUID
