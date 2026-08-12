#!/usr/bin/env bash
# EchoDesk Agent - Linux installer.
#
# Usage: sudo ./install.sh
#
# Expects to be run from inside agent/installer/linux/ of an already-placed
# project copy (i.e. you've already copied the whole project - the directory
# containing run.py and agent/ - to its final location before running this).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"   # .../installer/linux -> repo root
AGENT_DIR="$INSTALL_DIR/agent"

echo "EchoDesk Agent installer"
echo "Install directory: $INSTALL_DIR"

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root (sudo ./install.sh)." >&2
    exit 1
fi

if [[ ! -f "$AGENT_DIR/.env" ]]; then
    if [[ -f "$AGENT_DIR/.env.example" ]]; then
        echo "No agent/.env found - copying from .env.example."
        echo "You MUST edit agent/.env before the Agent can connect (backend URL + credentials)."
        cp "$AGENT_DIR/.env.example" "$AGENT_DIR/.env"
    else
        echo "WARNING: agent/.env and agent/.env.example both missing - create agent/.env manually." >&2
    fi
fi

PYTHON_BIN="$(command -v python3 || true)"
if [[ -z "$PYTHON_BIN" ]]; then
    echo "python3 is required but was not found on PATH." >&2
    exit 1
fi

echo "Creating virtual environment..."
"$PYTHON_BIN" -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip --quiet
"$INSTALL_DIR/venv/bin/pip" install -r "$AGENT_DIR/requirements.txt" --quiet

echo "Installing systemd service..."
"$INSTALL_DIR/venv/bin/python" -c "
from pathlib import Path
from agent.services import linux_service
linux_service.install(Path('$INSTALL_DIR'), python_executable='$INSTALL_DIR/venv/bin/python')
"

echo ""
echo "Done. Check status with: systemctl status echodesk-agent"
echo "Follow logs with:        journalctl -u echodesk-agent -f"
echo "Or:                      tail -f $AGENT_DIR/logs/agent.log"
