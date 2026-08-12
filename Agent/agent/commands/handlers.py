"""Executes a single command by type, returning the `output` dict that will
be sent back to the backend inside `command_result`.
"""

from __future__ import annotations

import logging
import os
import tempfile

from agent.api import endpoints
from agent.api.client import RestClient
from agent.constants import CommandType
from agent.files import browser, delete, downloader, uploader
from agent.platform import common as platform_common
from agent.power import lock, logout, restart, shutdown
from agent.power import sleep_hibernate

logger = logging.getLogger("agent.commands.handlers")


def _handle_message(payload: dict) -> dict:
    title = payload.get("title") or "Message from EchoDesk"
    message = payload.get("message", "")
    platform_common.show_message(title, message)
    return {"action": "message_request", "shown": True}


def _handle_screenshot(client: RestClient, command_id: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp_dir:
        destination = os.path.join(tmp_dir, f"screenshot_{command_id}.png")
        captured_path = platform_common.take_screenshot(destination)
        with open(captured_path, "rb") as handle:
            content = handle.read()

    logger.info("Uploading screenshot (%d bytes) for command %s", len(content), command_id)
    response = endpoints.upload_command_file(client, command_id, "screenshot.png", content, "image/png")
    file_meta = response.get("data", {})
    return {"action": "screenshot_request", "file_id": file_meta.get("id"), "size_bytes": len(content)}


def execute(command_type: str, client: RestClient, command_id: str, file_root: str | None, payload: dict) -> dict:
    if command_type == CommandType.LOCK.value:
        return lock.execute()
    if command_type == CommandType.RESTART.value:
        return restart.execute()
    if command_type == CommandType.SHUTDOWN.value:
        return shutdown.execute()
    if command_type == CommandType.SLEEP.value:
        return sleep_hibernate.execute_sleep()
    if command_type == CommandType.HIBERNATE.value:
        return sleep_hibernate.execute_hibernate()
    if command_type == CommandType.LOGOUT.value:
        return logout.execute()
    if command_type == CommandType.MESSAGE_REQUEST.value:
        return _handle_message(payload)
    if command_type == CommandType.FILE_LIST_REQUEST.value:
        return browser.list_directory(file_root, payload.get("path", "."))
    if command_type == CommandType.FILE_DOWNLOAD_REQUEST.value:
        return downloader.execute(client, command_id, file_root, payload)
    if command_type == CommandType.FILE_UPLOAD_REQUEST.value:
        return uploader.execute(client, command_id, file_root, payload)
    if command_type == CommandType.DELETE_FILE_REQUEST.value:
        return delete.execute(file_root, payload)
    if command_type == CommandType.SCREENSHOT_REQUEST.value:
        return _handle_screenshot(client, command_id)

    raise ValueError(f"No handler implemented for command_type={command_type}")
