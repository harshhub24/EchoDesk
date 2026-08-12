"""Command API tests."""

from __future__ import annotations

from app.extensions import db
from app.models import Device


def test_create_command(client, app):
    signup = client.post(
        "/api/v1/signup",
        json={"email": "cmd-owner@example.com", "password": "Password123!", "full_name": "Owner"},
    )
    token = signup.get_json()["data"]["access_token"]

    with app.app_context():
        user_id = signup.get_json()["data"]["user_id"]
        device = Device(
            uuid="uuid-1",
            device_id="device-1",
            owner_id=user_id,
            device_name="Device",
            device_type="windows",
            status="online",
        )
        db.session.add(device)
        db.session.commit()
        device_id = device.id

    response = client.post(
        "/api/v1/commands",
        headers={"Authorization": f"Bearer {token}"},
        json={"device_id": device_id, "command_type": "LOCK", "payload": {"reason": "policy"}},
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["command_type"] == "LOCK"
