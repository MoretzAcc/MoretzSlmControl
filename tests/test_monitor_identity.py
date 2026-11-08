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

    def test_showing_output_never_requests_keyboard_focus(self) -> None:
        adapter = LinuxPlatformAdapter('xcb')
        window = Mock()
        screen = Mock()
        screen.geometry.return_value = QRect(1920, 0, 1080, 1920)
        adapter.configure_display_window(window)
        adapter.attach_window_to_screen(window, screen)
        adapter.keep_window_in_focus(window)
        window.activateWindow.assert_not_called()
        window.showFullScreen.assert_called_once()
        window.setGeometry.assert_called_once_with(QRect(1920, 0, 1080, 1920))

    def test_unplug_keeps_previously_observed_identity_when_edid_disappears(self) -> None:
        from moretzslmcontrol.monitor_stuff.monitor_manager import MonitorManager
        app = Mock()
        app.screens.return_value = []
        adapter = Mock()
        adapter.describe_screen.side_effect = AssertionError('EDID unavailable during removal')
        manager = MonitorManager(app, adapter)
        screen = Mock()
        record, session = Mock(), Mock()
        manager._known_screens['existing-edid-id'] = screen
        manager._records_by_id['existing-edid-id'] = record
        manager._sessions_by_id['existing-edid-id'] = session
        manager._on_screen_removed(screen)
        self.assertFalse(record.is_connected)
        session.detach_screen.assert_called_once()
        self.assertNotIn('existing-edid-id', manager._known_screens)
        adapter.describe_screen.assert_not_called()
