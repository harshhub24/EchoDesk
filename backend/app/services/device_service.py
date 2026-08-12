"""Device lifecycle operations."""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from app.constants import DeviceStatus
from app.extensions import db
from app.models import ApiKey, Device
from app.security.api_keys import format_api_key, generate_api_key
from app.utils.time import utcnow


def register_device(
    owner_id: str,
    device_id: str,
    device_name: str,
    device_type: str,
    hostname: str | None = None,
    operating_system: str | None = None,
) -> Device:
    existing = Device.query.filter_by(owner_id=owner_id, device_id=device_id).first()
    if existing:
        existing.device_name = device_name
        existing.device_type = device_type
        existing.hostname = hostname
        existing.operating_system = operating_system
        existing.last_seen_at = utcnow()
        existing.status = DeviceStatus.ONLINE.value
        db.session.commit()
        return existing

    device = Device(
        uuid=str(uuid4()),
        device_id=device_id,
        owner_id=owner_id,
        device_name=device_name,
        device_type=device_type,
        hostname=hostname,
        operating_system=operating_system,
        status=DeviceStatus.ONLINE.value,
        last_seen_at=utcnow(),
    )
    db.session.add(device)
    db.session.commit()
    return device


def record_heartbeat(device: Device, status: str | None = None, telemetry: dict | None = None) -> Device:
    """Apply a heartbeat to an already-resolved Device instance."""

    device.last_seen_at = utcnow()
    device.status = status or DeviceStatus.ONLINE.value
    if telemetry:
        device.telemetry = telemetry
        device.last_telemetry_at = utcnow()
    db.session.commit()
    return device


def heartbeat_device(owner_id: str, device_id: str, status: str | None = None, telemetry: dict | None = None) -> Device:
    device = Device.query.filter_by(owner_id=owner_id, device_id=device_id).first()
    if not device:
        raise ValueError("Device not found")
    return record_heartbeat(device, status, telemetry)


def issue_device_api_key(device: Device, key_name: str = "agent-key", expires_in_days: int | None = None) -> tuple[ApiKey, str]:
    """Rotate: deactivate any existing keys for this device and mint a new one.

    Returns (ApiKey row, raw_key). The raw key is only ever available here - it
    is not recoverable from the stored hash afterwards.
    """

    ApiKey.query.filter_by(device_id=device.id, is_active=True).update({"is_active": False})

    key_prefix, raw_secret, hashed_secret = generate_api_key()
    expires_at = utcnow() + timedelta(days=expires_in_days) if expires_in_days else None
    api_key = ApiKey(
        user_id=device.owner_id,
        device_id=device.id,
        key_name=key_name,
        key_prefix=key_prefix,
        hashed_secret=hashed_secret,
        expires_at=expires_at,
        is_active=True,
    )
    db.session.add(api_key)
    db.session.commit()
    return api_key, format_api_key(key_prefix, raw_secret)


def revoke_device_api_keys(device: Device) -> int:
    updated = ApiKey.query.filter_by(device_id=device.id, is_active=True).update({"is_active": False})
    db.session.commit()
    return updated


def list_devices(owner_id: str) -> list[Device]:
    return Device.query.filter_by(owner_id=owner_id, is_registered=True).order_by(Device.updated_at.desc()).all()


def get_device(owner_id: str, device_identifier: str) -> Device:
    device = Device.query.filter(
        Device.owner_id == owner_id,
        (Device.id == device_identifier) | (Device.device_id == device_identifier) | (Device.uuid == device_identifier),
    ).first()
    if not device:
        raise ValueError("Device not found")
    return device


def delete_device(device: Device) -> None:
    device.is_registered = False
    device.status = DeviceStatus.OFFLINE.value
    db.session.commit()

