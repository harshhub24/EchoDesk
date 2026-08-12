"""Endpoint wrappers. One function per backend route the Agent calls - never
invents new routes or renames existing ones (see backend docs/API_REFERENCE.md).
"""

from __future__ import annotations

from agent.api.client import RestClient


def login(client: RestClient, email: str, password: str) -> dict:
    return client.post("/login", {"email": email, "password": password})


def register_device(client: RestClient, device_id: str, device_name: str, device_type: str, hostname: str | None, operating_system: str | None) -> dict:
    return client.post(
        "/devices/register",
        {
            "device_id": device_id,
            "device_name": device_name,
            "device_type": device_type,
            "hostname": hostname,
            "operating_system": operating_system,
        },
    )


def issue_device_api_key(client: RestClient, backend_device_row_id: str, key_name: str = "agent") -> dict:
    return client.post(f"/devices/{backend_device_row_id}/api-key", {"key_name": key_name})


def send_heartbeat(client: RestClient, status: str, telemetry: dict, device_id: str | None = None) -> dict:
    body: dict = {"status": status, "telemetry": telemetry}
    if device_id:
        # Only needed on the legacy user-JWT auth path; harmless to omit
        # when authenticated with a device API key.
        body["device_id"] = device_id
    return client.post("/devices/heartbeat", body)


def fetch_pending_commands(client: RestClient) -> list[dict]:
    response = client.get("/commands/pending")
    return response.get("data", [])


def upload_command_file(client: RestClient, command_id: str, filename: str, content: bytes, content_type: str = "application/octet-stream") -> dict:
    return client.upload_file(f"/commands/{command_id}/files", filename, content, content_type)


def list_command_files(client: RestClient, command_id: str) -> list[dict]:
    response = client.get(f"/commands/{command_id}/files")
    return response.get("data", [])


def download_command_file(client: RestClient, command_id: str, file_id: str) -> bytes:
    return client.download_file(f"/commands/{command_id}/files/{file_id}/download")


def health_check(client: RestClient) -> dict:
    return client.get("/health")
