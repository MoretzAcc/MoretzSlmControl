"""Reproductions of open PR #3 findings; failures remain until reviewed and fixed."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRect, QSizeF
from PySide6.QtWidgets import QApplication

from moretzslmcontrol.monitor_stuff.monitor_manager import MonitorManager
from moretzslmcontrol.monitor_stuff.platform.base import MonitorEdid, PlatformAdapter
from moretzslmcontrol.userinterface.main_window import MainWindow
from moretzslmcontrol.util.ui_settings import UiSettings, load_ui_settings, save_ui_settings


class Pr3ReviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_temporary_edid_failure_keeps_the_current_output_attached(self) -> None:
        # Simulate the new Windows COM fallback by returning no EDIDs. The
        # shared descriptor and session logic are identical on either platform.
        adapter = Mock(spec=PlatformAdapter)
        adapter.describe_screen.side_effect = lambda screen: PlatformAdapter.describe_screen(adapter, screen)
        adapter.get_host_id = Mock(return_value="review-host")
        edid = Mock(manufacturer_pnp_id="ACM", name="Panel", product_id=1, year=2024, week=1, serial="123")
        adapter.get_screen_edids = Mock(return_value=[MonitorEdid("DISPLAY1", edid)])
        screen = Mock()
        screen.name.return_value = "DISPLAY1"
        screen.devicePixelRatio.return_value = 1
        screen.geometry.return_value = QRect(0, 0, 1920, 1080)
        screen.physicalSize.return_value = QSizeF(500, 300)
        screen.refreshRate.return_value = 60
        for name in ("serialNumber", "manufacturer", "model"):
            getattr(screen, name).return_value = ""
        app = Mock()
        app.screens.return_value = [screen]
        manager = MonitorManager(app, adapter)
        uid = next(iter(manager._records_by_id))
        session = Mock()
        session.displayer.shape = (1080, 1920)
        manager._sessions_by_id[uid] = session
        adapter.get_screen_edids.return_value = []
        manager.rescan_screens()
        self.assertTrue(manager.get_screen_record(uid).is_connected, "Transient EDID failure disconnects the original session")
        session.detach_screen.assert_not_called()

    def test_large_fonts_keep_scaling_buttons_readable(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            manager = Mock()
            manager.iter_debug_views.return_value = []
            window = MainWindow(manager, settings_path=Path(folder) / "settings.json")
            try:
                window.show()
                window._set_ui_settings(UiSettings(font_scale=2, element_scale=0.5))
                self.app.processEvents()
                for button in (window._scale_up_button, window._scale_down_button, window._scale_settings_button):
                    self.assertGreaterEqual(button.height(), button.fontMetrics().height(), "Scaling controls clip their own text")
            finally:
                window.close()
                window._pattern_executor.shutdown(wait=True)
                self.app.processEvents()

    def test_existing_scheduling_test_does_not_depend_on_or_modify_user_preferences(self) -> None:
        # Keep this reproduction away from the real profile even though the
        # existing test creates MainWindow without an isolated settings_path.
        from test_calculation_scheduling import CalculationSchedulingTest

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            original = UiSettings(global_scale=3)
            save_ui_settings(path, original)
            with patch("moretzslmcontrol.userinterface.main_window.ui_settings_path", return_value=path):
                case = CalculationSchedulingTest("test_ui_scale_round_trip_preserves_font_size")
                case.setUpClass()
                result = unittest.TestResult()
                case.run(result)
            self.assertEqual(load_ui_settings(path), original, "An existing test overwrites saved UI preferences")
            self.assertTrue(result.wasSuccessful(), result.failures + result.errors)
