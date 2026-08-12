# EchoDesk Device Agent

Cross-platform (Linux Mint primary, Windows 10/11 secondary) background
service that registers a device with your EchoDesk backend, sends periodic
telemetry heartbeats, and executes remote commands you issue from your own
account (lock/restart/shutdown/sleep/hibernate/logout, on-screen messages,
file browsing/transfer, screenshots).

This is a personal remote device management client for devices you own and
explicitly authorize. It runs as a visible, authorized background service -
no stealth, no hidden execution, no credential harvesting, no surveillance
beyond what you explicitly request via commands.

## Quick start

```bash
# From the directory containing run.py and agent/:
python3 -m venv venv
source venv/bin/activate          # venv\Scripts\activate on Windows
pip install -r agent/requirements.txt

cp agent/.env.example agent/.env
# edit agent/.env: set ECHODESK_BACKEND_URL and either
#   ECHODESK_API_KEY (pre-provisioned), or
#   ECHODESK_EMAIL + ECHODESK_PASSWORD (one-time bootstrap enrollment)

python run.py
```

**Important:** always start via `run.py` (or `python -m agent.main` from
this directory), never `python agent/main.py` directly - see `run.py`'s
docstring for why (it's not just style: running it the other way can break
several dependencies).

For a permanent background service, see `agent/docs/INSTALLATION.md`.

## How authentication works

Two options, matching the backend's device-auth support (see
`agent/docs/API_INTEGRATION.md`):

1. **Pre-provisioned API key (recommended):** the device owner mints a
   device-scoped key via the backend (`POST /devices/{id}/api-key`) and puts
   it in `ECHODESK_API_KEY`. The Agent never sees the account password.
2. **One-time bootstrap:** set `ECHODESK_EMAIL`/`ECHODESK_PASSWORD`. On first
   run the Agent logs in once, registers the device, mints its own API key,
   and saves it to `agent/device_credentials.json` (owner-only file
   permissions on Linux/macOS). Every run after that uses the saved key -
   remove the email/password from `.env` once enrollment succeeds.

## Project layout

See `agent/docs/PROJECT_STRUCTURE.md` for the full breakdown.

## Documentation

- `agent/docs/INSTALLATION.md` - installing as a system service (systemd / Windows Service), PyInstaller packaging
- `agent/docs/API_INTEGRATION.md` - exactly which backend endpoints/events are used and how
- `agent/docs/COMMAND_FLOW.md` - how a command travels from the owner to the device and back
- `agent/docs/PROJECT_STRUCTURE.md` - module-by-module map
- `agent/docs/CHANGELOG.md` - version history

## Testing

```bash
pip install -r agent/requirements.txt
python -m pytest agent/tests -q
```

The suite includes a live integration test (`test_integration_backend.py`)
that spins up the actual backend in-process and drives the Agent through a
real enrollment -> heartbeat -> realtime command round trip. It's skipped
automatically unless the backend project is found (set
`ECHODESK_BACKEND_PATH` to point at it).
