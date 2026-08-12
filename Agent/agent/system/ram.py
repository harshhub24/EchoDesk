"""RAM telemetry."""

from __future__ import annotations

import psutil

_MB = 1024 * 1024


def get_ram_info() -> dict:
    vm = psutil.virtual_memory()
    return {
        "ram_percent": vm.percent,
        "ram_used_mb": round(vm.used / _MB, 1),
        "ram_total_mb": round(vm.total / _MB, 1),
    }
