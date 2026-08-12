# Project Structure

```
(repo root)/
├── run.py                     # THE entry point - always start here (see its docstring)
└── agent/
    ├── __init__.py
    ├── main.py                 # Wires everything together; Agent class + run_forever()
    ├── config.py                # AgentConfig, loaded from env / agent/.env
    ├── constants.py              # CommandType/CommandStatus/DeviceStatus - mirrors backend exactly
    ├── requirements.txt
    ├── README.md
    ├── .env.example
    │
    ├── api/
    │   ├── client.py            # RestClient: httpx wrapper, auth headers, retry/backoff
    │   ├── auth.py               # Enrollment/bootstrap flow, local credential persistence
    │   └── endpoints.py           # One typed function per backend REST route used
    │
    ├── socket/
    │   ├── client.py             # SocketClient: python-socketio wrapper, reconnect, emitters
    │   └── events.py               # Wires `command_created` to the dispatcher
    │
    ├── heartbeat/
    │   └── heartbeat.py           # HeartbeatLoop: telemetry every N seconds (REST + socket)
    │
    ├── commands/
    │   ├── dispatcher.py          # CommandDispatcher: validate -> ack -> execute -> report
    │   ├── handlers.py             # Maps command_type -> handler implementation
    │   └── validator.py            # Envelope/payload validation, expiry check
    │
    ├── platform/
    │   ├── common.py              # OS detection + dispatch (the ONLY branch point)
    │   ├── linux.py                # systemctl/loginctl/notify-send/mss backend
    │   └── windows.py               # shutdown.exe/rundll32/ctypes/mss backend
    │
    ├── system/
    │   ├── device.py               # Local device_id (UUID) persistence, telemetry aggregation
    │   ├── cpu.py / ram.py / disk.py / battery.py / network.py / hostname.py
    │
    ├── files/
    │   ├── browser.py              # FILE_LIST_REQUEST + resolve_safe_path (shared path-safety helper)
    │   ├── downloader.py            # FILE_DOWNLOAD_REQUEST (device -> owner)
    │   ├── uploader.py               # FILE_UPLOAD_REQUEST (owner -> device)
    │   └── delete.py                  # DELETE_FILE_REQUEST
    │
    ├── power/
    │   ├── lock.py / restart.py / shutdown.py / logout.py
    │   └── sleep_hibernate.py        # SLEEP + HIBERNATE
    │
    ├── services/
    │   ├── installer.py             # OS-dispatching install/uninstall entry point
    │   ├── linux_service.py          # systemd unit generation + install/uninstall
    │   └── windows_service.py         # pywin32 ServiceFramework wrapper
    │
    ├── utils/
    │   ├── logger.py                 # Rotating file + console logging setup
    │   └── retry.py                    # tenacity-based network retry decorator
    │
    ├── logs/                          # Runtime logs land here (agent.log, rotated)
    │
    ├── installer/
    │   ├── linux/
    │   │   ├── install.sh / uninstall.sh
    │   │   └── echodesk-agent.service   # Reference copy of the generated systemd unit
    │   └── windows/
    │       └── install.ps1 / uninstall.ps1
    │
    ├── tests/
    │   ├── conftest.py
    │   ├── test_api_client.py            # REST client, mocked transport
    │   ├── test_commands.py               # Validator + dispatcher, mocked I/O
    │   ├── test_files.py                   # Path safety + file manager
    │   ├── test_socket_client.py            # Socket wiring, mocked socketio.Client
    │   ├── test_system_info.py               # Real psutil collectors
    │   └── test_integration_backend.py        # Live in-process backend + full round trip
    │
    └── docs/
        ├── INSTALLATION.md
        ├── API_INTEGRATION.md
        ├── COMMAND_FLOW.md
        ├── PROJECT_STRUCTURE.md (this file)
        └── CHANGELOG.md
```

## Why `agent/socket/` and `agent/platform/` don't break stdlib `socket`/`platform`

Every internal import in this codebase is fully qualified
(`from agent.socket.client import ...`, `from agent.platform import common
as platform_common`, etc.) - never a bare `import socket` or `import
platform` from inside the `agent` package pointing at the wrong thing. As
long as the process is started via `run.py` (or `python -m agent.main` from
the directory *containing* `agent/`), Python never puts `agent/` itself at
the front of `sys.path`, so `agent.socket`/`agent.platform` and the real
stdlib `socket`/`platform` coexist without collision. See `run.py`'s
docstring for the failure mode this avoids.

## Design choices worth knowing about

- **Enrollment happens once.** After the first successful run, the Agent
  never calls `/devices/register` again - it just heartbeats using the
  persisted device API key. Re-run with bootstrap credentials (after
  deleting `agent/device_credentials.json`) if you need to update
  `device_name`/`hostname`/`operating_system` on the backend.
- **REST is the heartbeat source of truth**; the socket heartbeat is a
  bonus, sent only if the socket happens to already be connected.
- **`command_ack`/`command_result` only travel over the socket** (no REST
  equivalent exists on the backend) - see `commands/dispatcher.py`'s
  in-memory retry queue for how the Agent copes with the socket being down
  at the exact moment a command finishes.
