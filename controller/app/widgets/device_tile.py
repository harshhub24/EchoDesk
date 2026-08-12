"""One device's summary card, shown in the Devices page grid/list. Click to
open Device Details.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout

from app.models import Device
from app.theme import status_color
from app.utils.formatting import format_percent, format_relative_time
from app.widgets.card import GlassCard


class DeviceTile(GlassCard):
    clicked = Signal(str)  # device.id

    def __init__(self, device: Device, parent=None):
        super().__init__(parent)
        self.device = device
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        header = QVBoxLayout()
        name_row = QGridLayout()

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {status_color(device.status)}; font-size: 14pt;")
        name_row.addWidget(self.status_dot, 0, 0)

        self.name_label = QLabel(device.device_name)
        self.name_label.setProperty("cssClass", "subtitle")
        name_row.addWidget(self.name_label, 0, 1)

        header.addLayout(name_row)

        self.os_label = QLabel(device.operating_system or "Unknown OS")
        self.os_label.setProperty("cssClass", "muted")
        header.addWidget(self.os_label)

        self.hostname_label = QLabel(device.hostname or "—")
        self.hostname_label.setProperty("cssClass", "muted")
        header.addWidget(self.hostname_label)

        self.last_seen_label = QLabel(f"Last seen: {format_relative_time(device.last_seen_at)}")
        self.last_seen_label.setProperty("cssClass", "muted")
        header.addWidget(self.last_seen_label)

        metrics_row = QGridLayout()
        self.cpu_label = QLabel(f"CPU {format_percent(device.telemetry.cpu_percent)}")
        self.ram_label = QLabel(f"RAM {format_percent(device.telemetry.ram_percent)}")
        self.disk_label = QLabel(f"Disk {format_percent(device.telemetry.disk_percent)}")
        self.battery_label = QLabel(
            f"Battery {format_percent(device.telemetry.battery_percent)}" if device.telemetry.battery_percent is not None else "No battery"
        )
        for i, label in enumerate((self.cpu_label, self.ram_label, self.disk_label, self.battery_label)):
            label.setProperty("cssClass", "muted")
            metrics_row.addWidget(label, i // 2, i % 2)

        self.body_layout.addLayout(header)
        self.body_layout.addLayout(metrics_row)

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt override naming
        self.clicked.emit(self.device.id)
        super().mousePressEvent(event)

    def update_device(self, device: Device) -> None:
        self.device = device
        self.status_dot.setStyleSheet(f"color: {status_color(device.status)}; font-size: 14pt;")
        self.name_label.setText(device.device_name)
        self.os_label.setText(device.operating_system or "Unknown OS")
        self.hostname_label.setText(device.hostname or "—")
        self.last_seen_label.setText(f"Last seen: {format_relative_time(device.last_seen_at)}")
        self.cpu_label.setText(f"CPU {format_percent(device.telemetry.cpu_percent)}")
        self.ram_label.setText(f"RAM {format_percent(device.telemetry.ram_percent)}")
        self.disk_label.setText(f"Disk {format_percent(device.telemetry.disk_percent)}")
        self.battery_label.setText(
            f"Battery {format_percent(device.telemetry.battery_percent)}" if device.telemetry.battery_percent is not None else "No battery"
        )
