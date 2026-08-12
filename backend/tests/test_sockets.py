"""Socket baseline and device API-key auth tests."""

from __future__ import annotations

from app.extensions import socketio


def test_websocket_api_surface(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def _issue_device_and_key(client):
    signup = client.post(
        "/api/v1/signup",
        json={"email": "socket-owner@example.com", "password": "Password123!", "full_name": "Owner"},
    )
    token = signup.get_json()["data"]["access_token"]

    register = client.post(
        "/api/v1/devices/register",
        headers={"Authorization": f"Bearer {token}"},
        json={"device_id": "socket-device", "device_name": "Socket Device", "device_type": "linux"},
    )
    device_id = register.get_json()["data"]["id"]

    issue = client.post(
        f"/api/v1/devices/{device_id}/api-key",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    return device_id, issue.get_json()["data"]["api_key"]


def test_socket_connect_with_device_api_key(app, client):
    device_id, api_key = _issue_device_and_key(client)

    with app.app_context():
        sio_client = socketio.test_client(app, flask_test_client=client, auth={"api_key": api_key})
        try:
            received = sio_client.get_received()
            event_names = [event["name"] for event in received]
            assert "connected" in event_names
            assert "registered" in event_names
            registered_event = next(event for event in received if event["name"] == "registered")
            assert registered_event["args"][0]["device_id"] == device_id
        finally:
            sio_client.disconnect()


def test_socket_connect_with_bad_api_key_is_rejected(app, client):
    with app.app_context():
        sio_client = socketio.test_client(app, flask_test_client=client, auth={"api_key": "bad.key"})
        try:
            assert not sio_client.is_connected()
        finally:
            if sio_client.is_connected():
                sio_client.disconnect()


def test_socket_heartbeat_via_api_key_carries_telemetry(app, client):
    device_id, api_key = _issue_device_and_key(client)

    with app.app_context():
        sio_client = socketio.test_client(app, flask_test_client=client, auth={"api_key": api_key})
        try:
            sio_client.get_received()  # drain connect/registered
            sio_client.emit("heartbeat", {"status": "online", "telemetry": {"cpu_percent": 10.0, "ram_percent": 55.0}})
            received = sio_client.get_received()
            ack = next(event for event in received if event["name"] == "heartbeat_ack")
            assert ack["args"][0]["success"] is True
            assert ack["args"][0]["device_id"] == device_id
        finally:
            sio_client.disconnect()
