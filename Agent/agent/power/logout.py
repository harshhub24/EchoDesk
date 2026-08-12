"""LOGOUT command handler."""

from __future__ import annotations

import logging

from agent.platform import common as platform_common

logger = logging.getLogger("agent.power.logout")


def execute() -> dict:
    logger.info("Executing LOGOUT")
    platform_common.logout()
    return {"action": "logout", "initiated": True}
