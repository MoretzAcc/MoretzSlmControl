"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from moretzslmcontrol.monitor_stuff.platform import PlatformAdapter
from pyedid import Edid

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    ...

class LinuxPlatformAdapter(PlatformAdapter):

    @staticmethod
    def get_screen_edids() -> list[Edid]:
        # TODO
        pass