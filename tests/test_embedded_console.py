from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from moretzslmcontrol.userinterface.main_window import MainWindow
from moretzslmcontrol.util.ui_settings import UiSettings


class EmbeddedConsoleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        manager = Mock()
        manager.iter_debug_views.return_value = []
        self.window = MainWindow(manager, settings_path=Path(self.folder.name) / "settings.json")
        self.window._content_stack.setCurrentWidget(self.window._details_page)
        self.window.resize(1400, 900)
        self.window.show()
        self.drain()
        self.group = self.window._preview_labels["base"].parentWidget()

    def tearDown(self) -> None:
        self.window.close()
        self.window._pattern_executor.shutdown(wait=True)
        self.drain()
        self.folder.cleanup()

    def drain(self) -> None:
        for _ in range(4):
            self.app.processEvents()

    def assert_console_fits(self) -> None:
        console = self.group._console_widget
        self.assertTrue(console.isVisible())
        self.assertTrue(self.group.rect().contains(console.geometry()))
        controls_bottom = max(control.geometry().bottom() for control in self.group._file_controls)
        self.assertGreater(console.y(), controls_bottom)
        self.assertLess(console.geometry().right(), self.group.layout().cellRect(2, 4).left())
        self.assertLess(self.group._notch.y(), console.y())
        self.assertGreater(self.group._notch.x(), console.geometry().right())

    def test_console_fits_only_below_correction_and_hologram(self) -> None:
        self.assert_console_fits()
        self.assertEqual(self.group.layout().indexOf(self.group._console_widget), -1)

    def test_log_contents_and_header_width_do_not_change_pattern_or_window_dimensions(self) -> None:
        before_window = self.window.size()
        before_hint = self.window.sizeHint()
        before_group = self.group.size()
        before_columns = [self.group.layout().cellRect(2, column).width() for column in (0, 2)]
        self.window._console.setPlainText("A very long console entry " * 500)
        self.group._console_widget.setTitle("An intentionally very long console caption " * 8)
        self.drain()
        self.assertEqual(self.window.size(), before_window)
        self.assertEqual(self.window.sizeHint(), before_hint)
        self.assertEqual(self.group.size(), before_group)
        self.assertEqual([self.group.layout().cellRect(2, column).width() for column in (0, 2)], before_columns)
        self.assert_console_fits()

    def test_console_refits_after_scaling_and_window_resize_without_changing_content_height(self) -> None:
        for settings in (UiSettings(global_scale=0.8, font_scale=1.3, element_scale=0.75, preview_scale=0.6),
                         UiSettings(font_scale=1.5, preview_scale=0.5), UiSettings(preview_scale=1.5)):
            self.window._set_ui_settings(settings)
            self.window.resize(1100, 700)
            self.drain()
            self.assert_console_fits()
            self.assertAlmostEqual(self.group.height(), self.group.layout().totalSizeHint().height(), delta=2)
