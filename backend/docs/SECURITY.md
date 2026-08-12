# Security

## Controls

- JWT-based authentication for API access (15-minute access tokens, 30-day rotating refresh tokens)
- Device API keys (`prefix.secret`) as an unattended-process alternative to holding a user's login — see below
- bcrypt hashing for both user passwords and API key secrets
- centralized JSON error responses
- request rate limiting
- secure headers on every response
- explicit ownership checks for user-scoped and device-scoped resources
- audit logging support for key events

## Device API Keys

Since v0.2.0, a device can authenticate without the owning user's password or refresh token:

- The owner mints a key via `POST /devices/{id}/api-key` while logged in. The raw key (`{prefix}.{secret}`) is shown **exactly once** — only the bcrypt hash of the secret is stored.
- A key is scoped to exactly one device (`api_keys.device_id`); it cannot be used to act on any other device, even if issued by the same owner.
- Issuing a new key for a device immediately deactivates any previous key for that device (rotation, not accumulation).
- `DELETE /devices/{id}/api-key` revokes all active keys for a device immediately.
- Keys can carry an optional expiry (`expires_in_days`); expired keys are rejected the same as revoked ones.
- A compromised key exposes only that one device's heartbeat/pending-commands/file-transfer surface — not the owner's account, password, or other devices.

Operationally: treat a device's API key the same as an SSH key or service credential — store it with restrictive file permissions on the device, never commit it to source control, and rotate it if the device is decommissioned or suspected compromised.

## Intended Use

This backend is designed only for devices owned by the authenticated user or otherwise explicitly authorized. It is not multi-tenant and has no admin/support-staff access model — every device and command is scoped strictly to its owning user.
