from __future__ import annotations

import ctypes
import unittest
from unittest.mock import Mock
from moretzslmcontrol.monitor_stuff.platform.windows_peek import _set_peek_attributes


class WindowsPeekTest(unittest.TestCase):
    def test_uses_pointer_sized_hwnd_and_four_byte_boolean(self) -> None:
        calls = []
        def setter(hwnd: ctypes.c_void_p, attribute: int, value: object, size: int) -> int:
            calls.append((hwnd.value, attribute, ctypes.cast(value, ctypes.POINTER(ctypes.c_int32)).contents.value, size))
            return 0
        handle = 0x123456789
        self.assertTrue(_set_peek_attributes(handle, setter))
        self.assertEqual(calls, [(handle, 11, 1, 4), (handle, 12, 1, 4)])

    def test_reports_failed_dwm_attribute(self) -> None:
        self.assertFalse(_set_peek_attributes(1, Mock(side_effect=[0, -1])))
