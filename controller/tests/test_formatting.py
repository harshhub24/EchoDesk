"""Unit tests for app.utils.formatting."""

from __future__ import annotations

import datetime

from app.utils.formatting import (
    format_bytes,
    format_gb,
    format_mb,
    format_percent,
    format_relative_time,
    format_uptime,
    parse_backend_timestamp,
)


def test_format_bytes_none_is_dash():
    assert format_bytes(None) == "—"


def test_format_bytes_scales_units():
    assert format_bytes(500) == "500 B"
    assert "KB" in format_bytes(2048)
    assert "MB" in format_bytes(5 * 1024 * 1024)


def test_format_mb_and_gb():
    assert "GB" in format_mb(2048)  # 2048 MB -> 2 GB
    assert "GB" in format_gb(10)


def test_format_percent():
    assert format_percent(None) == "—"
    assert format_percent(42.6) == "43%"


def test_parse_backend_timestamp_handles_naive_and_aware():
    naive = "2026-01-01T12:00:00"
    aware = "2026-01-01T12:00:00Z"
    assert parse_backend_timestamp(naive).tzinfo is not None
    assert parse_backend_timestamp(aware).tzinfo is not None


def test_parse_backend_timestamp_none_and_invalid():
    assert parse_backend_timestamp(None) is None
    assert parse_backend_timestamp("not-a-date") is None


def test_format_relative_time_recent():
    now = datetime.datetime.now(datetime.timezone.utc)
    assert format_relative_time(now.isoformat()) == "Just now"


def test_format_relative_time_minutes_ago():
    ts = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)).isoformat()
    assert "minute" in format_relative_time(ts)


def test_format_relative_time_never_for_missing():
    assert format_relative_time(None) == "Never"


def test_format_uptime():
    assert format_uptime(None) == "—"
    assert format_uptime(65) == "1m"
    assert format_uptime(3665) == "1h 1m"
    assert format_uptime(90065) == "1d 1h 1m"
