# Desktop Controller — Phase 2: Architecture

## Layering (Clean Architecture, per your spec)

```
views/        Qt windows & pages (QMainWindow, QWidget pages) - layout + wiring only, no business logic
widgets/      Reusable Qt components (cards, device tile, sidebar item, chart widget, toast, etc.)
dialogs/      Modal dialogs (login, confirm-command, file conflict, settings, about)
services/     Business logic: talks to api/ and socket/, exposes Qt signals, no Qt widget imports
api/          HTTP layer: requests-based client, one function per backend endpoint (mirrors Agent's api/endpoints.py pattern)
socket/       python-socketio client wrapper, background thread, Qt signals for events
models/       Plain dataclasses mirroring backend response shapes (Device, Command, Notification, ActivityEntry, ...) - no ORM, just typed containers + `from_dict`
auth/         Token storage, refresh scheduling, login/logout orchestration
theme/        QSS stylesheet(s), color tokens, fonts
utils/        Formatting helpers (bytes→human, relative time), logging setup, validators
config/       .env loading, AppConfig dataclass (same pattern as Agent's config.py)
constants.py  CommandType/DeviceStatus/NotificationCategory - copied verbatim from backend, same discipline as the Agent
```

Dependency direction: `views/widgets/dialogs` → `services` → `api`/`socket`/`models`. Services never import from `views`; views never call `api`/`socket` directly. This is what makes it testable without a display (services + api layer are pure Python, unit-testable headlessly; only `views`/`widgets`/`dialogs` need a Qt event loop).

## Threading model

PySide6's UI must run entirely on the main thread. Two sources of background work:

1. **HTTP calls** (`api/`) - dispatched via a small `QThreadPool` + `QRunnable` worker pattern (`utils/workers.py`, Phase 4), each call runs off-thread and reports back through a Qt signal. Every `services/` method that hits the network is async from the UI's point of view: fire, get a signal later, update UI in the slot.
2. **Socket.IO client** (`socket/`) - one long-lived background thread (same pattern as the Agent's `SocketClient`), re-emits every inbound event as a Qt signal via a `QObject` bridge (`socket/bridge.py`, Phase 4) so widgets can `connect()` to it normally. Given the Phase 1 finding that the backend doesn't currently push realtime device/command updates to the owner, this thread's practical job for now is: stay connected (session presence, matches your spec's "Socket.IO updates" wording), and be ready to consume owner-room events the moment the backend adds them, without any Controller-side changes needed later.
3. **Polling** - `QTimer` on the main thread, interval configurable in Settings (default matches Agent heartbeat cadence, 30s for devices; 5-10s for the Command Center while a command is in flight, backing off once nothing is pending). Each tick triggers an async `api/` call via the worker pool, never blocks the UI thread.

## State management

A single `services/app_state.py` `QObject` holds the current session (user, tokens, selected device, last-known device list, last-known command list) and exposes Qt signals (`devices_updated`, `commands_updated`, `notifications_updated`, `auth_state_changed`, ...). Pages subscribe to what they need; nobody polls the backend directly from a view.

## Auth & token storage

- Access + refresh tokens held in memory (`AppState`) for the session.
- "Remember Login" (per spec) persists only the **refresh token**, encrypted at rest using Windows DPAPI via `pywin32`'s `win32crypt.CryptProtectData` (user-scoped, tied to the Windows login) - never plaintext on disk. Falls back to a clearly-labeled `keyring`-backed store if DPAPI isn't available (e.g. running the source directly on non-Windows during development), documented as dev-only.
- A background `QTimer` refreshes the access token a few minutes before its 15-minute expiry using `POST /refresh`, so a logged-in session doesn't silently die mid-use.
- Logout calls `POST /logout` (best-effort) and always clears local state regardless of that call's outcome.

## Error handling & resilience

- Every `api/` call funnels through one `RestClient` (same shape as the Agent's) with typed `ApiError`/`AuthenticationError` exceptions; a 401 mid-session triggers one silent refresh-and-retry before surfacing an error to the UI.
- Network failures degrade to a visible (non-blocking) status indicator + toast, never a crash - matches the Agent's "never crash" principle, applied to the UI: a failed poll just leaves the last-known data on screen with a "last updated" timestamp and retries on the next tick.

## Theme

QSS-based (no external UI framework), tokens defined once in `theme/tokens.py` (royal purple / blue accent / dark glassmorphism, per spec) and compiled into a stylesheet string in `theme/qss.py`, applied once at `app.setStyleSheet(...)` in `main.py`. Card/glass effects via QSS `border-radius` + translucent backgrounds + `QGraphicsDropShadowEffect` per-widget (Qt has no native backdrop-blur; a subtle drop shadow + semi-transparent panel is the practical "glassmorphism" approximation on desktop Qt, called out explicitly rather than overpromising a blur effect Qt can't natively do well).

## Packaging

PyInstaller `--onefile --windowed`, spec file generated in Phase 15, icon + version info embedded, `.env` read from next to the executable (same "config lives beside the binary" convention as the Agent) so a non-technical device owner can drop in a `.env` with their backend URL without touching source.
