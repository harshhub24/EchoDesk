# Changelog

## 1.0.0

Initial release, built against backend v0.2.0 and the completed Agent, with
no Agent changes and one backend bugfix (see below).

- Full page set: Login, Dashboard, Devices, Device Details (with CPU/RAM
  history charts), File Manager, Command Center, Activity Logs,
  Notifications, Settings, Profile.
- Auth: JWT login, "Remember Login" via Windows DPAPI (keyring fallback for
  non-Windows dev), proactive + reactive access-token refresh.
- All 12 backend command types sendable from Command Center; file transfer
  (download/upload/delete) fully functional in File Manager.
- Dark/royal-purple/blue-accent glassmorphism-approximation theme (QSS +
  drop-shadow elevation).
- Polling-based data refresh throughout (device list/detail, commands,
  activity, notifications) — the backend doesn't currently push realtime
  updates to the owner; the Socket.IO connection is kept alive for session
  presence and forward compatibility regardless.
- 40 automated tests (unit + a subprocess-isolated live integration test
  against the real backend), all passing, repeatably (3x stability check).
- PyInstaller `.spec` for a Windows onedir build, verified by an actual
  end-to-end build + frozen-binary launch test (see docs/BUILD_GUIDE.md) —
  caught and fixed a missing `platformdirs` hidden import along the way.

### Backend bugfix included in this release

`GET /devices` and `GET /devices/{id}` were missing `telemetry` and
`last_telemetry_at` from their response — those fields were added to the
`Device` model and `DeviceResponse` schema back when device-auth/telemetry
support was built, but the two route handlers built their response dicts
by hand and were never updated to include them. Found by this app's live
integration test (Device Details showed blank telemetry despite the
backend having real data). Fixed by introducing a single
`_device_to_dict()` helper both routes now share, so they can't drift
apart again. Backend's own 20-test suite still passes unmodified.

### Known limitations (see README.md for full detail)

- No realtime device/command push from the backend — everything here is
  polling-based by design, not a missing feature.
- Directory browsing (`FILE_LIST_REQUEST`) can't display a result — no
  REST path to a command's result data exists for non-file-producing
  command types. Download/Upload/Delete by exact path all work fully.
- Notifications page is correctly wired but will show empty until the
  backend starts writing notification records (no code path does today).
- Device API key issue/revoke wrappers exist in `app/api/endpoints.py` but
  aren't yet surfaced in any page's UI.
