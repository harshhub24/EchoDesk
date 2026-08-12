# Project Structure

```
controller/
├── main.py                      # Entry point
├── requirements.txt
├── README.md
├── .env.example
├── pytest.ini
├── PROJECT_CONTEXT.md            # Running summary, updated every phase
│
├── app/
│   ├── constants.py               # CommandType/DeviceStatus/etc - mirrors backend+Agent exactly
│   │
│   ├── config/
│   │   └── settings.py             # AppConfig, .env loader
│   │
│   ├── api/
│   │   ├── client.py                # RestClient (requests-based, Bearer auth, 401-refresh-retry)
│   │   └── endpoints.py               # One function per backend REST route used
│   │
│   ├── socket/
│   │   ├── client.py                  # Socket.IO client (owner-token auth)
│   │   └── bridge.py                    # Qt signal bridge + background connection thread
│   │
│   ├── auth/
│   │   ├── token_manager.py             # Login/logout/refresh lifecycle (Qt-thread-safety-critical, see docstrings)
│   │   └── secure_storage.py              # DPAPI (Windows) / keyring (dev fallback) refresh-token persistence
│   │
│   ├── models/                             # Plain dataclasses mirroring backend response shapes
│   │   ├── device.py (Device, Telemetry)
│   │   ├── command.py (Command, CommandFile)
│   │   ├── activity.py (ActivityEntry, Notification)
│   │   └── user.py (Session)
│   │
│   ├── services/                             # Business logic - the only layer allowed to touch api/socket
│   │   ├── app_state.py                        # Central session/socket owner, Qt signals
│   │   ├── dashboard_service.py
│   │   ├── device_service.py                     # DeviceListService, DeviceDetailService
│   │   ├── command_service.py                      # Shared by File Manager + Command Center
│   │   ├── activity_service.py
│   │   └── notification_service.py
│   │
│   ├── views/                                        # One file per page
│   │   ├── main_window.py                              # Login <-> Shell session-lifecycle switch
│   │   ├── login_view.py
│   │   ├── shell.py                                      # Sidebar + top nav + page stack, page lifecycle (start/stop)
│   │   ├── dashboard_view.py
│   │   ├── devices_view.py
│   │   ├── device_details_view.py
│   │   ├── file_manager_view.py
│   │   ├── command_center_view.py
│   │   ├── activity_logs_view.py
│   │   ├── notifications_view.py
│   │   ├── settings_view.py
│   │   └── profile_view.py
│   │
│   ├── widgets/                                            # Reusable components
│   │   ├── card.py (GlassCard), shadow.py
│   │   ├── stat_card.py, device_tile.py, telemetry_chart.py
│   │   └── sidebar.py, top_nav.py
│   │
│   ├── dialogs/                                              # (confirmations use QMessageBox inline for
│   │                                                            now; empty package reserved for custom
│   │                                                            dialogs if a page needs one beyond that)
│   │
│   ├── theme/
│   │   ├── tokens.py                                          # Single source of truth for colors/fonts/spacing
│   │   └── qss.py                                               # Compiles tokens into the app stylesheet
│   │
│   ├── utils/
│   │   ├── logger.py, formatting.py, workers.py                  # QThreadPool async helper (see its
│   │                                                                docstring for a GC-safety gotcha it fixes)
│   │
│   └── assets/                                                       # Icons/fonts for the PyInstaller build
│
├── logs/                                                                # Runtime logs (controller.log, rotated)
│
├── docs/
│   ├── PHASE_1_ANALYSIS.md ... PHASE_4_CORE_FRAMEWORK.md                 # Build-process phase notes
│   ├── INSTALLATION.md, BUILD_GUIDE.md, API_USAGE.md
│   ├── PROJECT_STRUCTURE.md (this file), USER_GUIDE.md, CHANGELOG.md
│
└── tests/
    ├── conftest.py
    ├── test_formatting.py, test_models.py
    ├── test_api_client.py, test_workers.py
    ├── test_token_manager.py, test_command_service.py
    ├── test_integration_backend.py                                         # Subprocess-isolated live test
    └── _integration_backend_script.py                                        # (see its docstring for why subprocess)
```

## Layering rule

`views/widgets/dialogs` → `services` → `api`/`socket`/`models`. Views never
import `app/api` or `app/socket` directly - always through a `services/`
class, which is what keeps `services/` unit-testable without a display and
`views/` free of network-error-handling boilerplate.

## Page lifecycle

Every page view implements `start()`/`stop()`. `app/views/shell.py` calls
`start()` when a page becomes visible (kicking off its polling `QTimer`s)
and `stop()` when navigating away — so only the currently-visible page is
ever polling. `MainWindow` calls `Shell.activate()` only once a session is
actually ready (not at app startup), and `Shell.stop_all()` on logout — see
`docs/PHASE_4_CORE_FRAMEWORK.md`'s "real bugs caught" section for why this
lifecycle matters (an earlier version started polling before login and got
401s).
