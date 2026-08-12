"""Standalone script exercising a real backend + the real Controller
services end-to-end. Run as a subprocess (see test_integration_backend.py)
rather than imported in-process, because the backend and Controller
projects happen to both use the top-level package name `app` - importing
both into the same interpreter corrupts module state for whichever project
imports second (proven the hard way: it broke unrelated TokenManager unit
tests running later in the same pytest session). A subprocess gives full
interpreter isolation with no such risk.

Usage: python _integration_backend_script.py <backend_path> <controller_path>
Exits 0 and prints "INTEGRATION TEST PASSED" on success.
"""

from __future__ import annotations

import socket as stdlib_socket
import sys
import threading
import time

backend_path, controller_path = sys.argv[1], sys.argv[2]

sys.path.insert(0, backend_path)
import os

os.environ["FLASK_ENV"] = "testing"
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from app.create_app import create_app as create_backend_app
from app.extensions import db as backend_db, socketio as backend_socketio

backend_app = create_backend_app("testing")
with backend_app.app_context():
    backend_db.create_all()


def find_free_port() -> int:
    with stdlib_socket.socket(stdlib_socket.AF_INET, stdlib_socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


port = find_free_port()
base_url = f"http://127.0.0.1:{port}"

threading.Thread(
    target=lambda: backend_socketio.run(backend_app, host="127.0.0.1", port=port, allow_unsafe_werkzeug=True),
    daemon=True,
).start()

deadline = time.time() + 10
while time.time() < deadline:
    try:
        with stdlib_socket.create_connection(("127.0.0.1", port), timeout=0.5):
            break
    except OSError:
        time.sleep(0.2)
else:
    raise RuntimeError("Backend did not start in time")

import requests

signup = requests.post(
    f"{base_url}/api/v1/signup",
    json={"email": "controller-integration@example.com", "password": "Password123!", "full_name": "Controller Owner"},
)
assert signup.status_code == 201, signup.text

# Fully switch the `app` namespace to the Controller before importing
# anything from it.
for mod_name in list(sys.modules):
    if mod_name == "app" or mod_name.startswith("app."):
        del sys.modules[mod_name]
sys.path.remove(backend_path)
sys.path.insert(0, controller_path)
os.chdir(controller_path)

os.environ["ECHODESK_BACKEND_URL"] = base_url
os.environ["ECHODESK_DATA_DIR"] = "/tmp/controller_integration_test_data"
os.environ["ECHODESK_LOG_DIR"] = "/tmp/controller_integration_test_data/logs"

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from app.config import load_config
from app.services import AppState
from app.api import endpoints
from app.services.device_service import DeviceListService
from app.services.command_service import CommandService

config = load_config()
config.ensure_directories()

app = QApplication([])
app_state = AppState(config)

results: dict = {}


def do_login():
    app_state.login("controller-integration@example.com", "Password123!", remember=False)


app_state.login_succeeded.connect(lambda session: results.setdefault("session", session))
app_state.login_failed.connect(lambda msg: results.setdefault("login_error", msg))


def register_device_and_send_command():
    if "session" not in results:
        results["failure"] = f"login did not succeed: {results.get('login_error')}"
        app.quit()
        return

    # Registering a device is the Agent's job, not the Controller's - the
    # Controller has no `register_device` wrapper (see
    # docs/PHASE_1_ANALYSIS.md). Register directly via REST here, exactly
    # as a real Agent would, so the Controller then has a real device to
    # list/command against.
    register_response = requests.post(
        f"{base_url}/api/v1/devices/register",
        headers={"Authorization": f"Bearer {app_state.rest_client.access_token}"},
        json={"device_id": "integration-dev-1", "device_name": "Integration Device", "device_type": "linux", "hostname": "int-host", "operating_system": "Linux Mint 22"},
    )
    assert register_response.status_code == 201, register_response.text
    results["device_row_id"] = register_response.json()["data"]["id"]

    device_service = DeviceListService(app_state)
    device_service.devices_updated.connect(lambda devices: results.setdefault("devices", devices))
    device_service.refresh()

    command_service = CommandService(app_state)
    command_service.command_created.connect(lambda c: results.setdefault("command", c))
    command_service.send_command(results["device_row_id"], "LOCK", {})
    results["command_service"] = command_service  # keep alive


def do_file_transfer_roundtrip():
    if "device_row_id" not in results:
        results["failure"] = "device registration did not complete"
        app.quit()
        return

    device_row_id = results["device_row_id"]
    key_response = endpoints.issue_device_api_key(app_state.rest_client, device_row_id)
    device_api_key = key_response["data"]["api_key"]

    download_cmd_response = endpoints.create_command(app_state.rest_client, device_row_id, "FILE_DOWNLOAD_REQUEST", {"path": "/tmp/report.txt"})
    command_id = download_cmd_response["data"]["id"]

    device_upload_response = requests.post(
        f"{base_url}/api/v1/commands/{command_id}/files",
        headers={"X-API-Key": device_api_key},
        files={"file": ("report.txt", b"integration test file content", "text/plain")},
    )
    assert device_upload_response.status_code == 201, device_upload_response.text

    files = endpoints.list_command_files(app_state.rest_client, command_id)
    results["files"] = files
    if files:
        content = endpoints.download_command_file(app_state.rest_client, command_id, files[0]["id"])
        results["downloaded_content"] = content

    app.quit()


QTimer.singleShot(500, do_login)
QTimer.singleShot(2000, register_device_and_send_command)
QTimer.singleShot(4000, do_file_transfer_roundtrip)
app.exec()

app_state.shutdown()

if "failure" in results:
    print(f"INTEGRATION TEST FAILED: {results['failure']}")
    sys.exit(1)

assert "session" in results, "login did not succeed"
assert results.get("devices") and results["devices"][0].device_name == "Integration Device", results.get("devices")
assert results.get("command") is not None and results["command"].command_type == "LOCK", results.get("command")
assert results.get("files") and len(results["files"]) == 1, results.get("files")
assert results.get("downloaded_content") == b"integration test file content", results.get("downloaded_content")

print("INTEGRATION TEST PASSED")
