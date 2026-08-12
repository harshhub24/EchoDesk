# Installation

## Prerequisites

- Windows 10/11 (primary target — this app is built for a Windows desktop
  operator; it will also run from source on Linux/macOS for development,
  with the refresh-token storage falling back to `keyring` instead of
  DPAPI, see `docs/PHASE_4_CORE_FRAMEWORK.md`)
- Python 3.12+

## Running from source

```bash
git clone <this project>  # or copy the folder
cd controller
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

copy .env.example .env
```

Edit `.env`:
- `ECHODESK_BACKEND_URL` — your backend's base URL (required)
- `ECHODESK_DEVICE_POLL_INTERVAL` / `ECHODESK_COMMAND_POLL_INTERVAL` — how
  often the app refreshes data (seconds); defaults are 30 and 5
- Everything else has a sensible default — see `.env.example`

```bash
python main.py
```

## Building a standalone .exe

See `docs/BUILD_GUIDE.md` for the full PyInstaller walkthrough. Short version:

```bash
pip install pyinstaller
pyinstaller EchoDeskController.spec
```

The built executable will be in `dist/EchoDeskController/`. Copy your
`.env` next to the `.exe` before distributing/running it.

## First run

1. Launch the app — you'll see the Login page.
2. Log in with your EchoDesk account (the same one your devices are
   registered under via the Agent).
3. You'll land on the Dashboard. Use the sidebar to navigate to Devices,
   File Manager, Command Center, Activity Logs, Notifications, Settings,
   or Profile.

## Troubleshooting

- **"Could not refresh devices: ..." on every page** — check
  `ECHODESK_BACKEND_URL` in `.env` and that the backend is reachable from
  this machine.
- **Login succeeds but nothing loads** — check the backend URL doesn't have
  a trailing `/api/v1` already baked in (that's appended automatically);
  it should just be the bare backend origin, e.g. `https://echodesk.example.com`.
- **Refresh token isn't remembered between runs** — on Windows this uses
  DPAPI and should just work under the same Windows user account; if
  you're running from source on Linux for development, install a keyring
  backend (`pip install keyrings.alt` is the simplest cross-platform dev
  fallback) or just re-log-in each run.
- **Directory browsing doesn't show anything** — this is a known,
  documented limitation, not a bug — see the README's "known limitations"
  section.
