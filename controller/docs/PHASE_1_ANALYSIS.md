# Desktop Controller — Phase 1: Backend + Agent Analysis

Re-verified directly against the actual backend source (not from memory) before writing anything. Nothing below is guessed.

## 1. Authentication (reuse exactly)

- `POST /api/v1/signup` → `{success, message, data: {user_id, access_token, refresh_token}}`
- `POST /api/v1/login` → same shape as signup
- `POST /api/v1/refresh` — send the **refresh token** as the Bearer token; rotates both tokens, old refresh token's `jti` is revoked
- `POST /api/v1/logout` — optional body `{refresh_token}`; revokes it (or the current one from the Bearer token) and marks the user's device sessions inactive
- `POST /api/v1/change-password` — `{current_password, new_password}`
- Access token TTL 15 min, refresh token TTL 30 days (confirmed against `.env.example`/config, unchanged since Phase 1 of the backend work)
- The Controller authenticates as the **owner/user** (JWT), never as a device — it never uses `X-API-Key`. That header is the Agent's credential only.

## 2. Devices (reuse exactly)

- `GET /api/v1/devices` — JWT, all of the caller's devices, `DeviceResponse[]`
- `GET /api/v1/devices/{id}` — JWT, single `DeviceResponse` (`{id}` accepts backend row id, `uuid`, or agent `device_id`)
- `DELETE /api/v1/devices/{id}` — JWT
- `DeviceResponse` fields: `id, uuid, device_id, device_name, device_type, hostname, operating_system, status, last_seen_at, telemetry (dict|null), last_telemetry_at`
- `telemetry` is a free-form dict but in practice always matches the Agent's `TelemetryPayload`: `cpu_percent, ram_percent, ram_used_mb, ram_total_mb, disk_percent, disk_used_gb, disk_total_gb, battery_percent, battery_charging, network_status, ip_address, mac_address, uptime_seconds`
- `POST /api/v1/devices/{id}/api-key` / `DELETE .../api-key` exist (JWT, owner-only) — the Controller **can** use these to show/rotate/revoke a device's Agent credential from Settings or Device Details, since that's a legitimate owner action, not a device action.

## 3. Commands (reuse exactly)

- `POST /api/v1/commands` — JWT, `{device_id (backend row id), command_type, payload}` → creates + broadcasts `command_created` to `device:{id}` room. `command_type` must be one of the 12 values in `app/constants.py::CommandType` (LOCK, RESTART, SHUTDOWN, SLEEP, HIBERNATE, LOGOUT, MESSAGE_REQUEST, FILE_LIST_REQUEST, FILE_DOWNLOAD_REQUEST, FILE_UPLOAD_REQUEST, DELETE_FILE_REQUEST, SCREENSHOT_REQUEST).
- `GET /api/v1/commands` — JWT, **all** of the caller's commands across **all** devices, no `device_id` filter param, no pagination. Fields returned: `id, device_id, created_by_id, command_type, payload, status, created_at`. **Does not include the CommandResult (`output`/`execution_status`/`finished_at`)** — see gap #1 below.
- `GET /api/v1/commands/pending` — JWT or `X-API-Key`; this is the Agent's endpoint, the Controller has no reason to call it.

## 4. Command Files (reuse exactly)

- `POST /commands/{id}/files`, `GET /commands/{id}/files`, `GET /commands/{id}/files/{file_id}/download`, `DELETE /commands/{id}/files/{file_id}` — all accept JWT. The Controller uses these for: downloading files the Agent uploaded (screenshots, FILE_DOWNLOAD_REQUEST results), and uploading files for the Agent to fetch (FILE_UPLOAD_REQUEST).

## 5. Socket.IO (reuse exactly)

- `connect` with `auth: {token: <user_access_token>}` joins room `user:{user_id}` only.
- **The Controller receives no realtime device-status or command-status push.** Confirmed by reading `app/sockets/events.py` directly:
  - `command_ack_received` and `command_result_received` are emitted with a bare `emit(...)` call (no `room=` / `broadcast=` argument), which in Flask-SocketIO sends **only to the requesting client** (the Agent that sent the ack/result) — not to the owner's `user:{id}` room.
  - `command_created` is broadcast only to `device:{id}` (the Agent's room).
  - There is no event that pushes device online/offline transitions to the owner either.
  - **Practical effect: the Controller's socket connection is currently useless for realtime dashboard updates.** It's still worth connecting (keeps a live session, and the door is open if the backend ever adds owner-room broadcasts) but the UI must not be designed assuming realtime push — it needs polling.

## 6. Activity & Notifications (reuse exactly, with a gap)

- `GET /api/v1/activity` — JWT, list of `{id, activity_type, category, message, details, created_at}`. Populated by `log_activity()` calls scattered through the backend (login, signup, logout, password change, etc.) — this one **is** actively written to, so Activity Logs will show real data.
- `GET /api/v1/notifications` — JWT, list of `{id, title, message, category, is_read, details, created_at}`. **Gap:** `app/services/notification_service.py::create_notification()` exists but is never called anywhere in the backend. No code path creates a "device online", "device offline", "command success", or "command failed" notification today. The Notifications page will be correctly wired to the real endpoint, but will show an empty list until/unless the backend starts writing notifications somewhere. There's also no mark-as-read endpoint (`is_read` is read-only via this API).

## 7. Telemetry & Live Updates

- Telemetry only updates when the Agent heartbeats (every 30s by default) and calls `POST /devices/heartbeat` or the socket `heartbeat` event — both write to the same `Device.telemetry` column, so `GET /devices` / `GET /devices/{id}` always reflects the latest value regardless of which path the Agent used.
- No "temperature" field exists anywhere (Agent doesn't collect it, backend has no column for it) — the spec's "Temperature (if available)" will show as unavailable/hidden, not fabricated.
- No "installed Agent version" field exists anywhere (Agent doesn't send one, backend has no column). Device Details will omit this rather than guess.

## 8. Summary of gaps vs. the requested Controller feature set

Per your instruction this round (**do not modify Backend or Agent**), these are constraints the Controller's design must work within, not bugs to fix:

| Requested feature | Backend support | Controller design response |
|---|---|---|
| Command Center: "Execution Result" | Not exposed via REST (no CommandResult fields on `GET /commands`, no `GET /commands/{id}`) | Show status only (pending→delivered→executing→success/failed) via polling; for file-producing commands (SCREENSHOT_REQUEST, FILE_DOWNLOAD_REQUEST) surface the actual file via the existing `GET /commands/{id}/files` endpoint, which *does* work |
| Command Center: "Command Progress" (realtime) | No realtime push to the owner | Poll `GET /commands` on an interval (configurable in Settings) instead of expecting socket push |
| Live Telemetry: realtime via Socket.IO | No realtime push to the owner | Poll `GET /devices`/`GET /devices/{id}` on an interval; keep the socket connected for session presence and future-proofing, but don't rely on it for data |
| Notifications: device online/offline, command success/failed | No backend code path ever creates these | Wire the page to the real `GET /notifications` endpoint (will legitimately be empty right now); do **not** synthesize fake client-side notifications that look backend-sourced — if you want this populated, it needs a small additive backend change in a future round, your call |
| Device Details: "Installed Agent Version" | No field anywhere | Omit this field from the UI rather than show a fabricated value |
| Live Telemetry: "Temperature" | No field anywhere | Omit / show "not available" |

Everything else in your spec (Login, Dashboard counts, Device List/Details, File Manager, Command sending, Activity Logs, Settings, Profile) maps cleanly onto existing, working endpoints with no gaps.
