# PROJECT_CONTEXT.md — Desktop Controller

## Status: All 15 phases complete

| Phase | Status |
|---|---|
| 1 — Analyze Backend + Agent | ✅ `docs/PHASE_1_ANALYSIS.md` |
| 2 — Architecture | ✅ `docs/PHASE_2_ARCHITECTURE.md` |
| 3 — Folder Structure | ✅ `docs/PHASE_3_FOLDER_STRUCTURE.md` |
| 4 — Core Framework | ✅ `docs/PHASE_4_CORE_FRAMEWORK.md` |
| 5 — Authentication | ✅ Login page, verified live |
| 6 — Dashboard | ✅ verified live with real device/command/activity data |
| 7 — Devices | ✅ verified live (grid/list, search/sort, telemetry on tiles) |
| 8 — Telemetry | ✅ Device Details + CPU/RAM charts, verified live |
| 9 — File Manager | ✅ Download/Upload/Delete verified live; List honestly marked unavailable (see gaps below) |
| 10 — Command Center | ✅ Quick actions + Message, verified live |
| 11 — Notifications | ✅ wired to real endpoint (empty today, see gaps) |
| 12 — Settings / Profile | ✅ local `.env` read/write; account info + change password + logout |
| 13 — Testing | ✅ 40 tests passing (unit + subprocess-isolated live integration), stable across repeated runs |
| 14 — Documentation | ✅ README, INSTALLATION, BUILD_GUIDE, API_USAGE, PROJECT_STRUCTURE, USER_GUIDE, CHANGELOG |
| 15 — PyInstaller Build | ✅ `.spec` file, actually built and the frozen binary launched successfully |

## Hard constraints honored throughout

- No Agent changes were made.
- The backend was touched exactly once: `GET /devices` and `GET
  /devices/{id}` were missing `telemetry`/`last_telemetry_at` from their
  response despite those fields existing in the `Device` model and
  `DeviceResponse` schema since the Agent-support work — a bugfix
  completing already-declared schema, not a new feature or a redesign.
  Backend's own 20-test suite still passes unmodified. See
  `docs/CHANGELOG.md` for detail.
- Every API call, socket event, auth flow, and field name matches
  `docs/PHASE_1_ANALYSIS.md` exactly.
- Communication is Controller → Backend only, never directly to an Agent.

## Real bugs found and fixed during the build (not just written and assumed correct)

1. **`QObject::startTimer` from the wrong thread** — `TokenManager` was
   starting a `QTimer` (and indirectly constructing a `SocketBridge`
   `QObject`) from a `QThreadPool` worker thread. Fixed by splitting every
   session method into a pure-network half (worker-thread-safe) and a
   Qt-object-touching half (main-thread-only). See
   `docs/PHASE_4_CORE_FRAMEWORK.md`.
2. **Silently dropped worker callbacks** — nothing kept a `Worker`'s Python
   object alive after `run_async()` returned (the normal fire-and-forget
   pattern), so Qt could garbage-collect it mid-flight. Fixed with a
   module-level keep-alive set.
3. **Dashboard/Devices/etc. polling started before login** — the Shell was
   built (and its first page activated) at app-construction time, before
   any session existed, causing immediate 401s. Fixed by separating
   "show the page's UI" from "start its polling," the latter gated on
   `MainWindow._on_session_ready` actually firing.
4. **Backend response gap**: `telemetry`/`last_telemetry_at` missing from
   `GET /devices` and `GET /devices/{id}` — caught by the Device Details
   live test showing blank telemetry despite the backend genuinely having
   the data. Fixed in the backend (see above), verified against the
   backend's own test suite too.
5. **`command_created` envelope mismatch** carried over from the Agent
   work does not apply here (Controller never receives that event, per the
   Phase 1 finding) — no equivalent bug existed on this side, but the
   Phase 1 analysis specifically checked for it.
6. **PyInstaller packaging**: missing `platformdirs` hidden import (needed
   by `pkg_resources`' runtime hook, invisible to static analysis) — found
   by actually building and running the frozen binary, not just writing
   the spec and assuming it would work.

## Known, documented limitations (not bugs — real backend/Agent constraints)

- **No realtime push.** Everything is polling-based (`QTimer`, configurable
  in Settings). The backend doesn't currently broadcast device/command
  updates to the owner's Socket.IO room.
- **Directory listing (`FILE_LIST_REQUEST`) can't show a result.** No REST
  path to a command's `output` exists for non-file-producing command
  types. Download/Upload/Delete-by-path all work fully. The File Manager
  page says this plainly rather than faking a browser.
- **Notifications page is correctly wired but will be empty** until the
  backend writes notification records (no code path does today).
- **Device API key issue/revoke** wrappers exist in `app/api/endpoints.py`
  but aren't surfaced in any page's UI yet — a natural next addition if
  wanted.

## Verification method used throughout

Every phase from 5 onward was checked against a **real backend spun up
in-process** (same pattern as the Agent's own integration test), driving
the Controller's actual `AppState`/services/views — not mocks standing in
for "should work." Live checks covered: login, session restore, device
list/detail with real telemetry, command send + status polling, file
upload/download round trip, all 8 sidebar pages + Device Details
navigation, and a real PyInstaller build + frozen-binary launch. Several of
the bugs above were only found because of this — they would not have
surfaced from unit tests with mocked I/O alone.
