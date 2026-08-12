# Changelog

## 0.2.0 (Agent-support additions)

Additive only — no existing table, column, endpoint, or event was renamed or removed.

- **Device API-key authentication.** Wired up the previously-unused `api_keys` table: keys are now scoped to a single device (`api_keys.device_id`). Added `POST /devices/{id}/api-key` and `DELETE /devices/{id}/api-key` (owner-only, JWT). `POST /devices/heartbeat`, `GET /commands/pending`, and all `/commands/{id}/files/*` routes now accept `X-API-Key: <prefix>.<secret>` as an alternative to a user Bearer token. Socket.IO `connect` accepts `auth: {api_key}` as an alternative to `auth: {token}` and auto-performs what `register_device` used to do.
- **Structured telemetry on heartbeat.** Added `devices.telemetry` (JSON) and `devices.last_telemetry_at` columns. `DeviceHeartbeatRequest` (REST) and the `heartbeat` socket event now accept an optional structured `telemetry` object (cpu/ram/disk/battery/network/ip/mac/uptime); omitting it behaves exactly as before.
- **Command file transfer.** New `command_files` table plus `POST/GET /commands/{id}/files` and `GET/DELETE /commands/{id}/files/{file_id}/download`. Uses the `UPLOAD_FOLDER`/`DOWNLOAD_FOLDER` paths that `create_app()` already provisioned but no route previously used. Gives `FILE_DOWNLOAD_REQUEST`, `FILE_UPLOAD_REQUEST`, and `SCREENSHOT_REQUEST` a real byte-transport channel (25 MB per-file ceiling); direction/uploader are derived from the authenticated caller, not client-supplied, and cross-device access is rejected.
- Fixed a latent bug in `SocketConnectionManager` where `connect_device()` would silently overwrite the `user_id` entry set by `connect_user()` for the same `sid` (now merges).
- Added `tests/test_device_agent_features.py` and extended `tests/test_sockets.py`; full suite (20 tests) passing.
- No `alembic.ini` / migration versions exist yet in this repo (only a hand-written `alembic/env.py`). For Postgres/production, run `flask db init` then `flask db migrate -m "agent support"` once to generate the migration for the new columns/tables — not done automatically here since there's no existing migration history to build on safely.

## 0.1.0

- Initial backend scaffold for authenticated device management.
- Added Flask app factory, SQLAlchemy models, REST blueprints, and Socket.IO events.
- Added docs and initial automated tests.
