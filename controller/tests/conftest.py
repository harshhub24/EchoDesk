"""Shared fixtures. pytest-qt provides `qtbot`/`qapp` automatically."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.config import AppConfig


@pytest.fixture()
def tmp_data_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture()
def app_config(tmp_data_dir):
    return AppConfig(
        backend_url="http://testserver",
        api_prefix="/api/v1",
        verify_tls=False,
        rest_timeout_seconds=5,
        device_poll_interval_seconds=30,
        command_poll_interval_seconds=5,
        data_dir=tmp_data_dir,
        log_dir=tmp_data_dir / "logs",
        log_level="DEBUG",
    )
