"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary

import winreg
from pywintypes import com_error

from PySide6.QtGui import QScreen

from moretzslmcontrol.monitor_stuff.platform import PlatformAdapter

from moretzslmcontrol.monitor_stuff.platform.base import MonitorEdid
from moretzslmcontrol.monitor_stuff.bit_depth import edid_bits_per_channel
from moretzslmcontrol.monitor_stuff.platform.windows_peek import exclude_from_peek
from moretzslmcontrol.monitor_stuff.platform.windows_edid.windows_edid import windows_match_edids


if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)

class WindowsPlatformAdapter(PlatformAdapter):
    def __init__(self) -> None:
        self._last_screen_edids: WeakKeyDictionary[QScreen, list[MonitorEdid]] = WeakKeyDictionary()

    def get_host_id(self) -> str:
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
            ) as key:
                value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return value
        except PermissionError:
            logger.debug("Failed to get host id (PermissionError).")
            return ""
        except OSError as _:
            logger.debug("Failed to get host id (OSError).")
            return ""

    def get_screen_edids(self, screen: QScreen) -> list[MonitorEdid]:
        try:
            monitors = windows_match_edids(screen)
        except com_error as error:
            # Keep an observed screen's identity during a failed WMI query.
            # Successful queries always refresh metadata, including replacements.
            cached = self._last_screen_edids.get(screen, [])
            fallback = "last successful EDID" if cached else "Qt screen metadata"
            logger.warning("%s: Windows monitor EDID is unavailable; using %s: %s", screen.name(), fallback, error)
            return cached
        edids = [
            MonitorEdid(
                os_identifier=monitor.instance_name,
                parsed_edid=monitor.parsed_edid,
                bits_per_channel=edid_bits_per_channel(monitor.edid),
            )
            for monitor in monitors
        ]
        self._last_screen_edids[screen] = edids
        return edids

    def attach_window_to_screen(self, window: QWidget, screen: QScreen) -> None:
        super().attach_window_to_screen(window, screen)
        if not exclude_from_peek(int(window.winId())):
            logger.warning("Windows DWM could not exclude the SLM output from Aero Peek")

    def detach_window_from_screen(self, window: QWidget) -> None:
        window.showMinimized()
        window.hide()

    def keep_window_in_focus(self, window: QWidget) -> None:
        super().keep_window_in_focus(window)
