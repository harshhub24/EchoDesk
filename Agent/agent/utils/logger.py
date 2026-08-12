"""Rotating log setup, shared by every Agent module.

Call setup_logging() exactly once, early in agent.main. Every other module
just does `logger = logging.getLogger(__name__)` as usual.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_dir: Path, level: str = "INFO", max_bytes: int = 5 * 1024 * 1024, backup_count: int = 5) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "agent.log"

    root_logger = logging.getLogger("agent")
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.handlers.clear()
    root_logger.propagate = False

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Quiet down noisy third-party libraries unless we're in DEBUG.
    if root_logger.level > logging.DEBUG:
        for noisy in ("urllib3", "engineio.client", "socketio.client"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    return root_logger
