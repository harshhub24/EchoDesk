"""LOCK command handler."""

from __future__ import annotations

import logging

from agent.platform import common as platform_common

logger = logging.getLogger("agent.power.lock")


def execute() -> dict:
    logger.info("Executing LOCK")
    platform_common.lock()
    return {"action": "lock", "initiated": True}
