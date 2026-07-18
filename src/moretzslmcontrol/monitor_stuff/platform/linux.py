"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from PySide6.QtGui import QScreen

from moretzslmcontrol.monitor_stuff.models import ScreenDescriptor
from moretzslmcontrol.monitor_stuff.platform import PlatformAdapter
from pyedid import Edid

from moretzslmcontrol.monitor_stuff.platform.linux_edid.get_all import get_linux_edids, LinuxMonitor

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)


class LinuxPlatformAdapter(PlatformAdapter):
    def __init__(self, qt_backend: str) -> None:
        self.qt_backend = qt_backend
        self.desktop_environment = os.environ.get("XDG_CURRENT_DESKTOP")
        self.session = os.environ.get("XDG_SESSION_TYPE")
        self.linux_monitors: list[LinuxMonitor] = []
        super().__init__()

    def get_screen_edids(self, screen: QScreen) -> list[Edid]:
        name = screen.name()

        monitor = next(
            (x for x in self.linux_monitors if x.connector_name == name),
            None,
        )

        if monitor is None:
            # Try with refreshing the list
            self.refresh_edid_list()

            monitor = next(
                (x for x in self.linux_monitors if x.connector_name == name),
                None,
            )

        if monitor is None:
            logger.error(f"Could not find EDID for connector {name}")
            # TODO more checks ?
            return []

        return [monitor.parsed_edid]

    def refresh_edid_list(self) -> None:
        self.linux_monitors = get_linux_edids()

    def log_all_edids(self) -> None:
        logger.info("Logging all EDIDs in linux_monitors:")
        for monitor in self.linux_monitors:
            logger.info(f"EDID for {monitor.connector_name}:\n{monitor.parsed_edid}\n\n")
