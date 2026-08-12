"""Command Center page. Sends commands via POST /commands (existing route,
broadcasts command_created to the Agent) and shows status via polling
GET /commands - see docs/PHASE_1_ANALYSIS.md for why status (not full
execution output) is what's available for most command types here; file-
producing commands (SCREENSHOT_REQUEST) get a "View" action using the
working files endpoints, same pattern as File Manager.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
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

from app.constants import COMMAND_TYPE_LABELS, QUICK_ACTION_COMMAND_TYPES, CommandType
from app.models import Command, Device
from app.services.app_state import AppState
from app.services.command_service import CommandService
from app.services.device_service import DeviceListService
from app.theme import COLORS, SPACING, command_status_color
from app.utils.formatting import format_relative_time
from app.widgets.card import GlassCard

_DESTRUCTIVE_TYPES = {
    CommandType.SHUTDOWN.value,
    CommandType.RESTART.value,
    CommandType.LOGOUT.value,
    CommandType.HIBERNATE.value,
}

_RESULT_VIEWABLE_TYPES = {CommandType.SCREENSHOT_REQUEST.value, CommandType.FILE_DOWNLOAD_REQUEST.value}


class CommandCenterView(QWidget):
    def __init__(self, app_state: AppState, parent: QWidget | None = None):
        super().__init__(parent)
        self.app_state = app_state
        self.device_service = DeviceListService(app_state)
        self.command_service = CommandService(app_state)
        self._devices: list[Device] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        heading = QLabel("Command Center")
        heading.setProperty("cssClass", "heading")
        layout.addWidget(heading)

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
        actions_title = QLabel("Quick Actions")
        actions_title.setProperty("cssClass", "subtitle")
        actions_card.body_layout.addWidget(actions_title)

        actions_grid = QGridLayout()
        for index, command_type in enumerate(QUICK_ACTION_COMMAND_TYPES):
            label = COMMAND_TYPE_LABELS.get(command_type, command_type)
            button = QPushButton(label)
            button.setProperty("cssClass", "danger" if command_type in _DESTRUCTIVE_TYPES else "primary")
            button.clicked.connect(lambda _checked=False, ct=command_type, lbl=label: self._send_quick_action(ct, lbl))
            actions_grid.addWidget(button, index // 4, index % 4)
        actions_card.body_layout.addLayout(actions_grid)
        layout.addWidget(actions_card)

        message_card = GlassCard()
        message_title = QLabel("Send Message")
        message_title.setProperty("cssClass", "subtitle")
        message_card.body_layout.addWidget(message_title)

        message_row = QHBoxLayout()
        self.message_title_input = QLineEdit()
        self.message_title_input.setPlaceholderText("Title (optional)")
        self.message_body_input = QLineEdit()
        self.message_body_input.setPlaceholderText("Message to show on the device...")
        send_message_button = QPushButton("Send")
        send_message_button.setProperty("cssClass", "primary")
        send_message_button.clicked.connect(self._send_message)
        message_row.addWidget(self.message_title_input)
        message_row.addWidget(self.message_body_input, stretch=1)
        message_row.addWidget(send_message_button)
        message_card.body_layout.addLayout(message_row)
        layout.addWidget(message_card)

        history_card = GlassCard()
        history_title = QLabel("Command History")
        history_title.setProperty("cssClass", "subtitle")
        history_card.body_layout.addWidget(history_title)

        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(["Command", "Status", "Sent", "Device", "Result"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        history_card.body_layout.addWidget(self.history_table)
        layout.addWidget(history_card, stretch=1)

        self.device_service.devices_updated.connect(self._on_devices_updated)
        self.command_service.commands_updated.connect(self._on_commands_updated)
        self.command_service.command_created.connect(lambda _c: self.command_service.refresh())
        self.command_service.command_create_failed.connect(self._on_command_error)

    def start(self) -> None:
        self.device_service.start()
        self.command_service.start()

    def stop(self) -> None:
        self.device_service.stop()
        self.command_service.stop()

    def _selected_device_id(self) -> str | None:
        return self.device_combo.currentData()

    def _device_name(self, device_id: str) -> str:
        for device in self._devices:
            if device.id == device_id:
                return device.device_name
        return device_id

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

    def _send_quick_action(self, command_type: str, label: str) -> None:
        device_id = self._selected_device_id()
        if not device_id:
            self._show_error("Select a device first.")
            return

        if command_type in _DESTRUCTIVE_TYPES:
            confirm = QMessageBox.question(
                self,
                f"Confirm {label}",
                f"Send '{label}' to {self._device_name(device_id)}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

        self.error_label.hide()
        self.command_service.send_command(device_id, command_type, {})

    def _send_message(self) -> None:
        device_id = self._selected_device_id()
        message = self.message_body_input.text().strip()
        if not device_id:
            self._show_error("Select a device first.")
            return
        if not message:
            self._show_error("Enter a message to send.")
            return

        self.error_label.hide()
        payload = {"message": message}
        title = self.message_title_input.text().strip()
        if title:
            payload["title"] = title
        self.command_service.send_command(device_id, CommandType.MESSAGE_REQUEST.value, payload)
        self.message_body_input.clear()

    def _on_command_error(self, message: str) -> None:
        self._show_error(f"Could not send command: {message}")

    def _on_commands_updated(self, commands: list[Command]) -> None:
        self._render_history(commands[:50])

    def _render_history(self, commands: list[Command]) -> None:
        from PySide6.QtGui import QColor

        self.history_table.setRowCount(len(commands))
        for row, command in enumerate(commands):
            label = COMMAND_TYPE_LABELS.get(command.command_type, command.command_type)
            self.history_table.setItem(row, 0, QTableWidgetItem(label))

            status_item = QTableWidgetItem(command.status.capitalize())
            status_item.setForeground(QColor(command_status_color(command.status)))
            self.history_table.setItem(row, 1, status_item)

            self.history_table.setItem(row, 2, QTableWidgetItem(format_relative_time(command.created_at)))
            self.history_table.setItem(row, 3, QTableWidgetItem(self._device_name(command.device_id)))

            if command.command_type in _RESULT_VIEWABLE_TYPES and command.status == "success":
                view_button = QPushButton("View / Save...")
                view_button.setProperty("cssClass", "ghost")
                view_button.clicked.connect(lambda _checked=False, c=command: self._view_result(c))
                self.history_table.setCellWidget(row, 4, view_button)
            else:
                self.history_table.setCellWidget(row, 4, None)
                note = "" if command.status in ("pending", "delivered", "executing") else "No viewable result"
                self.history_table.setItem(row, 4, QTableWidgetItem(note))

    def _view_result(self, command: Command) -> None:
        self.command_service.list_command_files(
            command.id,
            on_result=lambda files: self._pick_and_save(command, files),
            on_error=lambda msg: self._show_error(f"Could not list result files: {msg}"),
        )

    def _pick_and_save(self, command: Command, files) -> None:
        candidates = [f for f in files if f.direction == "device_to_owner"]
        if not candidates:
            self._show_error("No result file has arrived from the device yet.")
            return
        file_meta = sorted(candidates, key=lambda f: f.created_at or "")[-1]

        save_path, _filter = QFileDialog.getSaveFileName(self, "Save result as", file_meta.original_filename)
        if not save_path:
            return

        self.command_service.download_command_file(
            command.id,
            file_meta.id,
            on_result=lambda content: self._write_file(save_path, content),
            on_error=lambda msg: self._show_error(f"Download failed: {msg}"),
        )

    def _write_file(self, save_path: str, content: bytes) -> None:
        with open(save_path, "wb") as handle:
            handle.write(content)
        QMessageBox.information(self, "Saved", f"Result saved to {save_path}")

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()
