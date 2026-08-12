# EchoDesk

**A self-hosted, personal remote device management system** — monitor, control, and manage your own devices (Linux/Windows) from a native desktop app, backed by a real-time Flask API.

Think of it as a mini MDM (Mobile Device Management) stack, but built from scratch for personal use: your machines report telemetry, execute commands you send, and stay under your control end-to-end.

```
┌─────────────────────┐        REST + Socket.IO        ┌──────────────────┐        REST + Socket.IO        ┌─────────────────┐
│  Desktop Controller  │  ───────────────────────────▶  │   Flask Backend   │  ◀───────────────────────────  │  Device Agent   │
│      (PySide6)       │  ◀───────────────────────────  │ (PostgreSQL + JWT) │  ───────────────────────────▶  │ (Linux/Windows) │
└─────────────────────┘                                 └──────────────────┘                                 └─────────────────┘
     owner's UI                                             single source of truth                              runs on target device
```

> The Controller **never** talks to an Agent directly — every action, command, and piece of telemetry flows through the backend. This keeps auth, authorization, and audit logging centralized in one place.

---

## What it does

- **Register & track devices** — every Agent enrolls itself against your account and starts sending heartbeats (CPU, RAM, disk, battery, network, uptime).
- **Remote power control** — lock, restart, shutdown, sleep/hibernate, or log out a device from the Controller.
- **On-screen messaging** — push a message to a device's screen remotely.
- **File operations** — upload, download, and delete files on a remote device by path.
- **Screenshots on demand** — pull a live screenshot from any online device.
- **Activity & audit log** — every command and device event is recorded and viewable from the dashboard.
- **JWT auth + per-device API keys** — the owner authenticates with JWT; each Agent authenticates with its own scoped API key.
- **Live telemetry charts** — CPU/RAM history graphed inside the Controller (via PyQtGraph).

---

## Tech stack

| Component | Stack |
|---|---|
| **Backend** | Python 3.12+, Flask 3.x, SQLAlchemy 2.0, Flask-Migrate (Alembic), Flask-JWT-Extended, Flask-SocketIO, Flask-Limiter, Pydantic v2, PostgreSQL, Gunicorn + Eventlet |
| **Desktop Controller** | Python, PySide6 (Qt), python-socketio (client), PyQtGraph, PyInstaller (packaged as a Windows `.exe`) |
| **Device Agent** | Python, psutil, python-socketio (client), httpx/requests, tenacity (retry logic), mss (screenshots), runs as a native Windows Service / Linux systemd service |
| **Auth** | JWT (owner sessions) + scoped per-device API keys (Agent sessions) |
| **Realtime** | Socket.IO across all three components |
| **Testing** | pytest, pytest-flask, pytest-qt, pytest-cov |

---

## Project structure

```
EchoDesk/
├── backend/            # Flask API — the single source of truth
│   ├── app/
│   │   ├── api/            # REST endpoints
│   │   ├── models/         # SQLAlchemy models (device, user, command, activity_log...)
│   │   ├── services/       # business logic layer
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── sockets/        # Socket.IO event handlers
│   │   ├── security/       # JWT, password hashing, device auth, API keys
│   │   └── middleware/     # error handlers, security headers, request logging
│   ├── alembic/         # DB migrations
│   └── run.py
│
├── controller/         # PySide6 desktop app (the "admin panel")
│   ├── app/
│   │   ├── views/           # dashboard, devices, file manager, command center...
│   │   ├── widgets/         # reusable UI components (stat cards, device tiles, charts)
│   │   ├── services/        # talks to the backend REST/Socket.IO API
│   │   ├── api/ + socket/   # HTTP client + Socket.IO bridge
│   │   └── theme/           # design tokens + QSS styling
│   └── main.py
│
└── Agent/              # runs on every managed device
    └── agent/
        ├── system/          # CPU, RAM, disk, battery, network probes
        ├── power/            # lock/restart/shutdown/sleep/logout implementations
        ├── files/            # upload/download/delete/browse
        ├── services/         # install as Windows Service / Linux systemd unit
        ├── api/ + socket/    # backend communication layer
        └── main.py
```

---

## Getting started

### 1. Backend (Flask API)

```bash
cd backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# set DATABASE_URL (PostgreSQL), SECRET_KEY, JWT_SECRET_KEY

flask db upgrade          # run migrations
python run.py             # dev server
# production: gunicorn -k eventlet -w 1 run:app
```

### 2. Desktop Controller

```bash
cd controller
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# set ECHODESK_BACKEND_URL to your backend's URL

python main.py
```

Log in with the same account your devices will register under. Everything else — devices, telemetry, commands — follows from there.

### 3. Device Agent (install on each machine you want to manage)

```bash
cd Agent
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r agent/requirements.txt

cp agent/.env.example agent/.env
# set ECHODESK_BACKEND_URL, and either:
#   ECHODESK_API_KEY (pre-provisioned), or
#   ECHODESK_EMAIL + ECHODESK_PASSWORD (one-time bootstrap enrollment)

python run.py
```

For a permanent background service (auto-start on boot), see `Agent/agent/docs/INSTALLATION.md`.

---

## Known limitations

Documented honestly rather than hidden:

- **Realtime push to the owner is partial** — most Controller views poll on a configurable interval rather than receiving live Socket.IO pushes, since the backend doesn't yet broadcast every update type to the owner's room.
- **Remote directory browsing isn't available over REST** — a `FILE_LIST_REQUEST` result currently only reaches the Agent's socket channel, not a REST endpoint. Download/Upload/Delete by exact path work fully.

---

## Security notes

- All device communication is authenticated (JWT for the owner, scoped API keys for Agents).
- Refresh tokens are stored using OS-native secure storage (DPAPI on Windows via `pywin32`, `keyring` elsewhere).
- The Agent is a visible, explicitly-installed background service — no stealth, no hidden execution, no capability beyond what the owner's account can command.
- This project is meant for managing **devices you personally own and control**. It is not designed or intended for monitoring devices you do not have explicit authorization to manage.

---

## Built via vibe coding

EchoDesk was built end-to-end through **vibe coding** — describing the system, behavior, and constraints in natural language and iterating with Claude (Anthropic) across the backend, desktop app, and device agent, rather than hand-writing every line from a spec. Architecture decisions, API contracts, and UI structure were steered through conversation and refined by testing against the real running system, with bugs found and fixed by actually running the code — not just assumed correct.

---

## License

Personal project — for individual/portfolio use. Add a license file here if you intend to open-source it (MIT is a common choice for solo projects like this).
