"""Keep optical output opaque during Windows taskbar/desktop Peek.

API: https://learn.microsoft.com/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute
"""
from __future__ import annotations

import ctypes
from collections.abc import Callable
import sys


def _set_peek_attributes(hwnd: int, setter: Callable[..., int]) -> bool:
    enabled = ctypes.c_int32(1)  # Win32 BOOL is always four bytes.
    results = [setter(ctypes.c_void_p(hwnd), attribute, ctypes.byref(enabled), ctypes.sizeof(enabled))
               for attribute in (11, 12)]  # DISALLOW_PEEK, EXCLUDED_FROM_PEEK
    return all(result == 0 for result in results)


def exclude_from_peek(hwnd: int) -> bool:
    if sys.platform != "win32":
        return False
    try:
        setter = ctypes.WinDLL("dwmapi").DwmSetWindowAttribute
        setter.argtypes = (ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32)
        setter.restype = ctypes.c_int32
        return _set_peek_attributes(hwnd, setter)
    except (OSError, AttributeError):
        return False
