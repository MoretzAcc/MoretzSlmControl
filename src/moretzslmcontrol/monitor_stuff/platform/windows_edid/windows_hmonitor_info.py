"""
Author: Moritz van Eimern
Date: 18.07.2026
"""

from __future__ import annotations

import ctypes
import logging
from ctypes import wintypes
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)


user32 = ctypes.WinDLL("user32", use_last_error=True)


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * 32),
    ]


user32.GetMonitorInfoW.argtypes = [
    wintypes.HMONITOR,
    ctypes.POINTER(MONITORINFOEXW),
]
user32.GetMonitorInfoW.restype = wintypes.BOOL


def get_monitor_info(hmonitor: int) -> MONITORINFOEXW:
    info = MONITORINFOEXW()
    info.cbSize = ctypes.sizeof(info)

    success = user32.GetMonitorInfoW(
        wintypes.HMONITOR(hmonitor),
        ctypes.byref(info),
    )

    if not success:
        raise ctypes.WinError(ctypes.get_last_error())

    return info