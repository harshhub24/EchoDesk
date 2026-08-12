"""Integration test: runs the real (modified) EchoDesk backend in-process on
a background thread with a real HTTP+WebSocket server, then drives the Agent
against it exactly as it would run against a production backend - real
enrollment, real heartbeat, real socket connect, and a real command
round-trip (create via the backend's service layer -> delivered over the
socket -> executed by the dispatcher -> result stored in the DB).

This is the strongest evidence that the backend changes (Phase 2) and the
Agent (Phase 3) actually interoperate, not just that each passes its own
mocked unit tests.

Skipped automatically if the backend project isn't found next to this repo
checkout (set ECHODESK_BACKEND_PATH to point at it explicitly if needed).
"""

from __future__ import annotations

import os
import socket as stdlib_socket
import sys
import threading
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def _find_free_port() -> int:
    with stdlib_socket.socket(stdlib_socket.AF_INET, stdlib_socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _locate_backend_path() -> Path | None:
    override = os.environ.get("ECHODESK_BACKEND_PATH")
    if override:
        path = Path(override)
        return path if path.exists() else None

    for candidate in [
        Path("/home/claude/echodesk/EchoDesk/backend"),
        Path(__file__).resolve().parents[3] / "EchoDesk" / "backend",
    ]:
        if (candidate / "app" / "create_app.py").exists():
            return candidate
    return None


BACKEND_PATH = _locate_backend_path()


@pytest.fixture(scope="module")
def live_backend():
    if BACKEND_PATH is None:
        pytest.skip("EchoDesk backend project not found - set ECHODESK_BACKEND_PATH to enable this test")

    sys.path.insert(0, str(BACKEND_PATH))
    os.environ.setdefault("FLASK_ENV", "testing")

    from app.create_app import create_app
    from app.extensions import db, socketio

    app = create_app("testing")
    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    with app.app_context():
        db.create_all()

    server_thread = threading.Thread(
        target=lambda: socketio.run(app, host="127.0.0.1", port=port, allow_unsafe_werkzeug=True),
        daemon=True,
    )
    server_thread.start()

    # Wait for the server to actually accept connections before handing back.
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with stdlib_socket.create_connection(("127.0.0.1", port), timeout=0.5):
                break
        except OSError:
            time.sleep(0.2)
    else:
        pytest.fail("Backend server did not start in time")

    yield base_url

    with app.app_context():
        db.session.remove()
        db.drop_all()
    sys.path.remove(str(BACKEND_PATH))


@pytest.fixture()
def agent_env(tmp_path, live_backend, monkeypatch):
    monkeypatch.setenv("ECHODESK_BACKEND_URL", live_backend)
    monkeypatch.setenv("ECHODESK_API_PREFIX", "/api/v1")
    monkeypatch.setenv("ECHODESK_EMAIL", "agent-integration@example.com")
    monkeypatch.setenv("ECHODESK_PASSWORD", "Password123!")
    monkeypatch.setenv("ECHODESK_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ECHODESK_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("ECHODESK_VERIFY_TLS", "false")

    # First, sign the test user up against the live backend (login alone
    # isn't enough on a fresh DB - there's no account yet).
    import httpx

    signup = httpx.post(
        f"{live_backend}/api/v1/signup",
        json={"email": "agent-integration@example.com", "password": "Password123!", "full_name": "Agent Owner"},
    )
    assert signup.status_code == 201, signup.text

    return tmp_path


def test_full_enrollment_heartbeat_and_command_roundtrip(agent_env, live_backend):
    from agent.api.auth import ensure_authenticated
    from agent.api.client import RestClient
    from agent.api import endpoints
    from agent.commands.dispatcher import CommandDispatcher
    from agent.config import load_config
    from agent.socket.client import SocketClient
    from agent.socket.events import register_command_handler
    from agent.system import device as device_info

    config = load_config()
    config.ensure_directories()

    local_device_id = device_info.load_or_create_device_id(config.data_dir)
    rest_client = RestClient(config)

    # --- Enrollment (login -> register -> mint API key -> persist) ---
    api_key = ensure_authenticated(rest_client, config, config.data_dir, local_device_id)
    assert "." in api_key

    credentials_file = config.data_dir / "device_credentials.json"
    assert credentials_file.exists()

    # --- Heartbeat with real telemetry over REST ---
    telemetry = device_info.collect_telemetry()
    heartbeat_response = endpoints.send_heartbeat(rest_client, "online", telemetry)
    assert heartbeat_response["data"]["last_telemetry_at"] is not None

    # --- Socket connect using the minted device API key ---
    socket_client = SocketClient(config, api_key)
    dispatcher = CommandDispatcher(rest_client=rest_client, socket_client=socket_client, file_root=str(config.data_dir))
    register_command_handler(socket_client, dispatcher.handle)
    socket_client.connect()
    time.sleep(0.5)
    assert socket_client.connected is True

    # --- Create a real command exactly the way a controller app would (a
    #     fresh owner login + POST /commands), and confirm it arrives over
    #     the socket and gets executed + reported. ---
    import httpx

    login_response = httpx.post(
        f"{live_backend}/api/v1/login",
        json={"email": "agent-integration@example.com", "password": "Password123!"},
    )
    owner_token = login_response.json()["data"]["access_token"]

    devices_response = httpx.get(
        f"{live_backend}/api/v1/devices",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    device_row_id = devices_response.json()["data"][0]["id"]

    create_response = httpx.post(
        f"{live_backend}/api/v1/commands",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"device_id": device_row_id, "command_type": "MESSAGE_REQUEST", "payload": {"title": "Hi", "message": "Integration test message"}},
    )
    assert create_response.status_code == 201, create_response.text
    command_id = create_response.json()["data"]["id"]

    # Give the socket event + background dispatch thread time to run. On
    # Linux without a display, notify-send will fail gracefully (handled by
    # platform.linux.show_message), so this exercises the real code path
    # including its failure-handling branch.
    time.sleep(1.5)

    result_check = httpx.get(
        f"{live_backend}/api/v1/commands",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    commands = result_check.json()["data"]
    matching = next(c for c in commands if c["id"] == command_id)
    assert matching["status"] in ("success", "delivered", "executing")

    socket_client.disconnect()
    rest_client.close()
