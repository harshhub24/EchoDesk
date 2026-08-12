"""Device API tests."""

from __future__ import annotations

from app.extensions import db
from app.models import User
from app.security.passwords import hash_password


def _login_token(client):
    signup = client.post(
        "/api/v1/signup",
        json={"email": "device-owner@example.com", "password": "Password123!", "full_name": "Owner"},
    )
    return signup.get_json()["data"]["access_token"]


def test_register_device(client):
    token = _login_token(client)
    response = client.post(
        "/api/v1/devices/register",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "device_id": "device-1",
            "device_name": "Work Laptop",
            "device_type": "windows",
            "hostname": "workstation",
            "operating_system": "Windows 11",
        },
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["device_id"] == "device-1"
