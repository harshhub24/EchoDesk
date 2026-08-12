"""File Manager page.

Download, Upload, and Delete are fully functional (they use the backend's
working command-file endpoints). Directory listing (FILE_LIST_REQUEST) is
NOT functional today and is labeled as such rather than faked: its result
only ever exists inside `command_result.output`, which travels over
Socket.IO to whichever client sent the ack/result (the Agent) - never
broadcast to the owner. See docs/PHASE_1_ANALYSIS.md §8 and
docs/COMMAND_FLOW.md for the full explanation. Because there's no path
without a backend or Agent change (both explicitly off-limits for this
build), the operator must know the exact remote path for every operation
here rather than browsing to it.
"""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.constants import CommandType
from app.models import Command, Device
from app.services.app_state import AppState
from app.services.command_service import CommandService
from app.services.device_service import DeviceListService
from app.theme import COLORS, SPACING, command_status_color
from app.utils.formatting import format_relative_time
from app.widgets.card import GlassCard

logger = logging.getLogger("controller.views.file_manager")

_FILE_COMMAND_TYPES = {
    CommandType.FILE_LIST_REQUEST.value,
    CommandType.FILE_DOWNLOAD_REQUEST.value,
    CommandType.FILE_UPLOAD_REQUEST.value,
    CommandType.DELETE_FILE_REQUEST.value,
}

_DOWNLOADABLE_TYPES = {CommandType.FILE_DOWNLOAD_REQUEST.value, CommandType.SCREENSHOT_REQUEST.value}


