"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pyedid

from moretzslmcontrol.monitor_stuff.models import ScreenDescriptor
from moretzslmcontrol.monitor_stuff.platform import PlatformAdapter
from moretzslmcontrol.monitor_stuff.platform.windows_edid import request_windows_edids
from pyedid import Edid

# imports here

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from PySide6.QtWidgets import QWidget


class WindowsPlatformAdapter(PlatformAdapter):

    def __init__(self) -> None:
        super().__init__()
        self.windows_monitors = request_windows_edids()

    def get_screen_edid(self, descriptor: ScreenDescriptor) -> list[Edid]:
        win_monitors = request_windows_edids()

        

        return [pyedid.parse_edid(win_monitor.edid) for win_monitor in win_monitors]

    def detach_window_from_screen(self, window: QWidget) -> None:
        window.showMinimized()
        window.hide()

    def keep_window_in_focus(self, window: QWidget) -> None:
        super().keep_window_in_focus(window)

    def refresh_edid_list(self) -> None:
        self.windows_monitors = request_windows_edids()