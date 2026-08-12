# API Reference

Base path: `/api/v1`

## Auth

- `POST /signup`
- `POST /login`
- `POST /refresh`
- `POST /logout`
- `POST /change-password`

## Profile

- `GET /profile`
- `PUT /profile`

## Devices

- `POST /devices/register` — JWT only
- `GET /devices` — JWT only
- `GET /devices/{id}` — JWT only
- `DELETE /devices/{id}` — JWT only
- `POST /devices/heartbeat` — JWT **or** `X-API-Key`; accepts optional `telemetry` object
- `POST /devices/{id}/api-key` — JWT only (owner). Mints/rotates a device-scoped API key. **The raw key is returned once and cannot be retrieved again.**
- `DELETE /devices/{id}/api-key` — JWT only (owner). Revokes all active keys for the device.

## Commands

- `POST /commands` — JWT only (creates + broadcasts a command to the device)
- `GET /commands` — JWT only
- `GET /commands/pending` — JWT **or** `X-API-Key` (API-key callers only ever see their own device's pending commands)

## Command Files (new)

- `POST /commands/{command_id}/files` — JWT **or** `X-API-Key`, multipart field `file`. Direction is inferred from the caller: a device key uploading = `device_to_owner`; a JWT/owner uploading = `owner_to_device`. 25 MB per-file limit.
- `GET /commands/{command_id}/files` — JWT **or** `X-API-Key`. Lists file metadata for a command.
- `GET /commands/{command_id}/files/{file_id}/download` — JWT **or** `X-API-Key`. A device key may only download `owner_to_device` files; an owner may download either direction.
- `DELETE /commands/{command_id}/files/{file_id}` — JWT **or** `X-API-Key`.

## Operational

- `GET /activity`
- `GET /notifications`
- `GET /health`

## Device Authentication (new)

Two ways to authenticate as a device on the endpoints marked above:

1. **User JWT** (legacy/controller-app path) — `Authorization: Bearer <access_token>`. Works on any of the caller's devices; `device_id` must be supplied in the request body/room, since the token doesn't identify a single device.
2. **Device API key** (Agent path) — `X-API-Key: <prefix>.<secret>`, obtained via `POST /devices/{id}/api-key`. Identifies exactly one device; `device_id` is inferred, does not need to be supplied.

## Socket.IO (base namespace `/`)

| Event | Direction | Notes |
|---|---|---|
| `connect` | client→server | `auth: {token}` (user JWT) **or** `auth: {api_key}` (device key, new). The `api_key` path auto-registers the device room (equivalent of `register_device`). |
| `connected` | server→client | Ack |
| `register_device` | client→server | `{device_id}` — still required on the `token` path; a no-op safety net if already registered via `api_key` |
| `registered` | server→client | `{device_id}` |
| `heartbeat` | client→server | `{status?, telemetry?}` if connected via `api_key` (device already known); `{owner_id, device_id, status?, telemetry?}` on the legacy `token` path |
| `heartbeat_ack` | server→client | `{device_id}` |
| `command_ack` / `command_result` | client→server | Unchanged |
| `command_created` | server→client | Unchanged, broadcast to `device:{id}` room |
