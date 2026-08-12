"""Application-wide constants and enumerations."""

from __future__ import annotations

from enum import Enum


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


COMMAND_TYPES = {command_type.value for command_type in CommandType}
