"""Integration test: runs the real (modified) EchoDesk backend and the real
Controller services against it end-to-end. Executed as a subprocess (see
_integration_backend_script.py's docstring for why - the backend and
Controller projects both use the top-level package name `app`, and
importing both into one interpreter corrupts module state for whichever
project imports second, which broke unrelated unit tests running later in
the same pytest session the first time this was tried in-process).

Skipped automatically if the backend project isn't found (set
ECHODESK_BACKEND_PATH to point at it explicitly if needed).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

CONTROLLER_PATH = Path(__file__).resolve().parent.parent


def _locate_backend_path() -> Path | None:
    override = os.environ.get("ECHODESK_BACKEND_PATH")
    if override:
        path = Path(override)
        return path if path.exists() else None

    for candidate in [Path("/home/claude/echodesk/EchoDesk/backend")]:
        if (candidate / "app" / "create_app.py").exists():
            return candidate
    return None


def test_full_login_devices_command_file_roundtrip():
    backend_path = _locate_backend_path()
    if backend_path is None:
        pytest.skip("EchoDesk backend project not found - set ECHODESK_BACKEND_PATH to enable this test")

    script_path = Path(__file__).resolve().parent / "_integration_backend_script.py"

    result = subprocess.run(
        [sys.executable, str(script_path), str(backend_path), str(CONTROLLER_PATH)],
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
    )

    print(result.stdout)
    print(result.stderr)

    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    assert "INTEGRATION TEST PASSED" in result.stdout
