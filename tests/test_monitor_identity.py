from __future__ import annotations

import unittest
from unittest.mock import Mock

from PySide6.QtCore import QRect, QSizeF

from moretzslmcontrol.monitor_stuff.platform.linux import LinuxPlatformAdapter


class MonitorIdentityTest(unittest.TestCase):
    def test_missing_edid_keeps_connectors_distinct_and_identity_stable(self) -> None:
        adapter = LinuxPlatformAdapter('xcb')
        adapter.get_screen_edids = Mock(return_value=[])
        adapter.get_host_id = Mock(return_value='test-host')
        screen = Mock()
        screen.devicePixelRatio.return_value = 1
        screen.geometry.return_value = QRect(0, 0, 1920, 1080)
        screen.physicalSize.return_value = QSizeF(500, 300)
        screen.serialNumber.return_value = ''
        screen.manufacturer.return_value = ''
        screen.model.return_value = ''
        screen.refreshRate.return_value = 60
        screen.name.return_value = 'DUMMY0'
        original = adapter.describe_screen(screen).screen_uid
        screen.name.return_value = 'DUMMY1'
        self.assertNotEqual(adapter.describe_screen(screen).screen_uid, original)
        screen.name.return_value = 'DUMMY0'
        screen.geometry.return_value = QRect(1920, 0, 1280, 800)
        screen.devicePixelRatio.return_value = 1.5
        self.assertEqual(adapter.describe_screen(screen).screen_uid, original)
