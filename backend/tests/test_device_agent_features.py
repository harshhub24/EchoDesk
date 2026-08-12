"""Tests for the additive Agent-support features:
- Device API key issuance/auth (replaces needing the user's password in the Agent)
- Telemetry-carrying heartbeat
- Command file transfer (upload/list/download)
"""

from __future__ import annotations

import io


def _signup_and_login(client, email="agent-owner@example.com"):
    signup = client.post(
        "/api/v1/signup",
        json={"email": email, "password": "Password123!", "full_name": "Owner"},
    )
    assert signup.status_code == 201, signup.get_json()
    return signup.get_json()["data"]["access_token"]


def _register_device(client, token, device_id="agent-device-1"):
    response = client.post(
        "/api/v1/devices/register",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "device_id": device_id,
            "device_name": "Test Machine",
            "device_type": "linux",
            "hostname": "test-host",
            "operating_system": "Linux Mint 22",
        },
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


def test_issue_and_use_device_api_key(client):
    token = _signup_and_login(client)
    device = _register_device(client, token)

    issue = client.post(
        f"/api/v1/devices/{device['id']}/api-key",
        headers={"Authorization": f"Bearer {token}"},
        json={"key_name": "agent"},
    )
    assert issue.status_code == 201, issue.get_json()
    api_key = issue.get_json()["data"]["api_key"]
    assert "." in api_key

    # Heartbeat using ONLY the device API key - no user credentials involved.
    heartbeat = client.post(
        "/api/v1/devices/heartbeat",
        headers={"X-API-Key": api_key},
        json={"status": "online"},
    )
    assert heartbeat.status_code == 200, heartbeat.get_json()
    assert heartbeat.get_json()["data"]["device_id"] == device["id"]


def test_device_api_key_rejects_bad_key(client):
    token = _signup_and_login(client)
    _register_device(client, token)

    response = client.post(
        "/api/v1/devices/heartbeat",
        headers={"X-API-Key": "bogusprefix.bogussecret"},
        json={"status": "online"},
    )
    assert response.status_code == 401


