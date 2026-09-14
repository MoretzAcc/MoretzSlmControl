"""
Author: Moritz van Eimern
Date: 18.07.2026
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtGui import QScreen

from moretzslmcontrol.monitor_stuff.platform.windows_edid.active_windows_targets import (
    request_active_windows_targets,
)
from moretzslmcontrol.monitor_stuff.platform.windows_edid.name_normalization import (
    instance_name_matches_device_path,
)
from moretzslmcontrol.monitor_stuff.platform.windows_edid.request_all import (
    request_windows_edids,
    WindowsMonitor,
)
from moretzslmcontrol.monitor_stuff.platform.windows_edid.windows_hmonitor import get_hmonitor
from moretzslmcontrol.monitor_stuff.platform.windows_edid.windows_hmonitor_info import (
    get_monitor_info,
)

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)


def windows_match_edids(screen: QScreen) -> list[WindowsMonitor]:
    win_monitors = request_windows_edids()  # All Edids
    targets = request_active_windows_targets()  #
    hmonitor = get_hmonitor(screen)  # Get Monitor handle by applying a POINT to the screen

    monitor_info = get_monitor_info(hmonitor)

    screen_targets = [
        target
        for target in targets
        if target.gdi_device_name.casefold() == monitor_info.szDevice.casefold()
    ]

    global_matches: list[WindowsMonitor] = []

    for target in screen_targets:
        edid_matches = [
            monitor
            for monitor in win_monitors
            if instance_name_matches_device_path(
                monitor.instance_name,
                target.monitor_device_path,
            )
        ]

        if not edid_matches:
            logger.warning(
                "%s: No matching EDID entry for GDI device %s",
                screen.name(),
                target.gdi_device_name,
            )
        elif len(edid_matches) > 1:
            logger.warning(
                "%s: Multiple matching EDID entries for GDI device %s",
                screen.name(),
                target.gdi_device_name,
            )

        global_matches.extend(edid_matches)

    return global_matches
