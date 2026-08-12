"""Network telemetry: connectivity status, primary IP, and MAC address."""

from __future__ import annotations

import socket as stdlib_socket

import psutil


def get_network_status() -> str:
    try:
        with stdlib_socket.socket(stdlib_socket.AF_INET, stdlib_socket.SOCK_DGRAM) as sock:
            sock.settimeout(1.0)
            sock.connect(("8.8.8.8", 80))
        return "connected"
    except OSError:
        return "disconnected"


def get_primary_ip() -> str | None:
    try:
        with stdlib_socket.socket(stdlib_socket.AF_INET, stdlib_socket.SOCK_DGRAM) as sock:
            sock.settimeout(1.0)
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None


def get_mac_address() -> str | None:
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
    except Exception:
        return None

    for interface, addr_list in addrs.items():
        if interface == "lo" or interface.lower().startswith("loopback"):
            continue
        if interface not in stats or not stats[interface].isup:
            continue
        for addr in addr_list:
            if addr.family == psutil.AF_LINK:
                return addr.address
    return None


def get_network_info() -> dict:
    return {
        "network_status": get_network_status(),
        "ip_address": get_primary_ip(),
        "mac_address": get_mac_address(),
    }
