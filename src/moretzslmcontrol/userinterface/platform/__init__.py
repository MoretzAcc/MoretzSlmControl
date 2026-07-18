"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import platform as _platform

from moretzslmcontrol.userinterface.platform.base import PlatformAdapter
from moretzslmcontrol.userinterface.platform.linux import LinuxPlatformAdapter
from moretzslmcontrol.userinterface.platform.windows import WindowsPlatformAdapter

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    ...
logger = logging.getLogger(__name__)

def create_platform_adapter() -> PlatformAdapter:
    system_name = _platform.system().lower()
    logger.info(f"Detected Platform: {system_name}")
    if system_name == "windows":
        return WindowsPlatformAdapter()
    return LinuxPlatformAdapter()
