"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from moretzslmcontrol.hologram_manager import HologramManager
from moretzslmcontrol.userinterface.display_bridge import DisplayBridge
from moretzslmcontrol.userinterface.display_window import DisplayWindow
from moretzslmcontrol.monitor_stuff.models import SessionState, SessionDebugView


if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from PySide6.QtGui import QScreen
    from moretzslmcontrol.monitor_stuff.platform.base import PlatformAdapter
    from moretzslmcontrol.monitor_stuff.models import ScreenRecord


class DisplaySession:
    def __init__(self, screen_record: ScreenRecord, platform_adapter: PlatformAdapter) -> None:
        self.screen_record = screen_record
        self.session_id = screen_record.monitor_id
        self.heros_name = f"slm_{screen_record.monitor_id.replace(' ', '_')}"
        self.platform_adapter = platform_adapter
        self.bridge = DisplayBridge(session_id=self.session_id)
        self.displayer = HologramManager(
            H=screen_record.height,
            W=screen_record.width,
            herosName=self.heros_name,
            bridge=self.bridge,
        )
        self.window = DisplayWindow(
            session_id=self.session_id,
            displayer=self.displayer,
            platform_adapter=self.platform_adapter,
        )
        self.bridge.frameAvailable.connect(self.window.on_frame_available)
        self.window.closed.connect(self._on_window_closed)
        self._enabled = False
        self._attached_screen: QScreen | None = None
        self.screen_record.session_id = self.session_id
        self.screen_record.was_ever_activated = True

    @property
    def ready_for_frames(self) -> bool:
        return True

    @property
    def has_screen_attached(self) -> bool:
        return self._attached_screen is not None

    @property
    def state(self) -> SessionState:
        if self._enabled and self.screen_record.is_connected:
            return SessionState.ACTIVE_CONNECTED
        if self._enabled and not self.screen_record.is_connected:
            return SessionState.ACTIVE_DISCONNECTED
        if not self._enabled and self.screen_record.is_connected:
            return SessionState.INACTIVE_CONNECTED
        return SessionState.INACTIVE_DISCONNECTED

    def enable(self) -> None:
        self._enabled = True
        if self.screen_record.is_connected and self._attached_screen is not None:
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
        self.screen_record.is_connected = True
        if self._enabled:
            self.window.attach_to_screen(screen)
        self.bridge.notify_stats_changed()

    def detach_screen(self) -> None:
        self._attached_screen = None
        self.screen_record.is_connected = False
        self.window.detach_from_screen()
        self.bridge.notify_stats_changed()

    def _on_window_closed(self) -> None:
        if not self._enabled:
            return
        self._enabled = False
        self.bridge.notify_stats_changed()

    def close(self) -> None:
        """Close the output window and release this session's external resources."""
        self._enabled = False
        self.window.close()
        self.displayer.close()

    def build_debug_view(self) -> SessionDebugView:
        stats = self.displayer.getStatsSnapshot()
        return SessionDebugView(
            session_id=self.session_id,
            heros_name=self.heros_name,
            state=self.state,
            ready_for_frames=self.ready_for_frames,
            has_screen_attached=self.has_screen_attached,
            monitor_id=self.screen_record.monitor_id,
            screen_uid=self.screen_record.screen_uid,
            display_name=self.screen_record.display_name,
            serial_number=self.screen_record.serial_number,
            screen_name=self.screen_record.screen_name,
            manufacturer=self.screen_record.manufacturer,
            model=self.screen_record.model,
            port_name=self.screen_record.port_name,
            resolution=self.screen_record.resolution_text,
            physical_size=f"{self.screen_record.physical_size_x}mm x {self.screen_record.physical_size_y}mm",
            refresh_rate=f"{self.screen_record.refresh_rate} Hz",
            submitted_count=stats.submitted_count,
            accepted_count=stats.accepted_count,
            invalid_count=stats.invalid_count,
            displayed_count=stats.displayed_count,
            latest_revision=stats.latest_revision,
            last_displayed_revision=stats.last_displayed_revision,
            last_error=self.screen_record.last_error,
        )
