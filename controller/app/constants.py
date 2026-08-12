"""Constants mirrored verbatim from the backend (app/constants.py) and the
Agent (agent/constants.py). Do not add/rename/remove values here without a
matching backend change - the wire protocol is these exact strings. See
docs/PHASE_1_ANALYSIS.md for the source-of-truth verification.
"""

from __future__ import annotations

from enum import Enum

APP_NAME = "EchoDesk Controller"
APP_VERSION = "1.0.0"
APP_ORG_NAME = "EchoDesk"

DEFAULT_DEVICE_POLL_INTERVAL_SECONDS = 30
DEFAULT_COMMAND_POLL_INTERVAL_SECONDS = 5
DEFAULT_REST_TIMEOUT_SECONDS = 15
ACCESS_TOKEN_REFRESH_MARGIN_SECONDS = 120  # refresh this many seconds before the 15-min expiry


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

# Human-friendly labels for the Command Center UI (Phase 10).
COMMAND_TYPE_LABELS: dict[str, str] = {
    CommandType.LOCK.value: "Lock",
    CommandType.RESTART.value: "Restart",
    CommandType.SHUTDOWN.value: "Shutdown",
    CommandType.SLEEP.value: "Sleep",
    CommandType.HIBERNATE.value: "Hibernate",
    CommandType.LOGOUT.value: "Log Out",
    CommandType.MESSAGE_REQUEST.value: "Send Message",
    CommandType.FILE_LIST_REQUEST.value: "List Files",
    CommandType.FILE_DOWNLOAD_REQUEST.value: "Download File",
    CommandType.FILE_UPLOAD_REQUEST.value: "Upload File",
    CommandType.DELETE_FILE_REQUEST.value: "Delete File",
    CommandType.SCREENSHOT_REQUEST.value: "Screenshot",
}

# Commands sendable as one-click "quick actions" with no extra payload
# fields required from the operator.
QUICK_ACTION_COMMAND_TYPES = (
    CommandType.LOCK.value,
    CommandType.RESTART.value,
    CommandType.SHUTDOWN.value,
    CommandType.SLEEP.value,
    CommandType.HIBERNATE.value,
    CommandType.LOGOUT.value,
    CommandType.SCREENSHOT_REQUEST.value,
)


class NotificationCategory(str, Enum):
    """Mirrors app/models/notification.py's free-form `category` field.
    No backend code currently writes any of these (see PHASE_1_ANALYSIS.md
    gap #Notifications) - kept here so the UI has consistent icon/color
    mapping ready for whenever the backend starts populating them.
    """

    DEVICE_ONLINE = "device_online"
    DEVICE_OFFLINE = "device_offline"
    COMMAND_SUCCESS = "command_success"
    COMMAND_FAILED = "command_failed"
    SYSTEM_ALERT = "system_alert"
    GENERAL = "general"
