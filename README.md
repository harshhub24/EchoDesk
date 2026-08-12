<div align="center">

# 🖥️ EchoDesk

**A self-hosted, personal remote device management system.**
Monitor, control, and manage your own devices — from a native desktop app, backed by a real-time Flask API.

Think of it as a mini MDM (Mobile Device Management) stack, built from scratch for personal use.

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PySide6](https://img.shields.io/badge/PySide6-Qt-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-Realtime-010101?style=for-the-badge&logo=socketdotio&logoColor=white)](https://socket.io/)

[![License](https://img.shields.io/badge/License-Personal%20Use-lightgrey?style=flat-square)]()
[![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)]()
[![Build](https://img.shields.io/badge/Build-Vibe%20Coded-ff69b4?style=flat-square)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue?style=flat-square)]()

</div>

---

## 📑 Table of contents

- [What is EchoDesk](#-what-is-echodesk)
- [Architecture](#-architecture)
- [Features](#-features)
- [Tech stack](#-tech-stack)
- [Project structure](#-project-structure)
- [API reference](#-api-reference)
- [Getting started](#-getting-started)
- [Known limitations](#-known-limitations)
- [Security](#-security)
- [How this was built](#-how-this-was-built)
- [License](#-license)

---

## 📌 What is EchoDesk

EchoDesk lets you register your own devices (laptops, desktops — Linux or Windows), watch their live telemetry, and issue remote commands to them — all from a single desktop control panel that you own end-to-end.

There are **three independent pieces** that talk to each other only through the backend:

| Piece | Role |
|---|---|
| 🎛️ **Controller** | The app *you* use — a native Qt desktop app to view devices and send commands |
| ⚙️ **Backend** | The brain — a Flask + PostgreSQL API that owns auth, state, and routing |
| 📡 **Agent** | Runs *on* each managed device — reports telemetry, executes commands |

---

## 🏗️ Architecture

```
                    REST + Socket.IO                          REST + Socket.IO
┌───────────────────┐   ───────────────▶   ┌───────────────────┐   ───────────────▶   ┌───────────────────┐
│  Desktop Controller │                     │    Flask Backend    │                     │    Device Agent     │
│      (PySide6)      │   ◀───────────────   │  (PostgreSQL + JWT)  │   ◀───────────────   │  (Linux / Windows)   │
└───────────────────┘                     └───────────────────┘                     └───────────────────┘
     owner's UI                              single source of truth                     runs on target device
```

> 🔒 **The Controller never talks to an Agent directly.** Every action, command, and piece of telemetry flows through the backend — one place for auth, authorization, and audit logging.

**Request flow example — locking a device:**

```
1. Owner clicks "Lock" in Controller
2. Controller  ──POST /commands──▶  Backend   (JWT-authenticated)
3. Backend validates, stores command, notifies Agent over Socket.IO
4. Agent       ──executes lock──▶  OS
5. Agent       ──POST result───▶  Backend
6. Controller polls / receives update ──▶ shows "Locked" ✅
```

---

## ✨ Features

<table>
<tr>
<td width="50%" valign="top">

**Device management**
- 📋 Auto-registration on first Agent run
- 💓 Periodic heartbeats (CPU, RAM, disk, battery, network, uptime)
- 📈 Live telemetry charts (PyQtGraph) in the Controller
- 🟢 Online/offline status tracking

**Remote control**
- 🔒 Lock / 🔁 Restart / ⏻ Shutdown
- 😴 Sleep / Hibernate / 🚪 Log out
- 💬 Push on-screen messages

</td>
<td width="50%" valign="top">

**Files & media**
- 📤 Upload files to a device
- 📥 Download files from a device
- 🗑️ Delete files by path
- 📸 On-demand screenshots

**Platform**
- 🔐 JWT auth (owner) + scoped API keys (per device)
- 🗂️ Full activity/audit log
- 🔔 Notification pipeline
- 🧪 40+ automated tests across the stack

</td>
</tr>
</table>

---

## 🧰 Tech stack

<table>
<tr><th>Layer</th><th>Technologies</th></tr>
<tr>
<td><b>Backend</b></td>
<td>

`Python 3.12+` `Flask 3.x` `SQLAlchemy 2.0` `Flask-Migrate / Alembic` `Flask-JWT-Extended` `Flask-SocketIO` `Flask-Limiter` `Pydantic v2` `PostgreSQL` `Gunicorn + Eventlet` `bcrypt`

</td>
</tr>
<tr>
<td><b>Desktop Controller</b></td>
<td>

`Python` `PySide6 (Qt)` `python-socketio (client)` `PyQtGraph` `PyInstaller` — packaged as a standalone Windows `.exe`

</td>
</tr>
<tr>
<td><b>Device Agent</b></td>
<td>

`Python` `psutil` `python-socketio (client)` `httpx / requests` `tenacity` (retry logic) `mss` (screenshots) — installs as a native **Windows Service** or **Linux systemd service**

</td>
</tr>
<tr>
<td><b>Cross-cutting</b></td>
<td>

**Auth:** JWT (owner sessions) + scoped per-device API keys · **Realtime:** Socket.IO across all three apps · **Testing:** `pytest` `pytest-flask` `pytest-qt` `pytest-cov`

</td>
</tr>
</table>

---

## 🗂️ Project structure

```
EchoDesk/
├── backend/                # Flask API — the single source of truth
│   ├── app/
│   │   ├── api/                 # REST blueprints (auth, devices, commands, files...)
│   │   ├── models/              # SQLAlchemy models
│   │   ├── services/            # business logic layer
│   │   ├── schemas/             # Pydantic request/response validation
│   │   ├── sockets/             # Socket.IO event handlers
│   │   ├── security/            # JWT, password hashing, device auth, API keys
│   │   └── middleware/          # error handlers, security headers, request logging
│   ├── alembic/              # DB migrations
│   └── run.py
│
├── controller/              # PySide6 desktop app — the admin panel
│   ├── app/
│   │   ├── views/                # dashboard, devices, file manager, command center...
│   │   ├── widgets/               # stat cards, device tiles, telemetry charts
│   │   ├── services/               # talks to backend REST/Socket.IO
│   │   ├── api/ + socket/          # HTTP client + Socket.IO bridge
│   │   └── theme/                  # design tokens + QSS styling
│   └── main.py
│
└── Agent/                   # runs on every managed device
    └── agent/
        ├── system/               # CPU, RAM, disk, battery, network probes
        ├── power/                 # lock/restart/shutdown/sleep/logout
        ├── files/                  # upload/download/delete/browse
        ├── services/                # install as Windows Service / systemd unit
        ├── api/ + socket/            # backend communication layer
        └── main.py
```

---

## 🔌 API reference

Base URL: `/api/v1`

<table>
<tr><th>Method</th><th>Endpoint</th><th>Purpose</th></tr>
<tr><td colspan="3"><b>Auth</b></td></tr>
<tr><td>POST</td><td><code>/auth/signup</code></td><td>Create an owner account</td></tr>
<tr><td>POST</td><td><code>/auth/login</code></td><td>Log in, receive JWT pair</td></tr>
<tr><td>POST</td><td><code>/auth/refresh</code></td><td>Refresh access token</td></tr>
<tr><td>POST</td><td><code>/auth/logout</code></td><td>Revoke session</td></tr>
<tr><td>POST</td><td><code>/auth/change-password</code></td><td>Change account password</td></tr>
<tr><td colspan="3"><b>Devices</b></td></tr>
<tr><td>POST</td><td><code>/devices/register</code></td><td>Agent self-registration</td></tr>
<tr><td>GET</td><td><code>/devices</code></td><td>List all owned devices</td></tr>
<tr><td>GET</td><td><code>/devices/{id}</code></td><td>Device detail + telemetry</td></tr>
<tr><td>DELETE</td><td><code>/devices/{id}</code></td><td>Remove a device</td></tr>
<tr><td>POST</td><td><code>/devices/heartbeat</code></td><td>Agent telemetry heartbeat</td></tr>
<tr><td>POST</td><td><code>/devices/{id}/api-key</code></td><td>Issue a device API key</td></tr>
<tr><td>DELETE</td><td><code>/devices/{id}/api-key</code></td><td>Revoke a device API key</td></tr>
<tr><td colspan="3"><b>Commands</b></td></tr>
<tr><td>POST</td><td><code>/commands</code></td><td>Issue a remote command</td></tr>
<tr><td>GET</td><td><code>/commands</code></td><td>Command history</td></tr>
<tr><td>GET</td><td><code>/commands/pending</code></td><td>Agent polls for pending commands</td></tr>
<tr><td colspan="3"><b>Files</b></td></tr>
<tr><td>POST</td><td><code>/commands/{id}/files</code></td><td>Upload a file result</td></tr>
<tr><td>GET</td><td><code>/commands/{id}/files</code></td><td>List files for a command</td></tr>
<tr><td>GET</td><td><code>/commands/{id}/files/{fileId}/download</code></td><td>Download a file</td></tr>
<tr><td>DELETE</td><td><code>/commands/{id}/files/{fileId}</code></td><td>Delete a file</td></tr>
<tr><td colspan="3"><b>Other</b></td></tr>
<tr><td>GET</td><td><code>/activity</code></td><td>Audit log</td></tr>
<tr><td>GET</td><td><code>/notifications</code></td><td>Notifications feed</td></tr>
<tr><td>GET / PUT</td><td><code>/profile</code></td><td>Owner profile</td></tr>
<tr><td>GET</td><td><code>/health</code></td><td>Health check</td></tr>
</table>

All responses share one shape:

```jsonc
// success
{ "success": true,  "message": "...", "data": {} }
// error
{ "success": false, "message": "...", "error": {} }
```

---

## 🚀 Getting started

### 1️⃣ Backend (Flask API)

```bash
cd backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# set DATABASE_URL (PostgreSQL), SECRET_KEY, JWT_SECRET_KEY

flask db upgrade          # run migrations
python run.py              # dev server
# production: gunicorn -k eventlet -w 1 run:app
```

### 2️⃣ Desktop Controller

```bash
cd controller
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# set ECHODESK_BACKEND_URL to your backend's URL

python main.py
```

Log in with the same account your devices will register under — devices, telemetry, and commands all follow from there.

### 3️⃣ Device Agent (install on each machine you want to manage)

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

## ⚠️ Known limitations

Documented honestly rather than hidden:

| Limitation | Detail |
|---|---|
| **Partial realtime push** | Most Controller views poll on a configurable interval rather than receiving live Socket.IO pushes for every update type. |
| **No REST path for directory listing** | A `FILE_LIST_REQUEST` result currently only reaches the Agent's socket channel. Download/Upload/Delete by exact path work fully. |

---

## 🔐 Security

- All device communication is authenticated — **JWT** for the owner, **scoped API keys** for Agents.
- Refresh tokens use OS-native secure storage (**DPAPI** on Windows via `pywin32`, `keyring` elsewhere).
- The Agent is a **visible, explicitly-installed** background service — no stealth, no hidden execution, no capability beyond what the owner's account can command.
- Built for managing **devices you personally own and control** — not intended for monitoring devices without explicit authorization.

---

## 🤖 How this was built

EchoDesk was built end-to-end through **vibe coding** — describing the system, behavior, and constraints in natural language and iterating with **Claude (Anthropic)** across the backend, desktop app, and device agent, instead of hand-writing every line from a spec.

Architecture decisions, API contracts, and UI structure were steered through conversation and refined against the real running system — bugs were found and fixed by actually running the code, not assumed correct on paper.


Made with ⚡ and a lot of back-and-forth with Claude.

</div>

## 🛠️ Troubleshooting & Common Issues

If you run into issues while setting up or running EchoDesk:

1. **Database Migration Errors:**
   - Make sure your PostgreSQL server is running and the database specified in `.env` exists.
   - Run `flask db upgrade` after setting your environment variables.

2. **Socket.IO Connection Failed:**
   - Ensure `ECHODESK_BACKEND_URL` is set correctly in both Controller and Agent `.env` files.
   - Check firewall rules if connecting from a different device on the local network.

3. **Missing System Dependencies (PySide6 / PyQtGraph):**
   - On Linux, you might need additional Qt libraries: `sudo apt install libxcb-cursor0`.

4. **Agent Privileges:**
   - Some system metrics or power commands (shutdown/lock) require root/administrator privileges depending on the OS.

## 💬 Support & Issues
Found a bug or having setup issues? Feel free to open an issue in the [GitHub Issues tab](https://github.com/harshhub24/EchoDesk/issues).
