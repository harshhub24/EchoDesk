# Changelog

## 1.0.0

Initial release of the EchoDesk Device Agent, built against backend v0.2.0.

- Cross-platform (Linux Mint primary, Windows 10/11 secondary) single Python codebase; OS-specific code isolated to `agent/platform/linux.py` and `agent/platform/windows.py`.
- Device-API-key authentication (no long-term storage of the owner's password); one-time bootstrap enrollment flow.
- REST + Socket.IO dual-path command delivery, with REST polling fallback and an ack/result retry queue for socket downtime.
- Structured telemetry heartbeat (cpu/ram/disk/battery/network/ip/mac/uptime) every 30s (configurable).
- All 12 backend command types implemented: LOCK, RESTART, SHUTDOWN, SLEEP, HIBERNATE, LOGOUT, MESSAGE_REQUEST, FILE_LIST_REQUEST, FILE_DOWNLOAD_REQUEST, FILE_UPLOAD_REQUEST, DELETE_FILE_REQUEST, SCREENSHOT_REQUEST.
- Path-traversal-safe file manager, optionally sandboxed via `ECHODESK_FILE_ROOT`.
- systemd service (Linux) and Windows Service (pywin32) installers, plus PyInstaller packaging instructions.
- Rotating logs; never crashes on a single failed command/network blip - retries and reconnects automatically.
- 50 automated tests (unit + a live integration test against the real backend), all passing.

### Known limitations (carried over from backend v0.2.0, see backend CHANGELOG)
- File/screenshot transfer is capped at 25MB per file (matches the backend's `MAX_FILE_SIZE_BYTES`).
- The backend does not auto-expire commands server-side; the Agent enforces `expires_at` locally before executing.
- Kernel version, CPU architecture, and Python version are collected but not currently transmitted - the backend's telemetry schema doesn't have fields for them yet (see backend `docs/CHANGELOG.md`).
