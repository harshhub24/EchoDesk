"""Battery telemetry. Desktops without a battery report None cleanly."""

from __future__ import annotations

import psutil


def get_battery_info() -> dict:
    try:
        battery = psutil.sensors_battery()
    except Exception:
        battery = None

    if battery is None:
        return {"battery_percent": None, "battery_charging": None}

    return {
        "battery_percent": round(battery.percent, 1),
        "battery_charging": bool(battery.power_plugged),
    }
