"""Shared fixtures for Agent tests."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agent.api.client import RestClient
from agent.config import AgentConfig


@pytest.fixture()
def tmp_data_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture()
def agent_config(tmp_data_dir):
    return AgentConfig(
        backend_url="http://testserver",
        api_prefix="/api/v1",
        verify_tls=False,
        api_key=None,
        bootstrap_email=None,
        bootstrap_password=None,
        device_name="Test Device",
        device_type="linux",
        heartbeat_interval_seconds=30,
        rest_timeout_seconds=5,
        data_dir=tmp_data_dir,
        log_dir=tmp_data_dir / "logs",
        log_level="DEBUG",
        file_manager_root=None,
    )


@pytest.fixture()
def mock_rest_client():
    client = MagicMock(spec=RestClient)
    return client


@pytest.fixture()
def mock_socket_client():
    client = MagicMock()
    client.connected = True
    return client
