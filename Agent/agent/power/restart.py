"""RESTART command handler."""

from __future__ import annotations

import logging

from agent.platform import common as platform_common

logger = logging.getLogger("agent.power.restart")


def execute() -> dict:
    logger.info("Executing RESTART")
    platform_common.restart()
    return {"action": "restart", "initiated": True}
