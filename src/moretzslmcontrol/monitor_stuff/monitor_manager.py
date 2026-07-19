"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

from moretzslmcontrol.userinterface.display_session import DisplaySession
from moretzslmcontrol.monitor_stuff.models import ScreenRecord, SessionDebugView, SessionState


if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from PySide6.QtGui import QScreen
    from PySide6.QtWidgets import QApplication
    from moretzslmcontrol.monitor_stuff.platform.base import PlatformAdapter
    from moretzslmcontrol.hologram_manager import HologramManager


class MonitorManager(QObject):
    recordsChanged = Signal()

    def __init__(self, app: QApplication, platform_adapter: PlatformAdapter) -> None:
        super().__init__()
        self._app = app
        self._platform_adapter = platform_adapter
        self._records_by_id: dict[str, ScreenRecord] = {}
        self._sessions_by_id: dict[str, DisplaySession] = {}
        self._known_screens: dict[str, QScreen] = {}

        self._app.screenAdded.connect(self._on_screen_added)
        self._app.screenRemoved.connect(self._on_screen_removed)
        self.rescan_screens()

    def rescan_screens(self) -> None:
        current_ids: set[str] = set()
        for screen in self._app.screens():
            descriptor = self._platform_adapter.describe_screen(screen)
            current_ids.add(descriptor.screen_uid)
            self._known_screens[descriptor.screen_uid] = screen
            record = self._records_by_id.get(descriptor.screen_uid)
            if record is None:
                record = ScreenRecord(
                    monitor_id=descriptor.screen_uid,
                    screen_uid=descriptor.screen_uid,
                    display_name=descriptor.display_name,
                    serial_number=descriptor.serial_number,
                    screen_name=descriptor.screen_name,
                    manufacturer=descriptor.manufacturer,
                    model=descriptor.model,
                    port_name=descriptor.port_name,
                    width=descriptor.width,
                    height=descriptor.height,
                    geometry_x=descriptor.geometry_x,
                    geometry_y=descriptor.geometry_y,
                    physical_size_x=descriptor.physical_size_x,
                    physical_size_y=descriptor.physical_size_y,
                    refresh_rate=descriptor.refresh_rate,
                    associated_monitors=descriptor.associated_monitors,
                    is_connected=True,
                )
                self._records_by_id[descriptor.screen_uid] = record
            else:
                record.screen_uid = descriptor.screen_uid
                record.display_name = descriptor.display_name
                record.serial_number = descriptor.serial_number
                record.screen_name = descriptor.screen_name
                record.manufacturer = descriptor.manufacturer
                record.model = descriptor.model
                record.port_name = descriptor.port_name
                record.width = descriptor.width
                record.height = descriptor.height
                record.geometry_x = descriptor.geometry_x
                record.geometry_y = descriptor.geometry_y
                record.associated_monitors = descriptor.associated_monitors
                record.is_connected = True

            session = self._sessions_by_id.get(descriptor.screen_uid)
            if session is not None:
                session.attach_screen(screen)

        for monitor_id, record in self._records_by_id.items():
            if monitor_id not in current_ids:
                record.is_connected = False
                self._known_screens.pop(monitor_id, None)
                session = self._sessions_by_id.get(monitor_id)
                if session is not None:
                    session.detach_screen()

        self.recordsChanged.emit()

    def activate_monitor(self, monitor_id: str) -> DisplaySession | None:
        record = self._records_by_id.get(monitor_id)
        if record is None:
            return None
        session = self._sessions_by_id.get(monitor_id)
        if session is None:
            session = DisplaySession(record, self._platform_adapter)
            session.bridge.statsChanged.connect(lambda _session_id: self.recordsChanged.emit())
            self._sessions_by_id[monitor_id] = session
            if record.is_connected:
                screen = self._known_screens.get(monitor_id)
                if screen is not None:
                    session.attach_screen(screen)
        session.enable()
        self.recordsChanged.emit()
        return session

    def deactivate_monitor(self, monitor_id: str) -> None:
        session = self._sessions_by_id.get(monitor_id)
        if session is None:
            return
        session.disable()
        self.recordsChanged.emit()

    def get_session(self, monitor_id: str) -> DisplaySession | None:
        return self._sessions_by_id.get(monitor_id)

    def get_screen_record(self, monitor_id: str) -> ScreenRecord | None:
        """Return the persistent record for a known screen."""
        return self._records_by_id.get(monitor_id)

    def get_displayer(self, monitor_id: str) -> HologramManager | None:
        session = self.get_session(monitor_id)
        if session is None:
            return None
        return session.displayer

    def ensure_displayer(self, monitor_id: str) -> HologramManager | None:
        """Return a display manager, creating an inactive session when required."""
        record = self._records_by_id.get(monitor_id)
        if record is None:
            return None
        session = self._sessions_by_id.get(monitor_id)
        if session is None:
            session = DisplaySession(record, self._platform_adapter)
            session.bridge.statsChanged.connect(lambda _session_id: self.recordsChanged.emit())
            self._sessions_by_id[monitor_id] = session
            screen = self._known_screens.get(monitor_id)
            if record.is_connected and screen is not None:
                session.attach_screen(screen)
        return session.displayer

    def shutdown(self) -> None:
        """Release all display sessions and their external control resources."""
        for session in self._sessions_by_id.values():
            session.close()
        self._sessions_by_id.clear()

    def iter_debug_views(self) -> list[SessionDebugView]:
        views: list[SessionDebugView] = []
        for monitor_id in sorted(self._records_by_id):
            session = self._sessions_by_id.get(monitor_id)
            record = self._records_by_id[monitor_id]
            if session is None:
                views.append(
                    SessionDebugView(
                        session_id=record.monitor_id,
                        heros_name="",
                        state=SessionState.INACTIVE_CONNECTED if record.is_connected else SessionState.INACTIVE_DISCONNECTED,
                        ready_for_frames=False,
                        has_screen_attached=False,
                        monitor_id=record.monitor_id,
                        screen_uid=record.screen_uid,
                        display_name=record.display_name,
                        serial_number=record.serial_number,
                        screen_name=record.screen_name,
                        manufacturer=record.manufacturer,
                        model=record.model,
                        port_name=record.port_name,
                        resolution=record.resolution_text,
                        physical_size=f"{record.physical_size_x}mm x {record.physical_size_y}mm",
                        refresh_rate=f"{record.refresh_rate} Hz",
                        submitted_count=0,
                        accepted_count=0,
                        invalid_count=0,
                        displayed_count=0,
                        latest_revision=0,
                        last_displayed_revision=0,
                        last_error=record.last_error,
                    )
                )
            else:
                views.append(session.build_debug_view())
        return views

    def _on_screen_added(self, screen: QScreen) -> None:
        descriptor = self._platform_adapter.describe_screen(screen)
        self._known_screens[descriptor.screen_uid] = screen
        self.rescan_screens()

    def _on_screen_removed(self, screen: QScreen) -> None:
        descriptor = self._platform_adapter.describe_screen(screen)
        monitor_id = descriptor.screen_uid
        record = self._records_by_id.get(monitor_id)
        if record is not None:
            record.is_connected = False
        self._known_screens.pop(monitor_id, None)
        session = self._sessions_by_id.get(monitor_id)
        if session is not None:
            session.detach_screen()
        self.recordsChanged.emit()