def test_revoked_api_key_stops_working(client):
    token = _signup_and_login(client)
    device = _register_device(client, token)

    issue = client.post(
        f"/api/v1/devices/{device['id']}/api-key",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    api_key = issue.get_json()["data"]["api_key"]

    revoke = client.delete(
        f"/api/v1/devices/{device['id']}/api-key",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert revoke.status_code == 200
    assert revoke.get_json()["data"]["revoked_count"] == 1

    heartbeat = client.post(
        "/api/v1/devices/heartbeat",
        headers={"X-API-Key": api_key},
        json={"status": "online"},
    )
    assert heartbeat.status_code == 401


def test_heartbeat_with_telemetry_persists_on_device(client):
    token = _signup_and_login(client)
    device = _register_device(client, token)

    heartbeat = client.post(
        "/api/v1/devices/heartbeat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "device_id": device["device_id"],
            "status": "online",
            "telemetry": {
                "cpu_percent": 12.5,
                "ram_percent": 44.2,
                "ram_used_mb": 3400,
                "ram_total_mb": 8192,
                "disk_percent": 61.0,
                "battery_percent": 87.0,
                "battery_charging": True,
                "network_status": "connected",
            },
        },
    )
    assert heartbeat.status_code == 200, heartbeat.get_json()
    assert heartbeat.get_json()["data"]["last_telemetry_at"] is not None

    fetched = client.get(
        f"/api/v1/devices/{device['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert fetched.status_code == 200


def test_legacy_heartbeat_without_telemetry_still_works(client):
    token = _signup_and_login(client)
    device = _register_device(client, token)

    heartbeat = client.post(
        "/api/v1/devices/heartbeat",
        headers={"Authorization": f"Bearer {token}"},
        json={"device_id": device["device_id"], "status": "online"},
    )
    assert heartbeat.status_code == 200


def _create_command(client, token, device_row_id, command_type="FILE_DOWNLOAD_REQUEST"):
    response = client.post(
        "/api/v1/commands",
        headers={"Authorization": f"Bearer {token}"},
        json={"device_id": device_row_id, "command_type": command_type, "payload": {"path": "/tmp/report.txt"}},
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]


def test_device_uploads_file_owner_downloads_it(client):
    token = _signup_and_login(client)
    device = _register_device(client, token)
    issue = client.post(
        f"/api/v1/devices/{device['id']}/api-key",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    api_key = issue.get_json()["data"]["api_key"]

    command = _create_command(client, token, device["id"])

    upload = client.post(
        f"/api/v1/commands/{command['id']}/files",
        headers={"X-API-Key": api_key},
        data={"file": (io.BytesIO(b"hello from the device"), "report.txt")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 201, upload.get_json()
    file_meta = upload.get_json()["data"]
    assert file_meta["direction"] == "device_to_owner"
    assert file_meta["uploaded_by"] == "device"
    assert file_meta["size_bytes"] == len(b"hello from the device")

    listing = client.get(
        f"/api/v1/commands/{command['id']}/files",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listing.status_code == 200
    assert len(listing.get_json()["data"]) == 1

    download = client.get(
        f"/api/v1/commands/{command['id']}/files/{file_meta['id']}/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert download.status_code == 200
    assert download.data == b"hello from the device"


def test_owner_uploads_file_device_downloads_it(client):
    token = _signup_and_login(client)
    device = _register_device(client, token)
    issue = client.post(
        f"/api/v1/devices/{device['id']}/api-key",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    api_key = issue.get_json()["data"]["api_key"]

    command = _create_command(client, token, device["id"], command_type="FILE_UPLOAD_REQUEST")

    upload = client.post(
        f"/api/v1/commands/{command['id']}/files",
        headers={"Authorization": f"Bearer {token}"},
        data={"file": (io.BytesIO(b"deploy this to the device"), "payload.bin")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 201
    file_meta = upload.get_json()["data"]
    assert file_meta["direction"] == "owner_to_device"

    # Device (API key) can download it...
    download = client.get(
        f"/api/v1/commands/{command['id']}/files/{file_meta['id']}/download",
        headers={"X-API-Key": api_key},
    )
    assert download.status_code == 200
    assert download.data == b"deploy this to the device"


def test_device_cannot_download_its_own_upload(client):
    """A device should not be able to fetch a file it itself uploaded via this
    endpoint (that direction is for the owner to retrieve, not for the device
    to read back its own upload)."""

    token = _signup_and_login(client)
    device = _register_device(client, token)
    issue = client.post(
        f"/api/v1/devices/{device['id']}/api-key",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    api_key = issue.get_json()["data"]["api_key"]
    command = _create_command(client, token, device["id"])

    upload = client.post(
        f"/api/v1/commands/{command['id']}/files",
        headers={"X-API-Key": api_key},
        data={"file": (io.BytesIO(b"device data"), "out.txt")},
        content_type="multipart/form-data",
    )
    file_meta = upload.get_json()["data"]

    blocked = client.get(
        f"/api/v1/commands/{command['id']}/files/{file_meta['id']}/download",
        headers={"X-API-Key": api_key},
    )
    assert blocked.status_code == 404


def test_second_device_cannot_access_first_devices_files(client):
    token = _signup_and_login(client)
    device_a = _register_device(client, token, device_id="device-a")
    device_b = _register_device(client, token, device_id="device-b")

    key_a = client.post(
        f"/api/v1/devices/{device_a['id']}/api-key",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    ).get_json()["data"]["api_key"]
    key_b = client.post(
        f"/api/v1/devices/{device_b['id']}/api-key",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    ).get_json()["data"]["api_key"]

    command_a = _create_command(client, token, device_a["id"])

    # Device B tries to poll/act on device A's command via its own key.
    upload = client.post(
        f"/api/v1/commands/{command_a['id']}/files",
        headers={"X-API-Key": key_b},
        data={"file": (io.BytesIO(b"nope"), "nope.txt")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 404

    # Sanity: device A's own key works on its own command.
    upload_ok = client.post(
        f"/api/v1/commands/{command_a['id']}/files",
        headers={"X-API-Key": key_a},
        data={"file": (io.BytesIO(b"yes"), "yes.txt")},
        content_type="multipart/form-data",
    )
    assert upload_ok.status_code == 201


def test_device_api_key_scoped_pending_commands(client):
    token = _signup_and_login(client)
    device_a = _register_device(client, token, device_id="device-a")
    device_b = _register_device(client, token, device_id="device-b")
    key_a = client.post(
        f"/api/v1/devices/{device_a['id']}/api-key",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    ).get_json()["data"]["api_key"]

    _create_command(client, token, device_a["id"], command_type="LOCK")
    _create_command(client, token, device_b["id"], command_type="LOCK")

    pending = client.get("/api/v1/commands/pending", headers={"X-API-Key": key_a})
    assert pending.status_code == 200
    data = pending.get_json()["data"]
    assert len(data) == 1
    assert data[0]["device_id"] == device_a["id"]
