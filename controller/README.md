# EchoDesk Desktop Controller

A PySide6 desktop app for Windows that manages devices running the EchoDesk
Agent — through the EchoDesk backend only. It never talks to an Agent
directly:

```
Desktop Controller  →  Flask Backend  →  Agent (Linux/Windows)
```

## Quick start

```bash
python3 -m venv venv
source venv/bin/activate          # venv\Scripts\activate on Windows
pip install -r requirements.txt

cp .env.example .env
# edit .env: set ECHODESK_BACKEND_URL to your backend

python main.py
```

On first launch you'll land on the Login page. Log in with your EchoDesk
account (the same one your Agents are registered under) — everything else
follows from there.

## What's real vs. what's a known limitation

This app is built strictly against the backend and Agent exactly as they
exist today — no backend or Agent changes were made to support it (one
backend bugfix was made: `telemetry`/`last_telemetry_at` were missing from
the device REST responses despite being in the schema — see
`docs/CHANGELOG.md`). Two things work differently than you might expect
from the feature list, and are labeled as such in the app itself rather
than faked:

- **No realtime push.** The backend doesn't currently broadcast device or
  command updates to the owner over Socket.IO. Everything you see (device
  status, telemetry, command status) is polling-based (configurable in
  Settings), not push-based. The socket connection is still kept alive for
  session presence and is ready to pick up realtime updates the moment the
  backend adds them.
- **Directory browsing isn't available.** A `FILE_LIST_REQUEST` command's
  result only ever exists inside the Agent's `command_result.output`, sent
  over a socket channel that reaches the Agent, not the owner. There's no
  REST path to it. Download/Upload/Delete-by-exact-path all work fully
  (they use the backend's real file-transfer endpoints); browsing to find
  a path does not, and the File Manager page says so rather than pretending
  otherwise.

Full detail on both, and everything else that was verified against the
actual backend source rather than assumed: `docs/PHASE_1_ANALYSIS.md`.

## Documentation

- `docs/INSTALLATION.md` — setup, running from source, building an .exe
- `docs/BUILD_GUIDE.md` — PyInstaller packaging in depth
- `docs/API_USAGE.md` — every backend endpoint/event this app uses
- `docs/PROJECT_STRUCTURE.md` — module-by-module map
- `docs/USER_GUIDE.md` — how to use each page
- `docs/CHANGELOG.md` — version history
- `docs/PHASE_1_ANALYSIS.md` through `PHASE_4_CORE_FRAMEWORK.md` — the
  build's phase-by-phase analysis/architecture notes
- `PROJECT_CONTEXT.md` — running summary, updated after every phase

## Testing

```bash
pip install -r requirements.txt
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
```

40 tests: unit tests for every service/model/widget-adjacent logic, plus a
live integration test (`tests/test_integration_backend.py`) that spins up
the actual backend and drives the app's real `AppState`/services through a
full login → device registration → command → file-transfer round trip. It
runs as a subprocess for interpreter isolation (see that file's docstring)
and is skipped automatically unless the backend project is found — set
`ECHODESK_BACKEND_PATH` to point at it.
