"""Endpoint wrappers - one function per backend REST route the Controller
uses. Matches docs/PHASE_1_ANALYSIS.md exactly; never invents a route.
"""

from __future__ import annotations

from app.api.client import RestClient


# --- Auth --------------------------------------------------------------------------

def signup(client: RestClient, email: str, password: str, full_name: str) -> dict:
    return client.post("/signup", {"email": email, "password": password, "full_name": full_name})


def login(client: RestClient, email: str, password: str) -> dict:
    return client.post("/login", {"email": email, "password": password})


def refresh_tokens(client: RestClient) -> dict:
    return client.post("/refresh", use_refresh_token=True)


def logout(client: RestClient, refresh_token: str | None = None) -> dict:
    body = {"refresh_token": refresh_token} if refresh_token else None
    return client.post("/logout", body)


def change_password(client: RestClient, current_password: str, new_password: str) -> dict:
    return client.post("/change-password", {"current_password": current_password, "new_password": new_password})


# --- Profile -----------------------------------------------------------------------

def get_profile(client: RestClient) -> dict:
    return client.get("/profile")


def update_profile(client: RestClient, **fields) -> dict:
    return client.put("/profile", fields)


# --- Devices -----------------------------------------------------------------------

def list_devices(client: RestClient) -> list[dict]:
    return client.get("/devices").get("data", [])


def get_device(client: RestClient, device_identifier: str) -> dict:
    return client.get(f"/devices/{device_identifier}").get("data", {})


def delete_device(client: RestClient, device_identifier: str) -> dict:
    return client.delete(f"/devices/{device_identifier}")


def issue_device_api_key(client: RestClient, device_identifier: str, key_name: str = "agent", expires_in_days: int | None = None) -> dict:
    body = {"key_name": key_name}
    if expires_in_days:
        body["expires_in_days"] = expires_in_days
    return client.post(f"/devices/{device_identifier}/api-key", body)


def revoke_device_api_key(client: RestClient, device_identifier: str) -> dict:
    return client.delete(f"/devices/{device_identifier}/api-key")


# --- Commands ----------------------------------------------------------------------

def create_command(client: RestClient, device_row_id: str, command_type: str, payload: dict | None = None) -> dict:
    return client.post("/commands", {"device_id": device_row_id, "command_type": command_type, "payload": payload or {}})


def list_commands(client: RestClient) -> list[dict]:
    return client.get("/commands").get("data", [])


# --- Command files -------------------------------------------------------------------

def upload_command_file(client: RestClient, command_id: str, filename: str, content: bytes, content_type: str = "application/octet-stream") -> dict:
    return client.upload_file(f"/commands/{command_id}/files", filename, content, content_type)


def list_command_files(client: RestClient, command_id: str) -> list[dict]:
    return client.get(f"/commands/{command_id}/files").get("data", [])


def download_command_file(client: RestClient, command_id: str, file_id: str) -> bytes:
    return client.download_file(f"/commands/{command_id}/files/{file_id}/download")


def delete_command_file(client: RestClient, command_id: str, file_id: str) -> dict:
    return client.delete(f"/commands/{command_id}/files/{file_id}")


# --- Activity & notifications --------------------------------------------------------

def list_activity(client: RestClient) -> list[dict]:
    return client.get("/activity").get("data", [])


def list_notifications(client: RestClient) -> list[dict]:
    return client.get("/notifications").get("data", [])


# --- Health ---------------------------------------------------------------------------

def health_check(client: RestClient) -> dict:
    return client.get("/health")
