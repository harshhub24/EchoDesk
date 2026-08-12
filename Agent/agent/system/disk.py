"""Disk telemetry."""

from __future__ import annotations

import psutil

from agent.platform.common import current_platform
from agent.constants import Platform

_GB = 1024 * 1024 * 1024


def _root_path() -> str:
    return "C:\\" if current_platform() == Platform.WINDOWS else "/"


def get_disk_info() -> dict:
    usage = psutil.disk_usage(_root_path())
    return {
        "disk_percent": usage.percent,
        "disk_used_gb": round(usage.used / _GB, 1),
        "disk_total_gb": round(usage.total / _GB, 1),
    }
