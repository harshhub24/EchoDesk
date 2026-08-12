"""EchoDesk Device Agent.

Cross-platform (Linux Mint primary, Windows 10/11 secondary) background
service that registers a device with the EchoDesk backend, sends periodic
heartbeats with telemetry, and executes remote commands (power actions,
messages, file transfer, screenshots) over REST + Socket.IO.

Always import submodules with the `agent.` prefix (e.g. `from agent.system
import cpu`), and always start the process via the repo-root `run.py`, not
`agent/main.py` directly - see run.py's module docstring for why.
"""

from __future__ import annotations

__version__ = "1.0.0"