class FileManagerView(QWidget):
    def __init__(self, app_state: AppState, parent: QWidget | None = None):
        super().__init__(parent)
        self.app_state = app_state
        self.device_service = DeviceListService(app_state)
        self.command_service = CommandService(app_state)
        self._devices: list[Device] = []
        self._commands: list[Command] = []
        self._pending_upload_content: bytes | None = None
        self._pending_upload_filename: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        heading = QLabel("File Manager")
        heading.setProperty("cssClass", "heading")
        layout.addWidget(heading)

        limitation_note = QLabel(
            "Directory browsing isn't available yet - the backend doesn't currently expose a command's "
            "result to this app (see docs/COMMAND_FLOW.md). You can still download, upload, and delete "
            "files by exact path below."
        )
        limitation_note.setProperty("cssClass", "muted")
        limitation_note.setWordWrap(True)
        layout.addWidget(limitation_note)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {COLORS.danger};")
        self.error_label.hide()
        layout.addWidget(self.error_label)

        device_row = QHBoxLayout()
        device_row.addWidget(QLabel("Device:"))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(240)
        device_row.addWidget(self.device_combo)
        device_row.addStretch()
        layout.addLayout(device_row)

        actions_card = GlassCard()
        actions_title = QLabel("File Operations")
        actions_title.setProperty("cssClass", "subtitle")
        actions_card.body_layout.addWidget(actions_title)

        path_row = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Remote file path, e.g. /home/user/report.txt")
        path_row.addWidget(self.path_input, stretch=1)
        actions_card.body_layout.addLayout(path_row)

        buttons_row = QHBoxLayout()
        self.list_button = QPushButton("Request Listing (status only)")
        self.list_button.setProperty("cssClass", "ghost")
        self.list_button.clicked.connect(self._on_list_clicked)

        self.download_button = QPushButton("Download File")
        self.download_button.setProperty("cssClass", "primary")
        self.download_button.clicked.connect(self._on_download_clicked)

        self.delete_button = QPushButton("Delete File")
        self.delete_button.setProperty("cssClass", "danger")
        self.delete_button.clicked.connect(self._on_delete_clicked)

        buttons_row.addWidget(self.list_button)
        buttons_row.addWidget(self.download_button)
        buttons_row.addWidget(self.delete_button)
        actions_card.body_layout.addLayout(buttons_row)

        upload_row = QHBoxLayout()
        self.choose_file_button = QPushButton("Choose Local File...")
        self.choose_file_button.setProperty("cssClass", "ghost")
        self.choose_file_button.clicked.connect(self._on_choose_file)

        self.upload_destination_input = QLineEdit()
        self.upload_destination_input.setPlaceholderText("Destination path on device, e.g. /home/user/incoming.txt")

        self.upload_button = QPushButton("Upload File")
        self.upload_button.setProperty("cssClass", "primary")
        self.upload_button.clicked.connect(self._on_upload_clicked)

        upload_row.addWidget(self.choose_file_button)
        upload_row.addWidget(self.upload_destination_input, stretch=1)
        upload_row.addWidget(self.upload_button)
        actions_card.body_layout.addLayout(upload_row)

        self.selected_file_label = QLabel("No local file chosen")
        self.selected_file_label.setProperty("cssClass", "muted")
        actions_card.body_layout.addWidget(self.selected_file_label)

        layout.addWidget(actions_card)

        history_card = GlassCard()
        history_title = QLabel("File Command History")
        history_title.setProperty("cssClass", "subtitle")
        history_card.body_layout.addWidget(history_title)

        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(["Type", "Path", "Status", "Sent", "Action"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        history_card.body_layout.addWidget(self.history_table)
        layout.addWidget(history_card, stretch=1)

        self.device_service.devices_updated.connect(self._on_devices_updated)
        self.command_service.commands_updated.connect(self._on_commands_updated)
        self.command_service.command_created.connect(self._on_command_created)
        self.command_service.command_create_failed.connect(self._on_command_error)

    def start(self) -> None:
        self.device_service.start()
        self.command_service.start()

    def stop(self) -> None:
        self.device_service.stop()
        self.command_service.stop()

    def _selected_device_id(self) -> str | None:
        return self.device_combo.currentData()

    def _on_devices_updated(self, devices: list[Device]) -> None:
        self._devices = devices
        current = self.device_combo.currentData()
        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        for device in devices:
            self.device_combo.addItem(device.device_name, device.id)
        if current:
            index = self.device_combo.findData(current)
            if index >= 0:
                self.device_combo.setCurrentIndex(index)
        self.device_combo.blockSignals(False)

    def _require_device_and_path(self) -> tuple[str, str] | None:
        device_id = self._selected_device_id()
        path = self.path_input.text().strip()
        if not device_id:
            self._show_error("Select a device first.")
            return None
        if not path:
            self._show_error("Enter a remote file path.")
            return None
        self.error_label.hide()
        return device_id, path

    def _on_list_clicked(self) -> None:
        target = self._require_device_and_path()
        if not target:
            return
        device_id, path = target
        self.command_service.send_command(device_id, CommandType.FILE_LIST_REQUEST.value, {"path": path})

    def _on_download_clicked(self) -> None:
        target = self._require_device_and_path()
        if not target:
            return
        device_id, path = target
        self.command_service.send_command(device_id, CommandType.FILE_DOWNLOAD_REQUEST.value, {"path": path})

    def _on_delete_clicked(self) -> None:
        target = self._require_device_and_path()
        if not target:
            return
        device_id, path = target
        confirm = QMessageBox.question(
            self, "Delete File", f"Delete '{path}' on the device? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.command_service.send_command(device_id, CommandType.DELETE_FILE_REQUEST.value, {"path": path})

    def _on_choose_file(self) -> None:
        file_path, _filter = QFileDialog.getOpenFileName(self, "Choose file to upload")
        if not file_path:
            return
        with open(file_path, "rb") as handle:
            self._pending_upload_content = handle.read()
        import os

        self._pending_upload_filename = os.path.basename(file_path)
        self.selected_file_label.setText(f"Selected: {self._pending_upload_filename} ({len(self._pending_upload_content)} bytes)")

    def _on_upload_clicked(self) -> None:
        device_id = self._selected_device_id()
        destination = self.upload_destination_input.text().strip()
        if not device_id:
            self._show_error("Select a device first.")
            return
        if not destination:
            self._show_error("Enter a destination path on the device.")
            return
        if not self._pending_upload_content:
            self._show_error("Choose a local file to upload first.")
            return

        self.error_label.hide()
        self.command_service.send_command(device_id, CommandType.FILE_UPLOAD_REQUEST.value, {"destination_path": destination})
        # The actual bytes are attached once the command exists - handled in
        # _on_command_created for FILE_UPLOAD_REQUEST commands.
        self._awaiting_upload_attach = True

    def _on_command_created(self, command: Command) -> None:
        if command.command_type == CommandType.FILE_UPLOAD_REQUEST.value and self._pending_upload_content:
            content, filename = self._pending_upload_content, self._pending_upload_filename or "upload.bin"
            self.command_service.upload_file_for_command(
                command.id, filename, content, "application/octet-stream",
                on_result=lambda _r: logger.info("Upload attached to command %s", command.id),
                on_error=lambda msg: self._show_error(f"Upload attach failed: {msg}"),
            )
            self._pending_upload_content = None
            self._pending_upload_filename = None
            self.selected_file_label.setText("No local file chosen")
        self.command_service.refresh()

    def _on_command_error(self, message: str) -> None:
        self._show_error(f"Could not send command: {message}")

    def _on_commands_updated(self, commands: list[Command]) -> None:
        device_id = self._selected_device_id()
        relevant = [
            c for c in commands
            if c.command_type in _FILE_COMMAND_TYPES and (not device_id or c.device_id == device_id)
        ]
        self._commands = relevant
        self._render_history(relevant)

    def _render_history(self, commands: list[Command]) -> None:
        self.history_table.setRowCount(len(commands))
        for row, command in enumerate(commands):
            self.history_table.setItem(row, 0, QTableWidgetItem(command.command_type))
            path = command.payload.get("path") or command.payload.get("destination_path") or "—"
            self.history_table.setItem(row, 1, QTableWidgetItem(path))

            from PySide6.QtGui import QColor

            status_item = QTableWidgetItem(command.status.capitalize())
            status_item.setForeground(QColor(command_status_color(command.status)))
            self.history_table.setItem(row, 2, status_item)

            self.history_table.setItem(row, 3, QTableWidgetItem(format_relative_time(command.created_at)))

            if command.command_type in _DOWNLOADABLE_TYPES and command.status == "success":
                save_button = QPushButton("Save As...")
                save_button.setProperty("cssClass", "ghost")
                save_button.clicked.connect(lambda _checked=False, c=command: self._save_command_file(c))
                self.history_table.setCellWidget(row, 4, save_button)
            else:
                self.history_table.setCellWidget(row, 4, None)

    def _save_command_file(self, command: Command) -> None:
        self.command_service.list_command_files(
            command.id,
            on_result=lambda files: self._pick_and_save_file(command, files),
            on_error=lambda msg: self._show_error(f"Could not list files: {msg}"),
        )

    def _pick_and_save_file(self, command: Command, files) -> None:
        candidates = [f for f in files if f.direction == "device_to_owner"]
        if not candidates:
            self._show_error("No file has been received from the device for this command yet.")
            return
        file_meta = sorted(candidates, key=lambda f: f.created_at or "")[-1]

        save_path, _filter = QFileDialog.getSaveFileName(self, "Save file as", file_meta.original_filename)
        if not save_path:
            return

        self.command_service.download_command_file(
            command.id,
            file_meta.id,
            on_result=lambda content: self._write_saved_file(save_path, content),
            on_error=lambda msg: self._show_error(f"Download failed: {msg}"),
        )

    def _write_saved_file(self, save_path: str, content: bytes) -> None:
        with open(save_path, "wb") as handle:
            handle.write(content)
        QMessageBox.information(self, "Saved", f"File saved to {save_path}")

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()
