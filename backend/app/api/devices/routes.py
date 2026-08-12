"""Device routes."""

from __future__ import annotations

from flask import Blueprint, g, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Device, User
from app.schemas.devices import (
    DeviceApiKeyRequest,
    DeviceHeartbeatRequest,
    DeviceRegisterRequest,
)
from app.security.device_auth import device_auth_required
from app.services.device_service import (
    delete_device,
    get_device,
    heartbeat_device,
    issue_device_api_key,
    record_heartbeat,
    revoke_device_api_keys,
    list_devices,
    register_device,
)
from app.utils.responses import error_response, success_response


devices_bp = Blueprint("devices", __name__)


def _device_to_dict(device: Device) -> dict:
    """Single source of truth for the device response shape - used by both
    GET /devices and GET /devices/{id} so they never drift out of sync
    (they did, once: telemetry/last_telemetry_at were added to the Device
    model and DeviceResponse schema but these two routes built their dicts
    by hand and were never updated - caught by the Desktop Controller's
    live integration test showing blank telemetry on Device Details).
    """

    return {
        "id": device.id,
        "uuid": device.uuid,
        "device_id": device.device_id,
        "device_name": device.device_name,
        "device_type": device.device_type,
        "hostname": device.hostname,
        "operating_system": device.operating_system,
        "status": device.status,
        "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
        "telemetry": device.telemetry or {},
        "last_telemetry_at": device.last_telemetry_at.isoformat() if device.last_telemetry_at else None,
    }


@devices_bp.post("/devices/register")
@jwt_required()
def register_device_route():
    user = db.session.get(User, get_jwt_identity())
    if not user:
        return error_response("User not found", status_code=404)
    payload = DeviceRegisterRequest.model_validate(request.get_json(force=True)).model_dump()
    device = register_device(user.id, **payload)
    return success_response(
        "Device registered",
        {
            "id": device.id,
            "uuid": device.uuid,
            "device_id": device.device_id,
            "device_name": device.device_name,
            "device_type": device.device_type,
            "status": device.status,
        },
        201,
    )


@devices_bp.get("/devices")
@jwt_required()
def list_devices_route():
    user_id = get_jwt_identity()
    devices = list_devices(str(user_id))
    return success_response(
        "Devices retrieved",
        [_device_to_dict(device) for device in devices],
    )


@devices_bp.get("/devices/<string:device_identifier>")
@jwt_required()
def get_device_route(device_identifier: str):
    user_id = str(get_jwt_identity())
    try:
        device = get_device(user_id, device_identifier)
    except ValueError as error:
        return error_response(str(error), status_code=404)
    return success_response(
        "Device retrieved",
        _device_to_dict(device),
    )


@devices_bp.delete("/devices/<string:device_identifier>")
@jwt_required()
def delete_device_route(device_identifier: str):
    user_id = str(get_jwt_identity())
    try:
        device = get_device(user_id, device_identifier)
    except ValueError as error:
        return error_response(str(error), status_code=404)
    delete_device(device)
    return success_response("Device deleted")


@devices_bp.post("/devices/heartbeat")
@device_auth_required
def heartbeat_route():
    data = DeviceHeartbeatRequest.model_validate(request.get_json(force=True)).model_dump()
    telemetry = data.get("telemetry") or None

    if g.current_device is not None:
        # Authenticated via device API key: the key already identifies the device.
        device = record_heartbeat(g.current_device, data.get("status"), telemetry)
    else:
        # Legacy path: authenticated via the owning user's JWT, device_id required.
        if not data.get("device_id"):
            return error_response("device_id is required", status_code=400)
        try:
            device = heartbeat_device(str(g.current_user.id), data["device_id"], data.get("status"), telemetry)
        except ValueError as error:
            return error_response(str(error), status_code=404)

    return success_response(
        "Heartbeat recorded",
        {"device_id": device.id, "status": device.status, "last_telemetry_at": device.last_telemetry_at.isoformat() if device.last_telemetry_at else None},
    )


@devices_bp.post("/devices/<string:device_identifier>/api-key")
@jwt_required()
def issue_device_api_key_route(device_identifier: str):
    """Owner-only: mint (or rotate) a device-scoped API key for the Agent to use.

    The raw key is returned exactly once here and cannot be retrieved again -
    only re-issued (which immediately invalidates the previous key).
    """

    user_id = str(get_jwt_identity())
    try:
        device = get_device(user_id, device_identifier)
    except ValueError as error:
        return error_response(str(error), status_code=404)

    payload = DeviceApiKeyRequest.model_validate(request.get_json(silent=True) or {}).model_dump()
    api_key, raw_key = issue_device_api_key(device, payload["key_name"], payload.get("expires_in_days"))
    return success_response(
        "Device API key issued",
        {
            "api_key": raw_key,
            "key_prefix": api_key.key_prefix,
            "device_id": device.id,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
        },
        201,
    )


@devices_bp.delete("/devices/<string:device_identifier>/api-key")
@jwt_required()
def revoke_device_api_key_route(device_identifier: str):
    """Owner-only: revoke all active API keys for a device."""

    user_id = str(get_jwt_identity())
    try:
        device = get_device(user_id, device_identifier)
    except ValueError as error:
        return error_response(str(error), status_code=404)

    revoked = revoke_device_api_keys(device)
    return success_response("Device API keys revoked", {"device_id": device.id, "revoked_count": revoked})

