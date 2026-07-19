"""
Author: Moritz van Eimern
Date: 18.07.2026
"""

from __future__ import annotations

import ctypes
import logging
from ctypes import wintypes
from typing import TYPE_CHECKING

from PySide6.QtGui import QScreen

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)


MONITOR_DEFAULTTONEAREST = 2

user32 = ctypes.WinDLL("user32", use_last_error=True)

class POINT(ctypes.Structure):
    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG),
    ]


user32.MonitorFromPoint.argtypes = [
    POINT,
    wintypes.DWORD,
]
user32.MonitorFromPoint.restype = wintypes.HMONITOR

def get_hmonitor(screen: QScreen) -> int:
    geometry = screen.geometry()

    point = POINT(
        geometry.x() + geometry.width() // 2,
        geometry.y() + geometry.height() // 2,
    )

    hmonitor = user32.MonitorFromPoint(
        point,
        MONITOR_DEFAULTTONEAREST,
    )

    if not hmonitor:
        raise ctypes.WinError(ctypes.get_last_error())

    return int(hmonitor)
