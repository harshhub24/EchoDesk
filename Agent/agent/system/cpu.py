"""CPU telemetry."""

from __future__ import annotations

import platform as stdlib_platform

import psutil


def get_cpu_percent(interval: float = 0.5) -> float:
    return psutil.cpu_percent(interval=interval)


def get_cpu_info() -> dict:
    return {
        "processor": stdlib_platform.processor() or stdlib_platform.machine(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "architecture": stdlib_platform.machine(),
    }
