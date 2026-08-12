"""Command creation + status polling, shared by File Manager (Phase 9) and
Command Center (Phase 10). Per docs/PHASE_1_ANALYSIS.md: GET /commands
returns status only (no output/result data) and there's no realtime push to
the owner, so this is polling-based, and command_type results are only
inspectable for file-producing commands via the files endpoints below.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer, Signal

from app.api import endpoints
from app.api.client import ApiError
from app.models import Command, CommandFile
from app.services.app_state import AppState
from app.utils.workers import run_async

logger = logging.getLogger("controller.services.command_service")


class CommandService(QObject):
    commands_updated = Signal(list)  # list[Command]
    command_created = Signal(Command)
    command_create_failed = Signal(str)
    refresh_failed = Signal(str)

    def __init__(self, app_state: AppState, poll_interval_seconds: int | None = None):
        super().__init__()
        self.app_state = app_state
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._interval_ms = (poll_interval_seconds or app_state.config.command_poll_interval_seconds) * 1000

    def start(self) -> None:
        self.refresh()
        self._timer.start(self._interval_ms)

    def stop(self) -> None:
        self._timer.stop()

    def refresh(self) -> None:
        run_async(
            self._fetch,
            on_result=self.commands_updated.emit,
            on_error=lambda error, _tb: self.refresh_failed.emit(
                error.message if isinstance(error, ApiError) else str(error)
            ),
        )

    def _fetch(self) -> list[Command]:
        raw = endpoints.list_commands(self.app_state.rest_client)
        commands = [Command.from_dict(c) for c in raw]
        commands.sort(key=lambda c: c.created_at or "", reverse=True)
        return commands

    def send_command(self, device_row_id: str, command_type: str, payload: dict | None = None) -> None:
        run_async(
            endpoints.create_command,
            self.app_state.rest_client,
            device_row_id,
            command_type,
            payload or {},
            on_result=lambda response: self.command_created.emit(Command.from_dict(response["data"])),
            on_error=lambda error, _tb: self.command_create_failed.emit(
                error.message if isinstance(error, ApiError) else str(error)
            ),
        )

    # --- File transfer helpers (used for FILE_DOWNLOAD_REQUEST results,
    # FILE_UPLOAD_REQUEST staging, and SCREENSHOT_REQUEST results) --------------------

    def list_command_files(self, command_id: str, on_result, on_error) -> None:
        run_async(
            lambda: [CommandFile.from_dict(f) for f in endpoints.list_command_files(self.app_state.rest_client, command_id)],
            on_result=on_result,
            on_error=lambda error, _tb: on_error(error.message if isinstance(error, ApiError) else str(error)),
        )

    def upload_file_for_command(self, command_id: str, filename: str, content: bytes, content_type: str, on_result, on_error) -> None:
        run_async(
            endpoints.upload_command_file,
            self.app_state.rest_client,
            command_id,
            filename,
            content,
            content_type,
            on_result=on_result,
            on_error=lambda error, _tb: on_error(error.message if isinstance(error, ApiError) else str(error)),
        )

    def download_command_file(self, command_id: str, file_id: str, on_result, on_error) -> None:
        run_async(
            endpoints.download_command_file,
            self.app_state.rest_client,
            command_id,
            file_id,
            on_result=on_result,
            on_error=lambda error, _tb: on_error(error.message if isinstance(error, ApiError) else str(error)),
        )
