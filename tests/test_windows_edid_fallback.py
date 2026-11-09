from __future__ import annotations

import sys
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QRect, QSizeF


@unittest.skipUnless(sys.platform == "win32", "Requires the Windows platform adapter")
class WindowsEdidFallbackTest(unittest.TestCase):
    def test_unsupported_wmi_monitor_query_keeps_screen_available(self) -> None:
        from pywintypes import com_error
        from moretzslmcontrol.monitor_stuff.platform.windows import WindowsPlatformAdapter

        adapter = WindowsPlatformAdapter()
        screen = Mock()
        screen.name.return_value = "DISPLAY1"
        screen.devicePixelRatio.return_value = 1
        screen.geometry.return_value = QRect(0, 0, 1920, 1080)
        screen.physicalSize.return_value = QSizeF(500, 300)
        screen.serialNumber.return_value = ""
        screen.manufacturer.return_value = ""
        screen.model.return_value = ""
        screen.refreshRate.return_value = 60
        error = com_error(-2147217396, "OLE error 0x8004100c", None, None)
        with (
            patch("moretzslmcontrol.monitor_stuff.platform.windows.windows_match_edids", side_effect=error),
            patch.object(adapter, "get_host_id", return_value="test-host"),
            self.assertLogs("moretzslmcontrol.monitor_stuff.platform.windows", level="WARNING"),
        ):
            descriptor = adapter.describe_screen(screen)

        self.assertEqual(descriptor.screen_name, "DISPLAY1")
        self.assertEqual((descriptor.width, descriptor.height), (1920, 1080))
        self.assertEqual(descriptor.associated_monitors, [])
        self.assertTrue(descriptor.screen_uid)
