"""SHUTDOWN command handler."""

from __future__ import annotations

import logging

from agent.platform import common as platform_common

logger = logging.getLogger("agent.power.shutdown")


def execute() -> dict:
    logger.info("Executing SHUTDOWN")
    platform_common.shutdown()
    return {"action": "shutdown", "initiated": True}
