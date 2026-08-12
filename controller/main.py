"""EchoDesk Desktop Controller entry point.

Run with: python main.py
"""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from app.config import load_config
from app.constants import APP_NAME, APP_ORG_NAME
from app.services import AppState
from app.theme import apply_theme
from app.utils.logger import setup_logging
from app.views.main_window import MainWindow

logger = logging.getLogger("controller.main")


def main() -> int:
    config = load_config()
    config.ensure_directories()
    setup_logging(config.log_dir, config.log_level)
    logger.info("Starting %s", APP_NAME)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG_NAME)
    apply_theme(app)

    app_state = AppState(config)
    window = MainWindow(app_state)
    window.show()

    app_state.try_restore_session()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
