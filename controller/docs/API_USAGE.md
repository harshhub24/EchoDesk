# API Usage

Every backend call/event this app makes, and which module makes it. All
verified directly against the backend source — see `docs/PHASE_1_ANALYSIS.md`
for how, and for the two real gaps (no realtime push, no command-result
data via REST) that shape a few design choices below.

## REST (base: `{ECHODESK_BACKEND_URL}/api/v1`)

| Endpoint | Module | Used for |
|---|---|---|
| `POST /login` | `app/auth/token_manager.py` | Login page |
| `POST /refresh` | `app/auth/token_manager.py` | Silent session restore + proactive/reactive token refresh |
| `POST /logout` | `app/auth/token_manager.py` | Log Out (top nav / Profile) |
| `POST /change-password` | `app/views/profile_view.py` | Profile page |
| `GET /profile` | `app/views/profile_view.py` | Profile page |
| `GET /devices` | `app/services/device_service.py::DeviceListService`, `app/services/dashboard_service.py` | Devices page, Dashboard counts |
| `GET /devices/{id}` | `app/services/device_service.py::DeviceDetailService` | Device Details (polled) |
| `DELETE /devices/{id}` | `app/views/device_details_view.py` | Delete Device button |
| `POST /devices/{id}/api-key` | `app/api/endpoints.py` (available; not currently surfaced in any page's UI — see Known Gaps below) | |
| `POST /commands` | `app/services/command_service.py::CommandService.send_command` | Command Center quick actions/message, File Manager download/upload/delete/list requests |
| `GET /commands` | `app/services/command_service.py::CommandService.refresh`, `app/services/dashboard_service.py` | Command Center history, Dashboard recent commands |
| `POST /commands/{id}/files` | `app/services/command_service.py::upload_file_for_command` | File Manager upload flow |
| `GET /commands/{id}/files` | `app/services/command_service.py::list_command_files` | Finding a completed download/screenshot's file |
| `GET /commands/{id}/files/{file_id}/download` | `app/services/command_service.py::download_command_file` | Save As... in File Manager / Command Center |
| `GET /activity` | `app/services/activity_service.py` | Activity Logs page |
| `GET /notifications` | `app/services/notification_service.py` | Notifications page (see docs/PHASE_1_ANALYSIS.md — currently always empty, not a bug) |

## Socket.IO (base namespace `/`)

`app/socket/client.py` connects with `auth: {token: <user_access_token>}`,
joining the `user:{id}` room. Per the Phase 1 finding, **the backend
doesn't currently broadcast anything to that room** — no device
online/offline events, no command status pushes. This connection exists
for session presence and forward compatibility; every page's live-feeling
updates come from `QTimer`-driven polling (`app/services/*_service.py`),
configurable in Settings.

## Known gaps this app works around (not backend bugs — see PHASE_1_ANALYSIS.md)

- **`GET /commands` has no `output`/`execution_status` fields.** Only
  `status` (pending/delivered/executing/success/failed) is visible. For
  `SCREENSHOT_REQUEST` and `FILE_DOWNLOAD_REQUEST`, the actual result *is*
  retrievable — as a real file via the files endpoints above. Every other
  command type's detailed result (e.g. what a `FILE_LIST_REQUEST` actually
  listed) is not retrievable through any current API.
- **Device API keys aren't surfaced in the UI yet.** The wrapper
  (`issue_device_api_key`/`revoke_device_api_key`) exists in
  `app/api/endpoints.py` since the route is real and owner-usable, but no
  page currently calls it — a natural Device Details addition if you want
  to let operators provision Agent credentials from this app instead of
  curl/Postman.
