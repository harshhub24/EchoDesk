"""Device Details page. Shows everything DeviceResponse actually returns
(see docs/PHASE_1_ANALYSIS.md §2) - deliberately does not show "Installed
Agent Version" or "Temperature" since no backend field exists for either.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.api import endpoints
from app.api.client import ApiError
from app.models import Device
from app.services.app_state import AppState
from app.services.device_service import DeviceDetailService
from app.theme import COLORS, SPACING, status_color
from app.utils.formatting import format_bytes, format_gb, format_percent, format_relative_time, format_uptime
from app.utils.workers import run_async
from app.widgets.card import GlassCard
from app.widgets.telemetry_chart import RollingLineChart

logger = logging.getLogger("controller.views.device_details")


def _info_row(label_text: str) -> tuple[QWidget, QLabel]:
    label = QLabel(label_text)
    label.setProperty("cssClass", "muted")
    value = QLabel("—")
    return label, value


class DeviceDetailsView(QWidget):
    back_requested = Signal()
    device_deleted = Signal()

    def __init__(self, app_state: AppState, parent: QWidget | None = None):
        super().__init__(parent)
        self.app_state = app_state
        self.service = DeviceDetailService(app_state)
        self.current_device: Device | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        header_row = QHBoxLayout()
        back_button = QPushButton("← Back to Devices")
        back_button.setProperty("cssClass", "ghost")
        back_button.clicked.connect(self.back_requested)
        header_row.addWidget(back_button)
        header_row.addStretch()

        self.delete_button = QPushButton("Delete Device")
        self.delete_button.setProperty("cssClass", "danger")
        self.delete_button.clicked.connect(self._on_delete_clicked)
        header_row.addWidget(self.delete_button)
        layout.addLayout(header_row)

        self.name_label = QLabel("")
        self.name_label.setProperty("cssClass", "heading")
        layout.addWidget(self.name_label)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {COLORS.danger};")
        self.error_label.hide()
        layout.addWidget(self.error_label)

        info_row = QHBoxLayout()
        info_row.setSpacing(SPACING.md)

        self._system_card, self._system_fields = self._build_info_card(
            "System Information", ["Status", "Hostname", "Operating System", "Last Seen"]
        )
        self._network_card, self._network_fields = self._build_info_card(
            "Network", ["IP Address", "MAC Address", "Network Status"]
        )
        self._hardware_card, self._hardware_fields = self._build_info_card(
            "Hardware & Storage", ["Disk Usage", "Battery", "Uptime"]
        )

        info_row.addWidget(self._system_card)
        info_row.addWidget(self._network_card)
        info_row.addWidget(self._hardware_card)
        layout.addLayout(info_row)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(SPACING.md)
        self.cpu_chart = RollingLineChart("CPU Usage", "%")
        self.ram_chart = RollingLineChart("RAM Usage", "%")
        charts_row.addWidget(self.cpu_chart)
        charts_row.addWidget(self.ram_chart)
        layout.addLayout(charts_row, stretch=1)

        self.service.device_updated.connect(self._on_device_updated)
        self.service.device_not_found.connect(self._on_device_not_found)
        self.service.refresh_failed.connect(self._on_refresh_failed)

    def _build_info_card(self, title: str, field_names: list[str]) -> tuple[GlassCard, dict[str, QLabel]]:
        card = GlassCard()
        title_label = QLabel(title)
        title_label.setProperty("cssClass", "subtitle")
        card.body_layout.addWidget(title_label)

        grid = QGridLayout()
        fields: dict[str, QLabel] = {}
        for row, field_name in enumerate(field_names):
            label, value = _info_row(field_name)
            grid.addWidget(label, row, 0)
            grid.addWidget(value, row, 1)
            fields[field_name] = value
        card.body_layout.addLayout(grid)
        card.body_layout.addStretch()
        return card, fields

    def set_device(self, device_id: str) -> None:
        self.service.set_device(device_id)
        self.cpu_chart.clear_points()
        self.ram_chart.clear_points()

    def start(self) -> None:
        self.service.start()

    def stop(self) -> None:
        self.service.stop()

    def _on_device_updated(self, device: Device) -> None:
        self.current_device = device
        self.error_label.hide()

        self.name_label.setText(device.device_name)

        status_label = self._system_fields["Status"]
        status_label.setText(device.status.capitalize())
        status_label.setStyleSheet(f"color: {status_color(device.status)}; font-weight: 600;")
        self._system_fields["Hostname"].setText(device.hostname or "—")
        self._system_fields["Operating System"].setText(device.operating_system or "—")
        self._system_fields["Last Seen"].setText(format_relative_time(device.last_seen_at))

        t = device.telemetry
        self._network_fields["IP Address"].setText(t.ip_address or "—")
        self._network_fields["MAC Address"].setText(t.mac_address or "—")
        self._network_fields["Network Status"].setText((t.network_status or "unknown").capitalize())

        disk_text = "—"
        if t.disk_percent is not None:
            disk_text = f"{format_percent(t.disk_percent)} ({format_gb(t.disk_used_gb)} / {format_gb(t.disk_total_gb)})"
        self._hardware_fields["Disk Usage"].setText(disk_text)

        battery_text = "No battery" if t.battery_percent is None else f"{format_percent(t.battery_percent)}{' (charging)' if t.battery_charging else ''}"
        self._hardware_fields["Battery"].setText(battery_text)
        self._hardware_fields["Uptime"].setText(format_uptime(t.uptime_seconds))

        self.cpu_chart.add_point(t.cpu_percent)
        self.ram_chart.add_point(t.ram_percent)

    def _on_device_not_found(self) -> None:
        self.error_label.setText("This device no longer exists (it may have been deleted).")
        self.error_label.show()
        self.service.stop()

    def _on_refresh_failed(self, message: str) -> None:
        self.error_label.setText(f"Could not refresh device: {message}")
        self.error_label.show()

    def _on_delete_clicked(self) -> None:
        if not self.current_device:
            return
        confirm = QMessageBox.question(
            self,
            "Delete Device",
            f"Remove '{self.current_device.device_name}'? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        device_id = self.current_device.id
        self.delete_button.setEnabled(False)
        run_async(
            endpoints.delete_device,
            self.app_state.rest_client,
            device_id,
            on_result=lambda _r: self._on_delete_succeeded(),
            on_error=lambda error, _tb: self._on_delete_failed(error),
        )

    def _on_delete_succeeded(self) -> None:
        self.delete_button.setEnabled(True)
        self.device_deleted.emit()

    def _on_delete_failed(self, error: Exception) -> None:
        self.delete_button.setEnabled(True)
        message = error.message if isinstance(error, ApiError) else str(error)
        QMessageBox.critical(self, "Delete Failed", message)
