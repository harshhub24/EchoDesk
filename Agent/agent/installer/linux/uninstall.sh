#!/usr/bin/env bash
# EchoDesk Agent - Linux uninstaller.
#
# Usage: sudo ./uninstall.sh
# Stops and removes the systemd service. Does NOT delete the project files,
# your .env, or any local device credentials - remove those manually if
# you're fully decommissioning this device.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root (sudo ./uninstall.sh)." >&2
    exit 1
fi

PYTHON_BIN="$INSTALL_DIR/venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
    PYTHON_BIN="$(command -v python3)"
fi

"$PYTHON_BIN" -c "
from agent.services import linux_service
linux_service.uninstall()
"

echo "Service removed. To fully decommission this device, also consider:"
echo "  - Revoking its API key from the owner account (DELETE /devices/{id}/api-key)"
echo "  - Deleting $INSTALL_DIR/agent/device_credentials.json"
echo "  - Deleting the project directory: $INSTALL_DIR"
