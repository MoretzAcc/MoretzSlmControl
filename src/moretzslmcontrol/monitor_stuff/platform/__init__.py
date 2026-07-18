"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import platform as _platform

from moretzslmcontrol.monitor_stuff.platform.base import PlatformAdapter

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    ...
logger = logging.getLogger(__name__)

def create_platform_adapter(qt_backend: str) -> PlatformAdapter:
    system_name = _platform.system().lower()
    logger.info(f"Detected Platform: {system_name}")
    if system_name == "windows":
        from moretzslmcontrol.monitor_stuff.platform.windows import WindowsPlatformAdapter
        return WindowsPlatformAdapter()
    elif system_name == "linux":
        from moretzslmcontrol.monitor_stuff.platform.linux import LinuxPlatformAdapter
        return LinuxPlatformAdapter(qt_backend)
    raise Exception(f"Unsupported platform: {system_name}")
