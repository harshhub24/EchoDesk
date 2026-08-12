"""Devices page. Polling-driven (DeviceListService) - see
docs/PHASE_1_ANALYSIS.md for why there's no realtime push to poll instead of.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models import Device
from app.services.app_state import AppState
from app.services.device_service import DeviceListService
from app.theme import COLORS, SPACING
from app.widgets.device_tile import DeviceTile

_SORT_OPTIONS = [
    ("name", "Name"),
    ("status", "Status"),
    ("last_seen", "Last Seen"),
]


class DevicesView(QWidget):
    device_selected = Signal(str)  # device.id

    def __init__(self, app_state: AppState, parent: QWidget | None = None):
        super().__init__(parent)
        self.app_state = app_state
        self.service = DeviceListService(app_state)
        self._devices: list[Device] = []
        self._tiles: dict[str, DeviceTile] = {}
        self._grid_columns = 3

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        heading = QLabel("Devices")
        heading.setProperty("cssClass", "heading")
        layout.addWidget(heading)

        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or hostname...")
        self.search_input.textChanged.connect(self._apply_filters)

        self.sort_combo = QComboBox()
        for key, label in _SORT_OPTIONS:
            self.sort_combo.addItem(label, key)
        self.sort_combo.currentIndexChanged.connect(self._apply_filters)

        self.grid_button = QPushButton("Grid")
        self.grid_button.setProperty("cssClass", "ghost")
        self.grid_button.clicked.connect(lambda: self._set_columns(3))

        self.list_button = QPushButton("List")
        self.list_button.setProperty("cssClass", "ghost")
        self.list_button.clicked.connect(lambda: self._set_columns(1))

        toolbar.addWidget(self.search_input, stretch=1)
        toolbar.addWidget(self.sort_combo)
        toolbar.addWidget(self.grid_button)
        toolbar.addWidget(self.list_button)
        layout.addLayout(toolbar)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {COLORS.danger};")
        self.error_label.hide()
        layout.addWidget(self.error_label)

        self.empty_label = QLabel("No devices registered yet.")
        self.empty_label.setProperty("cssClass", "muted")
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(SPACING.md)
        scroll_area.setWidget(self._grid_container)
        layout.addWidget(scroll_area, stretch=1)

        self.service.devices_updated.connect(self._on_devices_updated)
        self.service.refresh_failed.connect(self._on_refresh_failed)

    def start(self) -> None:
        self.service.start()

    def stop(self) -> None:
        self.service.stop()

    def _set_columns(self, columns: int) -> None:
        self._grid_columns = columns
        self._relayout_tiles()

    def _on_devices_updated(self, devices: list[Device]) -> None:
        self.error_label.hide()
        self._devices = devices
        self._sync_tiles()
        self._apply_filters()

    def _on_refresh_failed(self, message: str) -> None:
        self.error_label.setText(f"Could not refresh devices: {message}")
        self.error_label.show()

    def _sync_tiles(self) -> None:
        current_ids = {d.id for d in self._devices}

        for device_id in list(self._tiles.keys()):
            if device_id not in current_ids:
                tile = self._tiles.pop(device_id)
                tile.setParent(None)
                tile.deleteLater()

        for device in self._devices:
            if device.id in self._tiles:
                self._tiles[device.id].update_device(device)
            else:
                tile = DeviceTile(device)
                tile.clicked.connect(self.device_selected)
                self._tiles[device.id] = tile

    def _apply_filters(self) -> None:
        query = self.search_input.text().strip().lower()
        sort_key = self.sort_combo.currentData()

        filtered = [
            d for d in self._devices
            if not query or query in d.device_name.lower() or query in (d.hostname or "").lower()
        ]

        if sort_key == "name":
            filtered.sort(key=lambda d: d.device_name.lower())
        elif sort_key == "status":
            filtered.sort(key=lambda d: (d.status != "online", d.device_name.lower()))
        elif sort_key == "last_seen":
            filtered.sort(key=lambda d: d.last_seen_at or "", reverse=True)

        self.empty_label.setVisible(len(self._devices) == 0)
        self._render_tiles([self._tiles[d.id] for d in filtered if d.id in self._tiles])

    def _render_tiles(self, ordered_tiles: list[DeviceTile]) -> None:
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(self._grid_container)
                widget.hide()

        for index, tile in enumerate(ordered_tiles):
            row, col = divmod(index, self._grid_columns)
            self._grid_layout.addWidget(tile, row, col)
            tile.show()

    def _relayout_tiles(self) -> None:
        self._apply_filters()
