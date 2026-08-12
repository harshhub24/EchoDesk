"""Constants shared across the Agent.

CommandType/CommandStatus/DeviceStatus values are copied verbatim from the
backend's app/constants.py (EchoDesk backend v0.2.0). Do not add, rename, or
remove values here without a matching backend change - the wire protocol is
these exact strings.
"""

from __future__ import annotations

from enum import Enum


AGENT_NAME = "EchoDesk Agent"
AGENT_VERSION = "1.0.0"

DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 30
DEFAULT_REST_TIMEOUT_SECONDS = 15
DEFAULT_SOCKET_RECONNECT_DELAY_SECONDS = 5
DEFAULT_SOCKET_RECONNECT_DELAY_MAX_SECONDS = 60
MAX_TRANSFERABLE_FILE_SIZE_BYTES = 25 * 1024 * 1024  # must match backend MAX_FILE_SIZE_BYTES

STATE_FILE_NAME = "agent_state.json"
API_KEY_FILE_NAME = "device_credentials.json"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class CommandStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"


class CommandType(str, Enum):
    LOCK = "LOCK"
    RESTART = "RESTART"
    SHUTDOWN = "SHUTDOWN"
    SLEEP = "SLEEP"
    HIBERNATE = "HIBERNATE"
    LOGOUT = "LOGOUT"
    MESSAGE_REQUEST = "MESSAGE_REQUEST"
    FILE_LIST_REQUEST = "FILE_LIST_REQUEST"
    FILE_DOWNLOAD_REQUEST = "FILE_DOWNLOAD_REQUEST"
    FILE_UPLOAD_REQUEST = "FILE_UPLOAD_REQUEST"
    DELETE_FILE_REQUEST = "DELETE_FILE_REQUEST"
    SCREENSHOT_REQUEST = "SCREENSHOT_REQUEST"


KNOWN_COMMAND_TYPES = {member.value for member in CommandType}


class TransferDirection(str, Enum):
    DEVICE_TO_OWNER = "device_to_owner"
    OWNER_TO_DEVICE = "owner_to_device"


class Platform(str, Enum):
    LINUX = "linux"
    WINDOWS = "windows"
    UNKNOWN = "unknown"
