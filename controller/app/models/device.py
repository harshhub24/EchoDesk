"""Device model - mirrors backend DeviceResponse exactly (see
docs/PHASE_1_ANALYSIS.md §2). Plain dataclass, not an ORM model.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Telemetry:
    cpu_percent: float | None = None
    ram_percent: float | None = None
    ram_used_mb: float | None = None
    ram_total_mb: float | None = None
    disk_percent: float | None = None
    disk_used_gb: float | None = None
    disk_total_gb: float | None = None
    battery_percent: float | None = None
    battery_charging: bool | None = None
    network_status: str | None = None
    ip_address: str | None = None
    mac_address: str | None = None
    uptime_seconds: int | None = None

    @classmethod
    def from_dict(cls, data: dict | None) -> "Telemetry":
        data = data or {}
        known_fields = {f for f in cls.__dataclass_fields__}
        return cls(**{key: value for key, value in data.items() if key in known_fields})


@dataclass
class Device:
    id: str
    uuid: str
    device_id: str
    device_name: str
    device_type: str
    hostname: str | None = None
    operating_system: str | None = None
    status: str = "unknown"
    last_seen_at: str | None = None
    telemetry: Telemetry = field(default_factory=Telemetry)
    last_telemetry_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Device":
        return cls(
            id=data["id"],
            uuid=data.get("uuid", ""),
            device_id=data["device_id"],
            device_name=data.get("device_name", ""),
            device_type=data.get("device_type", ""),
            hostname=data.get("hostname"),
            operating_system=data.get("operating_system"),
            status=data.get("status", "unknown"),
            last_seen_at=data.get("last_seen_at"),
            telemetry=Telemetry.from_dict(data.get("telemetry")),
            last_telemetry_at=data.get("last_telemetry_at"),
        )

    @property
    def is_online(self) -> bool:
        return self.status == "online"
