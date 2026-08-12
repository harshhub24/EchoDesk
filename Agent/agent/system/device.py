"""Device identity (local UUID) and the full info snapshot collected on first
run / registration and reused for the backend's DeviceRegisterRequest.
"""

from __future__ import annotations

import json
import logging
import platform as stdlib_platform
import sys
import time
import uuid
from pathlib import Path

from agent.constants import STATE_FILE_NAME
from agent.platform import common as platform_common
from agent.system import battery, cpu, disk, network, ram
from agent.system.hostname import get_hostname

logger = logging.getLogger("agent.system.device")

_START_TIME = time.time()


def _state_file(data_dir: Path) -> Path:
    return data_dir / STATE_FILE_NAME


def load_or_create_device_id(data_dir: Path) -> str:
    """Return a stable local device_id, generating and persisting one on
    first run. This is the Agent's own identifier (distinct from the
    backend's internal row id/uuid), sent as `device_id` in
    /devices/register.
    """

    state_path = _state_file(data_dir)
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            existing = state.get("device_id")
            if existing:
                return existing
        except (json.JSONDecodeError, OSError) as error:
            logger.warning("Could not read existing state file (%s); generating a new device_id", error)

    device_id = str(uuid.uuid4())
    data_dir.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"device_id": device_id}), encoding="utf-8")
    logger.info("Generated new local device_id: %s", device_id)
    return device_id


def save_backend_device_row_id(data_dir: Path, backend_device_row_id: str) -> None:
    """Persist the backend's own row id alongside our local device_id, purely
    for local debugging/logging - not required for API calls, since the
    device API key already scopes every request to the right device.
    """

    state_path = _state_file(data_dir)
    state = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            state = {}
    state["backend_device_row_id"] = backend_device_row_id
    state_path.write_text(json.dumps(state), encoding="utf-8")


def get_uptime_seconds() -> int:
    return int(time.time() - _START_TIME)


def collect_registration_info(device_name: str | None, device_type: str) -> dict:
    """Everything needed for POST /devices/register.

    Only hostname/operating_system are accepted by the backend's
    DeviceRegisterRequest today - the richer fields (kernel, arch, python
    version, cpu/ram/storage/battery) are collected here too and folded into
    the *first heartbeat's* telemetry payload instead, since that's the field
    the backend actually persists them to.
    """

    hostname = get_hostname()
    return {
        "device_id": None,  # filled in by the caller (system.device.load_or_create_device_id)
        "device_name": device_name or hostname,
        "device_type": device_type,
        "hostname": hostname,
        "operating_system": platform_common.os_version(),
    }


def collect_static_system_info() -> dict:
    """Info that doesn't change between heartbeats - logged locally and
    useful for support/debugging, not currently sent over the wire (the
    backend's telemetry schema is metrics-focused; see docs/COMMAND_FLOW.md
    for the full list of what is/isn't transmitted).
    """

    return {
        "hostname": get_hostname(),
        "operating_system": platform_common.os_version(),
        "kernel_version": platform_common.kernel_version(),
        "architecture": stdlib_platform.machine(),
        "python_version": stdlib_platform.python_version(),
        **cpu.get_cpu_info(),
    }


def collect_telemetry() -> dict:
    """Point-in-time metrics matching the backend's TelemetryPayload schema
    exactly (see backend docs/API_REFERENCE.md) - safe to send as-is on
    every heartbeat.
    """

    payload: dict = {"cpu_percent": cpu.get_cpu_percent(interval=0.3)}
    payload.update(ram.get_ram_info())
    payload.update(disk.get_disk_info())
    payload.update(battery.get_battery_info())
    payload.update(network.get_network_info())
    payload["uptime_seconds"] = get_uptime_seconds()
    return payload
