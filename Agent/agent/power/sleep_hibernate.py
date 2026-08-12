"""SLEEP / HIBERNATE command handlers.

(Not listed as separate files in the requested structure's power/ folder,
but SLEEP and HIBERNATE are in the required command list, so they live here
rather than being silently dropped.)
"""

from __future__ import annotations

import logging

from agent.platform import common as platform_common

logger = logging.getLogger("agent.power.sleep_hibernate")


def execute_sleep() -> dict:
    logger.info("Executing SLEEP")
    platform_common.sleep()
    return {"action": "sleep", "initiated": True}


def execute_hibernate() -> dict:
    logger.info("Executing HIBERNATE")
    platform_common.hibernate()
    return {"action": "hibernate", "initiated": True}
