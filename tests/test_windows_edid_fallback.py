from __future__ import annotations

import sys
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QRect, QSizeF

from moretzslmcontrol.monitor_stuff.monitor_manager import MonitorManager


@unittest.skipUnless(sys.platform == "win32", "Requires the Windows platform adapter")
class WindowsEdidFallbackTest(unittest.TestCase):
    def setUp(self) -> None:
        from pywintypes import com_error
        from moretzslmcontrol.monitor_stuff.platform.windows import WindowsPlatformAdapter

        self.adapter = WindowsPlatformAdapter()
        self.screen = Mock()
        self.screen.name.return_value = "DISPLAY1"
        self.screen.devicePixelRatio.return_value = 1
        self.screen.geometry.return_value = QRect(0, 0, 1920, 1080)
        self.screen.physicalSize.return_value = QSizeF(500, 300)
        self.screen.serialNumber.return_value = ""
        self.screen.manufacturer.return_value = ""
        self.screen.model.return_value = ""
        self.screen.refreshRate.return_value = 60
        self.error = com_error(-2147217396, "OLE error 0x8004100c", None, None)
        host = patch.object(self.adapter, "get_host_id", return_value="test-host")
        host.start()
        self.addCleanup(host.stop)

    @staticmethod
    def monitor(connector: str, serial: str) -> Mock:
        edid = bytearray(128)
        edid[:8] = b"\x00\xff\xff\xff\xff\xff\xff\x00"
        edid[18:21] = bytes((1, 4, 0xA0))  # EDID 1.4, digital, 8 bits/channel.
        edid[127] = (-sum(edid)) % 256
        return Mock(
            instance_name=connector, edid=bytes(edid),
            parsed_edid=Mock(manufacturer_pnp_id="ACM", name="Panel", product_id=1, year=2024, week=1, serial=serial),
        )

    def test_unsupported_wmi_monitor_query_keeps_screen_available(self) -> None:
        with (
            patch("moretzslmcontrol.monitor_stuff.platform.windows.windows_match_edids", side_effect=self.error),
            self.assertLogs("moretzslmcontrol.monitor_stuff.platform.windows", level="WARNING"),
        ):
            descriptor = self.adapter.describe_screen(self.screen)
        self.assertEqual(descriptor.screen_name, "DISPLAY1")
        self.assertEqual((descriptor.width, descriptor.height), (1920, 1080))
        self.assertEqual(descriptor.associated_monitors, [])
        self.assertTrue(descriptor.screen_uid)

    def test_successful_edid_queries_refresh_metadata_and_keep_geometry_out_of_identity(self) -> None:
        first = self.monitor("connector-1", "first-panel")
        replacement = self.monitor("connector-1", "replacement-panel")
        with patch("moretzslmcontrol.monitor_stuff.platform.windows.windows_match_edids", side_effect=[[first], [first], [replacement]]) as query:
            original = self.adapter.describe_screen(self.screen)
            self.screen.geometry.return_value = QRect(0, 0, 3840, 2160)
            resized = self.adapter.describe_screen(self.screen)
            replaced = self.adapter.describe_screen(self.screen)
        self.assertEqual(query.call_count, 3)
        self.assertEqual(original.screen_uid, resized.screen_uid)
        self.assertEqual((resized.width, resized.height), (3840, 2160))
        self.assertEqual(resized.associated_monitors[0].bits_per_channel, 8)
        self.assertNotEqual(original.screen_uid, replaced.screen_uid)
        self.assertIs(replaced.associated_monitors[0].parsed_edid, replacement.parsed_edid)

    def test_failed_query_reuses_edid_without_detaching_session_and_recovers(self) -> None:
        monitor = self.monitor("connector-1", "first-panel")
        app = Mock()
        app.screens.return_value = [self.screen]
        with patch("moretzslmcontrol.monitor_stuff.platform.windows.windows_match_edids", side_effect=[[monitor], self.error, [monitor]]):
            manager = MonitorManager(app, self.adapter)
            uid = next(iter(manager._records_by_id))
            session = Mock()
            session.displayer.shape = (1080, 1920)
            manager._sessions_by_id[uid] = session
            with self.assertLogs("moretzslmcontrol.monitor_stuff.platform.windows", level="WARNING"):
                manager.rescan_screens()
            self.assertTrue(manager.get_screen_record(uid).is_connected)
            self.assertEqual(len(manager._records_by_id), 1)
            session.detach_screen.assert_not_called()
            manager.rescan_screens()
        self.assertTrue(manager.get_screen_record(uid).is_connected)
        session.detach_screen.assert_not_called()
        self.assertEqual(session.attach_screen.call_count, 2)

    def test_new_screen_never_inherits_another_screens_cached_edid(self) -> None:
        monitor = self.monitor("connector-1", "first-panel")
        other_screen = Mock()
        other_screen.name.return_value = "DISPLAY2"
        with patch("moretzslmcontrol.monitor_stuff.platform.windows.windows_match_edids", side_effect=[[monitor], self.error, []]):
            self.assertTrue(self.adapter.get_screen_edids(self.screen))
            with self.assertLogs("moretzslmcontrol.monitor_stuff.platform.windows", level="WARNING"):
                self.assertEqual(self.adapter.get_screen_edids(other_screen), [])
            # A successful empty query is authoritative, not replaced by a cache.
            self.assertEqual(self.adapter.get_screen_edids(self.screen), [])
