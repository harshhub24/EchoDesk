"""Hostname info."""

from __future__ import annotations

import socket as stdlib_socket


def get_hostname() -> str:
    return stdlib_socket.gethostname()
