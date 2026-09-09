"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal, Slot

from moretzslmcontrol.userinterface.display_session import DisplaySession
from moretzslmcontrol.monitor_stuff.models import ScreenRecord, SessionDebugView, SessionState

logger = logging.getLogger(__name__)


if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from PySide6.QtGui import QScreen
    from PySide6.QtWidgets import QApplication
    from moretzslmcontrol.monitor_stuff.platform.base import PlatformAdapter
    from moretzslmcontrol.hologram_manager import HologramManager


class MonitorManager(QObject):
    recordsChanged = Signal()
    consoleChanged = Signal(str)

    def __init__(self, app: QApplication, platform_adapter: PlatformAdapter) -> None:
        super().__init__()
        self._app = app
        self._platform_adapter = platform_adapter
        self._records_by_id: dict[str, ScreenRecord] = {}
        self._sessions_by_id: dict[str, DisplaySession] = {}
        self._known_screens: dict[str, QScreen] = {}
        self._console_entries_by_id: dict[str, deque[tuple[str, str, str]]] = {}

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

        for screen_uid, record in self._records_by_id.items():
            if screen_uid not in current_ids:
                record.is_connected = False
                self._known_screens.pop(screen_uid, None)
                session = self._sessions_by_id.get(screen_uid)
                if session is not None:
                    session.detach_screen()

        self.recordsChanged.emit()

    def activate_monitor(self, screen_uid: str) -> DisplaySession | None:
        record = self._records_by_id.get(screen_uid)
        if record is None:
            return None
        session = self._sessions_by_id.get(screen_uid)
        if session is None:
            session = self._create_session(record)
        session.enable()
        self.recordsChanged.emit()
        return session

    def deactivate_monitor(self, screen_uid: str) -> None:
        session = self._sessions_by_id.get(screen_uid)
        if session is None:
            return
        session.disable()
        self.recordsChanged.emit()

    def get_session(self, screen_uid: str) -> DisplaySession | None:
        return self._sessions_by_id.get(screen_uid)

    def get_screen_record(self, screen_uid: str) -> ScreenRecord | None:
        """Return the persistent record for a known screen."""
        return self._records_by_id.get(screen_uid)

    def get_displayer(self, screen_uid: str) -> HologramManager | None:
        session = self.get_session(screen_uid)
        if session is None:
            return None
        return session.displayer

    def ensure_displayer(self, screen_uid: str) -> HologramManager | None:
        """Return a display manager, creating an inactive session when required."""
        record = self._records_by_id.get(screen_uid)
        if record is None:
            return None
        session = self._sessions_by_id.get(screen_uid)
        if session is None:
            session = self._create_session(record)
        return session.displayer

    def _create_session(self, record: ScreenRecord) -> DisplaySession:
        session = DisplaySession(record, self._platform_adapter)
        session.bridge.statsChanged.connect(self._on_session_stats_changed)
        session.bridge.consoleMessage.connect(self._on_session_console_message)
        session.bridge.slmWindowToggleRequested.connect(self._on_slm_window_toggle_requested)
        self._sessions_by_id[record.screen_uid] = session
        screen = self._known_screens.get(record.screen_uid)
        if record.is_connected and screen is not None:
            session.attach_screen(screen)
        self.write_to_console(record.screen_uid, "Session initialized.")
        self.write_to_console(
            record.screen_uid,
            f"HERO initialized and discoverable as '{session.heros_name}'.",
        )
        return session

    def shutdown(self) -> None:
        """Release all display sessions and their external control resources."""
        for session in self._sessions_by_id.values():
            session.close()
        self._sessions_by_id.clear()

    def write_to_console(self, screen_uid: str, message: str, level: str = "info") -> None:
        """Store a screen-scoped console entry and mirror it to the application logger."""
        log_method = {
            "info": logger.info,
            "warning": logger.warning,
            "error": logger.error,
        }.get(level)
        if log_method is None:
            raise ValueError(f"Unsupported console level: {level}")
        record = self._records_by_id.get(screen_uid)
        display_name = record.display_name if record is not None else screen_uid
        log_method("[%s] %s", display_name, message)
        entries = self._console_entries_by_id.setdefault(screen_uid, deque(maxlen=500))
        timestamp = datetime.now().astimezone().strftime("%H:%M:%S")
        entries.append((timestamp, level, message))
        self.consoleChanged.emit(screen_uid)

    def get_console_entries(self, screen_uid: str) -> tuple[tuple[str, str, str], ...]:
        """Return the retained console entries for one screen in chronological order."""
        return tuple(self._console_entries_by_id.get(screen_uid, ()))

    @Slot(str)
    def _on_session_stats_changed(self, _session_id: str) -> None:
        self.recordsChanged.emit()

    @Slot(str, str, str)
    def _on_session_console_message(self, session_id: str, level: str, message: str) -> None:
        record = self._records_by_id.get(session_id)
        if record is not None and level == "error":
            record.last_error = message
        self.write_to_console(session_id, message, level)

    @Slot(str)
    def _on_slm_window_toggle_requested(self, session_id: str) -> None:
        session = self._sessions_by_id.get(session_id)
        if session is None:
            return
        if session.state in (SessionState.ACTIVE_CONNECTED, SessionState.ACTIVE_DISCONNECTED):
            session.disable()
            self.write_to_console(session_id, "SLM window disabled via HERO.")
        else:
            session.enable()
            self.write_to_console(session_id, "SLM window enabled via HERO.")

    def iter_debug_views(self) -> list[SessionDebugView]:
        views: list[SessionDebugView] = []
        for screen_uid in sorted(self._records_by_id):
            session = self._sessions_by_id.get(screen_uid)
            record = self._records_by_id[screen_uid]
            if session is None:
                views.append(
                    SessionDebugView(
                        session_id=record.screen_uid,
                        heros_name="",
                        state=SessionState.INACTIVE_CONNECTED if record.is_connected else SessionState.INACTIVE_DISCONNECTED,
                        ready_for_frames=False,
                        has_screen_attached=False,
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
        screen_uid = descriptor.screen_uid
        record = self._records_by_id.get(screen_uid)
        if record is not None:
            record.is_connected = False
        self._known_screens.pop(screen_uid, None)
        session = self._sessions_by_id.get(screen_uid)
        if session is not None:
            session.detach_screen()
        self.recordsChanged.emit()
logger = logging.getLogger(__name__)
