# API Integration

Every backend endpoint/event the Agent uses, and which module calls it.
Nothing here was invented - it all matches the backend's
`docs/API_REFERENCE.md` (v0.2.0) exactly.

## REST (base: `{ECHODESK_BACKEND_URL}{ECHODESK_API_PREFIX}`, default `/api/v1`)

| Endpoint | Module | When |
|---|---|---|
| `POST /login` | `agent/api/auth.py` | Only during one-time bootstrap enrollment |
| `POST /devices/register` | `agent/api/auth.py` | Only during one-time bootstrap enrollment |
| `POST /devices/{id}/api-key` | `agent/api/auth.py` | Only during one-time bootstrap enrollment |
| `POST /devices/heartbeat` | `agent/heartbeat/heartbeat.py` | Every `ECHODESK_HEARTBEAT_INTERVAL` seconds (default 30) |
| `GET /commands/pending` | `agent/main.py` (`_run_command_poll_loop`) | Every 15 seconds, as a fallback alongside realtime delivery |
| `POST /commands/{id}/files` | `agent/files/downloader.py`, `agent/commands/handlers.py` | FILE_DOWNLOAD_REQUEST, SCREENSHOT_REQUEST |
| `GET /commands/{id}/files` | `agent/files/uploader.py` | FILE_UPLOAD_REQUEST (to find the staged file) |
| `GET /commands/{id}/files/{file_id}/download` | `agent/files/uploader.py` | FILE_UPLOAD_REQUEST |

Auth header on every request after enrollment: `X-API-Key: <prefix>.<secret>`
(the device-scoped key minted during enrollment). See `agent/api/client.py`.

## Socket.IO (base: `ECHODESK_BACKEND_URL`, default namespace `/`)

| Event | Direction | Module |
|---|---|---|
| `connect` (`auth: {api_key}`) | Agent -> backend | `agent/socket/client.py` |
| `connected` | backend -> Agent | ack, logged only |
| `registered` | backend -> Agent | ack, logged only |
| `heartbeat` | Agent -> backend | `agent/heartbeat/heartbeat.py`, only sent if the socket happens to be connected (REST heartbeat is the source of truth) |
| `heartbeat_ack` | backend -> Agent | ack, logged only |
| `command_created` | backend -> Agent | `agent/socket/events.py` -> `agent/commands/dispatcher.py`. **Note:** the backend wraps this as `{"success": true, "command": {...}}` - `events.py` unwraps it before passing to the dispatcher. |
| `command_ack` | Agent -> backend | `agent/commands/dispatcher.py`, sent for `delivered` then `executing` |
| `command_ack_received` | backend -> Agent | ack, logged only |
| `command_result` | Agent -> backend | `agent/commands/dispatcher.py`, sent for `success`/`failed` |
| `command_result_received` | backend -> Agent | ack, logged only |

`command_ack`/`command_result` have **no REST equivalent** on the backend -
if the socket is disconnected when a command finishes, `dispatcher.py`
queues the message and retries it every 5 seconds until the socket
reconnects (`CommandDispatcher.flush_pending`, called from
`agent/main.py`'s flush loop).

## Telemetry field mapping

`agent/system/device.py::collect_telemetry()` produces exactly the field
names the backend's `TelemetryPayload` schema expects (see backend
`app/schemas/devices.py`). This is asserted by
`agent/tests/test_system_info.py::test_collect_telemetry_matches_backend_schema_field_names`
- if you ever add a field on either side, that test will catch a mismatch
before it causes a 422 in production (the backend schema uses
`extra="forbid"`, so unknown fields are rejected outright).

## What is *not* sent

`agent/system/device.py::collect_static_system_info()` gathers kernel
version, architecture, and Python version (as your original spec requested)
but these are logged locally only - the backend's `DeviceRegisterRequest`
and `TelemetryPayload` schemas don't have fields for them today. See the
backend's `docs/CHANGELOG.md` (0.2.0 notes) if you want to extend the schema
further; the Agent's collectors already produce the data, only the wire
schema would need to grow.
