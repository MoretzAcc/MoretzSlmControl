"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from moretzslmcontrol.control.slm_connector import SlmConnector
from moretzslmcontrol.userinterface.display_bridge import DisplayBridge
from moretzslmcontrol.userinterface.display_window import DisplayWindow
from moretzslmcontrol.userinterface.models import SessionState, SessionDebugView


if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from PySide6.QtGui import QScreen
    from moretzslmcontrol.userinterface.platform.base import PlatformAdapter
    from moretzslmcontrol.userinterface.models import MonitorRecord


class DisplaySession:
    def __init__(self, monitor_record: MonitorRecord, platform_adapter: PlatformAdapter) -> None:
        self.monitor_record = monitor_record
        self.session_id = monitor_record.monitor_id
        self.heros_name = f"slmHero_{monitor_record.monitor_id.replace(' ', '_')}"
        self.platform_adapter = platform_adapter
        self.bridge = DisplayBridge(session_id=self.session_id)
        self.displayer = SlmConnector(
            H=monitor_record.height,
            W=monitor_record.width,
            herosName=self.heros_name,
            bridge=self.bridge,
        )
        self.window = DisplayWindow(
            session_id=self.session_id,
            displayer=self.displayer,
            platform_adapter=self.platform_adapter,
        )
        self.bridge.frameAvailable.connect(self.window.on_frame_available)
        self._enabled = False
        self._attached_screen: QScreen | None = None
        self.monitor_record.session_id = self.session_id
        self.monitor_record.was_ever_activated = True

    @property
    def ready_for_frames(self) -> bool:
        return True

    @property
    def has_screen_attached(self) -> bool:
        return self._attached_screen is not None

    @property
    def state(self) -> SessionState:
        if self._enabled and self.monitor_record.is_connected:
            return SessionState.ACTIVE_CONNECTED
        if self._enabled and not self.monitor_record.is_connected:
            return SessionState.ACTIVE_DISCONNECTED
        if not self._enabled and self.monitor_record.is_connected:
            return SessionState.INACTIVE_CONNECTED
        return SessionState.INACTIVE_DISCONNECTED

    def enable(self) -> None:
        self._enabled = True
        if self.monitor_record.is_connected and self._attached_screen is not None:
            self.window.attach_to_screen(self._attached_screen)
        else:
            self.window.detach_from_screen()
        self.bridge.notify_stats_changed()

    def disable(self) -> None:
        self._enabled = False
        self.window.detach_from_screen()
        self.bridge.notify_stats_changed()

    def attach_screen(self, screen: QScreen) -> None:
        self._attached_screen = screen
        self.monitor_record.is_connected = True
        if self._enabled:
            self.window.attach_to_screen(screen)
        self.bridge.notify_stats_changed()

    def detach_screen(self) -> None:
        self._attached_screen = None
        self.monitor_record.is_connected = False
        self.window.detach_from_screen()
        self.bridge.notify_stats_changed()

    def build_debug_view(self) -> SessionDebugView:
        stats = self.displayer.getStatsSnapshot()
        return SessionDebugView(
            session_id=self.session_id,
            heros_name=self.heros_name,
            state=self.state,
            ready_for_frames=self.ready_for_frames,
            has_screen_attached=self.has_screen_attached,
            monitor_id=self.monitor_record.monitor_id,
            serial_number=self.monitor_record.serial_number,
            screen_name=self.monitor_record.screen_name,
            manufacturer=self.monitor_record.manufacturer,
            model=self.monitor_record.model,
            port_name=self.monitor_record.port_name,
            resolution=self.monitor_record.resolution_text,
            physical_size=f"{self.monitor_record.physical_size_x}mm x {self.monitor_record.physical_size_y}mm",
            refresh_rate=f"{self.monitor_record.refresh_rate} Hz",
            submitted_count=stats.submitted_count,
            accepted_count=stats.accepted_count,
            invalid_count=stats.invalid_count,
            displayed_count=stats.displayed_count,
            latest_revision=stats.latest_revision,
            last_displayed_revision=stats.last_displayed_revision,
            last_error=self.monitor_record.last_error,
        )
