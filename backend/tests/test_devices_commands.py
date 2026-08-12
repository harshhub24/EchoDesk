from __future__ import annotations


def test_device_registration_and_command_creation(client):
    signup_response = client.post(
        "/api/v1/signup",
        json={"email": "controller@example.com", "password": "StrongPass123!", "full_name": "Controller User"},
    )
    access_token = signup_response.get_json()["data"]["access_token"]

    device_response = client.post(
        "/api/v1/devices/register",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "device_id": "device-001",
            "device_name": "Office Laptop",
            "device_type": "windows-desktop",
            "hostname": "office-laptop",
            "operating_system": "Windows 11",
        },
    )
    device_payload = device_response.get_json()

    assert device_response.status_code == 201
    device_id = device_payload["data"]["id"]

    command_response = client.post(
        "/api/v1/commands",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"device_id": device_id, "command_type": "MESSAGE_REQUEST", "payload": {"message": "Hello"}},
    )
    command_payload = command_response.get_json()

    assert command_response.status_code == 201
    assert command_payload["data"]["command_type"] == "MESSAGE_REQUEST"
