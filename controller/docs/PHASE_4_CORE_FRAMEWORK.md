# Desktop Controller — Phase 4: Core Framework

## What was built

- `app/constants.py` — mirrors backend/Agent constants exactly, plus UI-only label maps
- `app/config/settings.py` — `AppConfig`, same `.env`-next-to-executable convention as the Agent
- `app/utils/logger.py`, `app/utils/formatting.py`, `app/utils/workers.py`
- `app/models/*` — plain dataclasses (`Device`, `Telemetry`, `Command`, `CommandFile`, `ActivityEntry`, `Notification`, `Session`), each with `from_dict`, deliberately containing **only** fields the backend actually returns (see Phase 1 gaps)
- `app/api/client.py` + `app/api/endpoints.py` — `requests`-based REST client (Bearer-only, single reactive-refresh-on-401), one function per endpoint from `PHASE_1_ANALYSIS.md`
- `app/auth/secure_storage.py` + `app/auth/token_manager.py` — DPAPI-backed (Windows) / keyring-backed (dev fallback) refresh-token persistence, proactive + reactive token refresh
- `app/socket/client.py` + `app/socket/bridge.py` — Socket.IO client (owner-token auth), background connection thread, Qt signal bridge
- `app/theme/tokens.py` + `app/theme/qss.py` — dark/purple/blue glassmorphism-approximation stylesheet
- `app/widgets/shadow.py` + `app/widgets/card.py` — shared elevation helper + base `GlassCard`
- `app/services/app_state.py` — central `AppState`, owns everything above, exposes session-lifecycle signals
- `app/views/main_window.py` — placeholder shell proving the wiring (Login UI is Phase 5)
- `main.py`, `requirements.txt`, `.env.example`

## Verification (not just claims)

- **28 unit tests passing** (`pytest tests/ -q`): formatting, REST client (mocked transport, auth headers, 401-refresh-retry, multipart upload), async worker helper, full `TokenManager` lifecycle (mocked network + storage).
- **A live end-to-end smoke test** (real backend, spun up in-process exactly like the Agent's integration test) exercising: signup → `AppState.login()` → real `POST /login` → real authenticated `GET /devices` → real Socket.IO connect to the `user:{id}` room. All confirmed working.

### Two real bugs the live test caught and fixed:

1. **`QObject::startTimer: Timers cannot be started from another thread`.** `TokenManager` was starting its proactive-refresh `QTimer` (and, via a signal, constructing a `SocketBridge` `QObject`) from inside the network call itself - which `run_async` executes on a `QThreadPool` worker thread. Fixed by splitting every session-touching method into a pure-network half (safe on a worker thread: `login`, `restore_session`, `logout`) and a Qt-object-touching half (`activate_session`, `deactivate_session`) that only ever runs from a worker-result callback, which Qt automatically marshals back to the main thread. This is now a documented pattern (see the docstrings in `token_manager.py`) that later phases must follow for any new session-adjacent state.
2. **Silently dropped worker callbacks.** `QRunnable` isn't `QObject`-derived, so nothing pinned a `Worker`'s Python object (and its `signals`) alive once `run_async()` returned - a very common fire-and-forget call pattern (`run_async(fn, on_result=...)` with the return value discarded, which is how `AppState` always calls it). Python's GC could collect the worker mid-flight, silently dropping the result/error signal. Fixed with a module-level keep-alive set in `app/utils/workers.py`, cleared once the worker's `finished` signal fires. Caught by a plain unit test (`test_workers.py`) before this could have caused mysteriously-hanging logins in later phases.

## PROJECT_CONTEXT.md

Updated - see the file at the project root.
