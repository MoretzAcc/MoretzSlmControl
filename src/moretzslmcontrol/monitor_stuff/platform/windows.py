"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QScreen

from moretzslmcontrol.monitor_stuff.platform import PlatformAdapter

from moretzslmcontrol.monitor_stuff.platform.base import MonitorEdid
from moretzslmcontrol.monitor_stuff.platform.windows_edid.windows_edid import windows_match_edids

# imports here

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from PySide6.QtWidgets import QWidget


class WindowsPlatformAdapter(PlatformAdapter):
    def get_screen_edids(self, screen: QScreen) -> list[MonitorEdid]:
        return [
            MonitorEdid(
                os_identifier=win_monitor.instance_name, parsed_edid=win_monitor.parsed_edid
            )
            for win_monitor in windows_match_edids(screen)
        ]

    def detach_window_from_screen(self, window: QWidget) -> None:
        window.showMinimized()
        window.hide()

    def keep_window_in_focus(self, window: QWidget) -> None:
        super().keep_window_in_focus(window)
