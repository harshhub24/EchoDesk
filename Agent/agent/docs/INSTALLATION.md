# Installation

## 1. Prerequisites

- Python 3.12+ on both platforms
- Linux Mint: `libnotify-bin` for on-screen messages (`sudo apt install libnotify-bin`) - optional, MESSAGE_REQUEST degrades gracefully without it
- Windows 10/11: no extra system packages needed; `pywin32` (installed via requirements.txt) provides service support

## 2. Get the code onto the device

Copy the whole project (the folder containing `run.py` and `agent/`) to its
final location:

- Linux: e.g. `/opt/echodesk-agent`
- Windows: e.g. `C:\Program Files\EchoDeskAgent`

## 3. Configure

```bash
cp agent/.env.example agent/.env
```

Edit `agent/.env`:
- `ECHODESK_BACKEND_URL` - your backend's base URL
- Either `ECHODESK_API_KEY` (recommended) or `ECHODESK_EMAIL`/`ECHODESK_PASSWORD` for one-time enrollment (see README.md)
- Optionally `ECHODESK_FILE_ROOT` to sandbox the file manager to one directory

## 4. Install as a system service

### Linux (systemd)

```bash
cd agent/installer/linux
sudo ./install.sh
```

This creates a virtualenv at `<install_dir>/venv`, installs dependencies,
writes `/etc/systemd/system/echodesk-agent.service` (see
`agent/installer/linux/echodesk-agent.service` for the template), and
starts the service.

Manage it with:
```bash
systemctl status echodesk-agent
systemctl restart echodesk-agent
journalctl -u echodesk-agent -f
```

Uninstall:
```bash
cd agent/installer/linux
sudo ./uninstall.sh
```

### Windows 10/11 (Windows Service)

Open PowerShell **as Administrator**:
```powershell
cd agent\installer\windows
.\install.ps1
```

This creates a virtualenv, installs dependencies (including `pywin32`), and
registers/starts the `EchoDeskAgent` Windows Service.

Manage it with:
```powershell
Get-Service EchoDeskAgent
Restart-Service EchoDeskAgent
```

Uninstall:
```powershell
cd agent\installer\windows
.\uninstall.ps1
```

## 5. Running without installing a service (development / testing)

```bash
python run.py
```

Runs in the foreground with console + rotating file logging
(`agent/logs/agent.log`). Ctrl+C for a graceful shutdown.

## 6. Packaging a standalone executable (PyInstaller)

Useful if you don't want to rely on a system Python/venv being present.

```bash
pip install pyinstaller
pyinstaller --onefile --name echodesk-agent --add-data "agent/.env.example:agent" run.py
```

Notes:
- Build separately on Linux and Windows (PyInstaller doesn't cross-compile).
- The resulting binary still reads `agent/.env` relative to its own
  location by default - keep `agent/.env` next to the built executable, or
  set `ECHODESK_DATA_DIR`/`ECHODESK_LOG_DIR` explicitly.
- On Windows, if you want the frozen binary to run *as* the Windows Service
  itself (instead of via the venv Python + `windows_service.py`), point the
  service's `ExecStart` equivalent (via `sc.exe create` or a service wrapper
  like NSSM) at the built `.exe` instead of `python run.py`.
- `mss` (screenshots) and `pywin32` (Windows service) both need to be
  present at build time so PyInstaller can bundle them - installing from
  `agent/requirements.txt` before building covers this.

## Troubleshooting

- **"Cannot start: No device API key available..."** - set `ECHODESK_API_KEY`
  or `ECHODESK_EMAIL`/`ECHODESK_PASSWORD` in `agent/.env`.
- **Enrollment succeeds but heartbeats fail with 401** - the backend URL is
  probably wrong, or the persisted key in `agent/device_credentials.json` was
  revoked; delete that file and re-enroll.
- **Commands aren't arriving in realtime** - check `agent/logs/agent.log` for
  socket connect errors; the Agent still works via REST polling
  (`/commands/pending`, every 15s) as a fallback even if the socket can't
  connect (e.g. a proxy blocking WebSocket upgrades - the client also falls
  back to long-polling automatically).
