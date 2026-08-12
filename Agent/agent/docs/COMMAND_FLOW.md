# Command Flow

## End-to-end path (realtime)

1. Owner's controller app calls `POST /commands` on the backend with
   `{device_id (backend row id), command_type, payload}`.
2. Backend creates the command (`status=pending`, `expires_at = now + 10min`)
   and broadcasts `command_created` to the Socket.IO room `device:{id}`.
3. `agent/socket/events.py` receives it, unwraps the
   `{"success": true, "command": {...}}` envelope, and hands the bare
   command dict to `agent/commands/dispatcher.py::CommandDispatcher.handle`
   on a dedicated background thread (so a slow command never blocks the
   socket event loop or the heartbeat).
4. `dispatcher.handle`:
   - Validates the envelope (`agent/commands/validator.py::validate_envelope`) - rejects unknown `command_type`.
   - Checks for duplicate delivery (same `command_id` seen twice, e.g. once via socket and once via the REST poll fallback) - second delivery is a no-op.
   - Checks expiry locally (`validator.is_expired`) - **the backend does not automatically flip expired commands to status `expired`**, so the Agent must self-police this.
   - Validates the payload has the fields that `command_type` needs.
   - Emits `command_ack` with `status=delivered`, then `status=executing`.
   - Calls `agent/commands/handlers.py::execute(command_type, ...)`.
   - On success: emits `command_result` with `execution_status=success` and the handler's `output` dict.
   - On any exception: emits `command_result` with `execution_status=failed` and `{"error": str(exception)}`.

## REST fallback path

`agent/main.py::_run_command_poll_loop` polls `GET /commands/pending` every
15 seconds and feeds every returned command through the same
`dispatcher.handle`. This covers:
- The startup window before the first successful socket connection.
- Any command missed while the socket was disconnected (network blip, proxy
  blocking WebSocket upgrade, backend restart, ...).

Because `dispatcher.handle` deduplicates by `command_id`, a command that
arrives via both paths (e.g. delivered by socket just before a poll also
picks it up) is only executed once.

## Per-command-type behavior

| `command_type` | Handler | Notes |
|---|---|---|
| `LOCK` | `agent/power/lock.py` | `loginctl lock-session`, falls back to `cinnamon-screensaver-command --lock` (Linux) / `LockWorkStation` (Windows) |
| `RESTART` | `agent/power/restart.py` | `systemctl reboot` / `shutdown /r /t 0` |
| `SHUTDOWN` | `agent/power/shutdown.py` | `systemctl poweroff` / `shutdown /s /t 0` |
| `SLEEP` | `agent/power/sleep_hibernate.py` | `systemctl suspend` / `SetSuspendState` |
| `HIBERNATE` | `agent/power/sleep_hibernate.py` | `systemctl hibernate` / `shutdown /h` |
| `LOGOUT` | `agent/power/logout.py` | `loginctl terminate-user` / `shutdown /l` |
| `MESSAGE_REQUEST` | `agent/commands/handlers.py::_handle_message` | `payload: {title?, message}`. Shows an on-screen notification/message box. Degrades gracefully (reports failure via `command_result`, doesn't crash the Agent) if the display/notify tool is unavailable. |
| `FILE_LIST_REQUEST` | `agent/files/browser.py` | `payload: {path?}` (defaults to `.`). Returns directory entries; bounded by `ECHODESK_FILE_ROOT` if set. |
| `FILE_DOWNLOAD_REQUEST` | `agent/files/downloader.py` | `payload: {path}`. Agent reads the local file and **uploads** it via `POST /commands/{id}/files` so the owner can then download it - see API_INTEGRATION.md. 25MB limit. |
| `FILE_UPLOAD_REQUEST` | `agent/files/uploader.py` | `payload: {destination_path}`. Agent fetches the file the owner already attached to this command (`GET /commands/{id}/files`, direction `owner_to_device`) and writes it locally. |
| `DELETE_FILE_REQUEST` | `agent/files/delete.py` | `payload: {path}`. Deletes a file or directory (recursively). |
| `SCREENSHOT_REQUEST` | `agent/commands/handlers.py::_handle_screenshot` | Captures the primary display via `mss`, uploads as `screenshot.png` the same way FILE_DOWNLOAD_REQUEST does. |

## Path safety

Every file-manager handler resolves paths through
`agent/files/browser.py::resolve_safe_path`, which rejects any path that
would resolve outside `ECHODESK_FILE_ROOT` (if configured) - including
`../../` traversal attempts. If `ECHODESK_FILE_ROOT` is unset, the Agent is
bounded only by the OS-level permissions of the account it runs as (which is
why the installation docs recommend running it as a normal user, not root,
where practical).
