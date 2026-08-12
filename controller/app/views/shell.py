"""Post-login shell: sidebar + top nav + a page stack. Pages register
themselves here as they're built (Phase 6 adds Dashboard; Phase 7+ add the
rest). This replaces MainWindow's old placeholder "signed in" page.
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from app.services.app_state import AppState
from app.views.activity_logs_view import ActivityLogsView
from app.views.command_center_view import CommandCenterView
from app.views.dashboard_view import DashboardView
from app.views.device_details_view import DeviceDetailsView
from app.views.devices_view import DevicesView
from app.views.file_manager_view import FileManagerView
from app.views.notifications_view import NotificationsView
from app.views.profile_view import ProfileView
from app.views.settings_view import SettingsView
from app.widgets.sidebar import Sidebar
from app.widgets.top_nav import TopNav

# (key, label) - order defines sidebar order.
_NAV_ITEMS = [
    ("dashboard", "Dashboard"),
    ("devices", "Devices"),
    ("files", "File Manager"),
    ("commands", "Command Center"),
    ("activity", "Activity Logs"),
    ("notifications", "Notifications"),
    ("settings", "Settings"),
    ("profile", "Profile"),
]


class Shell(QWidget):
    def __init__(self, app_state: AppState, parent: QWidget | None = None):
        super().__init__(parent)
        self.app_state = app_state

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar()
        root_layout.addWidget(self.sidebar)

        right_column = QVBoxLayout()
        right_column.setContentsMargins(0, 0, 0, 0)
        right_column.setSpacing(0)

        self.top_nav = TopNav()
        self.top_nav.logout_requested.connect(self.app_state.logout)
        right_column.addWidget(self.top_nav)

        self.page_stack = QStackedWidget()
        right_column.addWidget(self.page_stack)

        right_container = QWidget()
        right_container.setLayout(right_column)
        root_layout.addWidget(right_container)

        self._pages: dict[str, QWidget] = {}
        self._current_key: str | None = None
        self._register_pages()

        self.sidebar.item_selected.connect(self._on_nav_selected)
        self.app_state.socket_connected.connect(lambda: self.top_nav.set_connection_status(True))
        self.app_state.socket_disconnected.connect(lambda: self.top_nav.set_connection_status(False))

        # Show the first page's UI immediately, but do NOT start its
        # polling yet - the Shell is constructed once at app startup,
        # before any login has necessarily happened. Polling only starts
        # once `activate()` is called (by MainWindow, once a session is
        # actually ready) - otherwise the very first API calls fire with
        # no access token yet and 401.
        if _NAV_ITEMS:
            first_key = _NAV_ITEMS[0][0]
            self.page_stack.setCurrentWidget(self._pages[first_key])
            self.top_nav.set_title(_NAV_ITEMS[0][1])
            self.sidebar.set_active(first_key)

    def _register_pages(self) -> None:
        dashboard = DashboardView(self.app_state)
        self._add_page("dashboard", "Dashboard", dashboard)

        devices = DevicesView(self.app_state)
        devices.device_selected.connect(self._show_device_details)
        self._add_page("devices", "Devices", devices)

        file_manager = FileManagerView(self.app_state)
        self._add_page("files", "File Manager", file_manager)

        command_center = CommandCenterView(self.app_state)
        self._add_page("commands", "Command Center", command_center)

        activity_logs = ActivityLogsView(self.app_state)
        self._add_page("activity", "Activity Logs", activity_logs)

        notifications = NotificationsView(self.app_state)
        self._add_page("notifications", "Notifications", notifications)

        settings = SettingsView(self.app_state)
        self._add_page("settings", "Settings", settings)

        profile = ProfileView(self.app_state)
        self._add_page("profile", "Profile", profile)

        # Device Details is reachable only by clicking a device tile, not
        # via the sidebar - registered as a page (so start/stop lifecycle
        # works the same way) but deliberately not added to the sidebar.
        self._device_details_page = DeviceDetailsView(self.app_state)
        self._device_details_page.back_requested.connect(self._show_devices_list)
        self._device_details_page.device_deleted.connect(self._show_devices_list)
        self.page_stack.addWidget(self._device_details_page)
        self._pages["device_details"] = self._device_details_page

    def _show_device_details(self, device_id: str) -> None:
        current_page = self._pages.get(self._current_key) if self._current_key else None
        if current_page and hasattr(current_page, "stop"):
            current_page.stop()

        self._device_details_page.set_device(device_id)
        self._current_key = "device_details"
        self.page_stack.setCurrentWidget(self._device_details_page)
        self.top_nav.set_title("Device Details")
        self._device_details_page.start()

    def _show_devices_list(self) -> None:
        self._activate_page("devices")

    def _add_page(self, key: str, label: str, page: QWidget) -> None:
        self._pages[key] = page
        self.page_stack.addWidget(page)
        self.sidebar.add_item(key, label)

    def activate(self) -> None:
        """Call once the session is actually ready (Shell becomes visible)
        - starts polling for whichever page is currently selected. Safe to
        call repeatedly; only does something the first time after
        construction or after `stop_all()` was called (e.g. a prior logout).
        """

        if self._current_key is None and _NAV_ITEMS:
            self._activate_page(_NAV_ITEMS[0][0])

    def _on_nav_selected(self, key: str) -> None:
        if key == self._current_key:
            return
        self._activate_page(key)

    def _activate_page(self, key: str) -> None:
        page = self._pages.get(key)
        if not page:
            return

        if self._current_key and self._current_key != key:
            previous_page = self._pages.get(self._current_key)
            if previous_page and hasattr(previous_page, "stop"):
                previous_page.stop()

        self._current_key = key
        self.page_stack.setCurrentWidget(page)
        self.top_nav.set_title(dict(_NAV_ITEMS).get(key, key.title()))
        self.sidebar.set_active(key)
        if hasattr(page, "start"):
            page.start()

    def stop_all(self) -> None:
        for page in self._pages.values():
            if hasattr(page, "stop"):
                page.stop()
        self._current_key = None
