#!/usr/bin/env python3
"""EchoDesk Agent launcher.

Run this file, not agent/main.py directly:

    python run.py

Why this file exists: the project has packages literally named `agent/socket`
and `agent/platform` (matching the requested project layout). If you run
`agent/main.py` directly (`cd agent && python main.py`), Python puts
`agent/`'s own directory at the front of sys.path, which would shadow the
*stdlib* `socket` and `platform` modules for every third-party dependency
that needs them (psutil, requests, python-socketio, ...) - causing very
confusing, hard-to-diagnose import errors.

Running from here instead means the *parent* directory (this file's
directory, which contains `agent/`) is what lands on sys.path, so `agent` is
imported as a normal package and `agent.socket` / `agent.platform` never
collide with the real `socket` / `platform` modules.

For services (systemd / Windows Service) and PyInstaller builds, point at
this file as the entry point - see agent/docs/INSTALLATION.md.
"""

from __future__ import annotations

import runpy


if __name__ == "__main__":
    runpy.run_module("agent.main", run_name="__main__")
