"""Device schemas."""

from __future__ import annotations

from pydantic import Field

from .common import ApiSchema


class DeviceRegisterRequest(ApiSchema):
    device_id: str = Field(min_length=3, max_length=128)
    device_name: str = Field(min_length=1, max_length=255)
    device_type: str = Field(min_length=1, max_length=64)
    hostname: str | None = Field(default=None, max_length=255)
    operating_system: str | None = Field(default=None, max_length=255)


class TelemetryPayload(ApiSchema):
    """Structured point-in-time device metrics sent alongside a heartbeat."""

    cpu_percent: float | None = Field(default=None, ge=0, le=100)
    ram_percent: float | None = Field(default=None, ge=0, le=100)
    ram_used_mb: float | None = Field(default=None, ge=0)
    ram_total_mb: float | None = Field(default=None, ge=0)
    disk_percent: float | None = Field(default=None, ge=0, le=100)
    disk_used_gb: float | None = Field(default=None, ge=0)
    disk_total_gb: float | None = Field(default=None, ge=0)
    battery_percent: float | None = Field(default=None, ge=0, le=100)
    battery_charging: bool | None = None
    network_status: str | None = Field(default=None, max_length=32)
    ip_address: str | None = Field(default=None, max_length=64)
    mac_address: str | None = Field(default=None, max_length=64)
    uptime_seconds: int | None = Field(default=None, ge=0)


class DeviceHeartbeatRequest(ApiSchema):
    # device_id is optional when authenticating with a device-scoped API key
    # (the key already identifies exactly one device); required on the legacy
    # user-JWT path since that path can address any of the caller's devices.
    device_id: str | None = Field(default=None, min_length=3, max_length=128)
    status: str | None = Field(default=None, max_length=32)
    telemetry: TelemetryPayload | None = None


class DeviceResponse(ApiSchema):
    id: str
    uuid: str
    device_id: str
    device_name: str
    device_type: str
    hostname: str | None
    operating_system: str | None
    status: str
    last_seen_at: str | None = None
    telemetry: dict | None = None
    last_telemetry_at: str | None = None


class DeviceApiKeyRequest(ApiSchema):
    key_name: str = Field(default="agent-key", min_length=1, max_length=255)
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)


class DeviceApiKeyResponse(ApiSchema):
    api_key: str
    key_prefix: str
    device_id: str
    expires_at: str | None = None
