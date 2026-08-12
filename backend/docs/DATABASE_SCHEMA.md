# Database Schema

## Tables

- `users`
- `devices` — now includes `telemetry` (JSON) and `last_telemetry_at`
- `device_sessions`
- `commands`
- `command_results`
- `command_files` — new; byte-level file transfer metadata
- `refresh_tokens`
- `activity_logs`
- `notifications`
- `user_settings`
- `api_keys` — now includes `device_id` (nullable FK to `devices.id`), scoping a key to one device

## Relationships

- A user owns many devices.
- A device belongs to one user and has many sessions, commands, API keys, and command files.
- A command belongs to one device and one creator, and may have many attached files (`command_files`).
- A command has zero or one execution result.
- A command file belongs to one command and one device, and has a `direction` (`device_to_owner` | `owner_to_device`) and `uploaded_by` (`device` | `owner`).
- An API key belongs to one user and, when used for device authentication, exactly one device.
- A user has many refresh tokens, notifications, activity logs, and API keys.

## New in 0.2.0

| Table/Column | Type | Notes |
|---|---|---|
| `devices.telemetry` | JSON | Last-reported CPU/RAM/disk/battery/network snapshot from the Agent's heartbeat |
| `devices.last_telemetry_at` | datetime | Set only when a heartbeat includes telemetry |
| `api_keys.device_id` | string(36), FK, nullable | Scopes a key to one device; null = not currently usable for device auth |
| `command_files` (table) | — | `command_id`, `device_id`, `direction`, `original_filename`, `stored_relative_path`, `content_type`, `size_bytes`, `checksum_sha256`, `uploaded_by` |
