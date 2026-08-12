# Desktop Controller — Phase 3: Folder Structure

Matches your requested tree exactly. Scaffolded with empty `__init__.py` per
package; no logic yet (that starts Phase 4).

```
controller/
├── app/
│   ├── __init__.py
│   ├── api/            # REST client + one function per backend endpoint
│   ├── auth/            # Token storage/refresh, login orchestration
│   ├── socket/            # Socket.IO client wrapper (background thread + Qt signal bridge)
│   ├── models/              # Dataclasses mirroring backend response shapes
│   ├── services/               # Business logic + AppState (Qt signals), no widget imports
│   ├── views/                     # Pages: Login, Dashboard, Devices, DeviceDetails, FileManager, CommandCenter, ActivityLogs, Notifications, Settings, Profile
│   ├── widgets/                     # Reusable components: cards, sidebar, device tile, charts, toast
│   ├── dialogs/                       # Modals: login errors, confirm-destructive-command, settings, about
│   ├── theme/                           # QSS + color/font tokens
│   ├── assets/                            # Icons, fonts, images
│   ├── utils/                               # Formatting, workers (QThreadPool), logging
│   ├── config/                                # AppConfig (.env loader)
│   └── constants.py                             # CommandType/DeviceStatus/etc, copied verbatim from backend
│
├── logs/         # Rotating controller.log
├── docs/         # This file + the rest of the doc set (Phase 14)
├── tests/        # Phase 13
├── main.py
├── requirements.txt
├── README.md
└── .env.example
```

## Note on the `app/socket` package name

Same category of question as the Agent's `agent/socket/` - here it resolves
itself naturally: `main.py` sits at `controller/` (sibling to `app/`), so
running `python main.py` from `controller/` puts `controller/` (not
`controller/app/`) on `sys.path[0]`. `app` becomes the top-level package,
and the socket module is only ever reachable as `app.socket` - never a bare
top-level `socket` - so there's no collision with the stdlib `socket` module
the way there could have been with the Agent's flatter layout. Internal
imports will still always be fully qualified (`from app.socket import
client`, never a relative bare `import socket` meaning our own package) as
a matter of consistent style with the Agent codebase, but no special
launcher workaround is needed here.
