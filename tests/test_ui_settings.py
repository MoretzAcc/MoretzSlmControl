from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from moretzslmcontrol.userinterface.main_window import MainWindow
from moretzslmcontrol.util.config_file import load_configuration, save_configuration
from moretzslmcontrol.util.ui_settings import UiSettings, load_ui_settings, save_ui_settings


class UiSettingsPersistenceTest(unittest.TestCase):
    def test_first_run_creates_defaults_and_reloads_saved_factors(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "nested" / "settings.json"
            self.assertEqual(load_ui_settings(path), UiSettings())
            self.assertEqual(json.loads(path.read_text())["ui"]["font_scale"], 1)
            settings = UiSettings(global_scale=0.8, font_scale=1.5, element_scale=0.9, preview_scale=0.5)
            save_ui_settings(path, settings)
            self.assertEqual(load_ui_settings(path), settings)
            self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_invalid_settings_are_backed_up_before_replacing_with_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            original = '{"format_version": 1, "ui": {"font_scale": -1}}'
            path.write_text(original)
            with self.assertLogs("moretzslmcontrol.util.ui_settings", level="WARNING"):
                self.assertEqual(load_ui_settings(path), UiSettings())
            backups = list(path.parent.glob("settings.invalid.*.json"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), original)

    def test_nonfinite_boolean_and_out_of_range_factors_are_rejected(self) -> None:
        for value in (True, float("nan"), float("inf"), 0, 3.1, "1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                UiSettings.from_mapping({"font_scale": value})


class UiScalingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / "settings.json"
        self.manager = Mock()
        self.manager.iter_debug_views.return_value = []
        self.window = MainWindow(self.manager, settings_path=self.path)
        self.window.show()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.window.close()
        self.window._pattern_executor.shutdown(wait=True)
        self.app.processEvents()
        self.folder.cleanup()

    def test_relative_factors_are_independent_and_global_multiplies_all_three(self) -> None:
        field = self.window._shift_inputs["X"]
        font_size = field.font().pointSizeF()
        element_size = self.window._scale_up_button.width()
        preview_size = self.window._preview_labels["hologram"].width()
        self.window._set_ui_settings(replace(self.window._ui_settings, font_scale=1.5))
        self.assertAlmostEqual(field.font().pointSizeF(), font_size * 1.5)
        self.assertEqual(self.window._scale_up_button.width(), element_size)
        self.assertEqual(self.window._preview_labels["hologram"].width(), preview_size)
        self.window._set_ui_settings(replace(self.window._ui_settings, element_scale=1.5))
        self.assertEqual(self.window._scale_up_button.width(), round(element_size * 1.5))
        self.assertEqual(self.window._preview_labels["hologram"].width(), preview_size)
        self.window._set_ui_settings(replace(self.window._ui_settings, preview_scale=0.5))
        self.assertEqual(self.window._preview_labels["hologram"].width(), round(preview_size * 0.5))
        self.window._change_ui_scale(-0.5)
        self.assertAlmostEqual(field.font().pointSizeF(), font_size * 1.5 * 0.5)
        self.assertEqual(self.window._scale_up_button.width(), round(element_size * 1.5 * 0.5))
        self.assertEqual(self.window._preview_labels["hologram"].width(), round(preview_size * 0.5 * 0.5))
        self.assertEqual(load_ui_settings(self.path), self.window._ui_settings)

    def test_modeless_dialog_updates_immediately_and_sidebar_stays_synchronized(self) -> None:
        self.window._show_ui_settings()
        dialog = self.window._ui_settings_dialog
        self.assertFalse(dialog.isModal())
        dialog.fields["font_scale"].setValue(150)
        self.assertEqual(self.window._ui_settings.font_scale, 1.5)
        self.assertEqual(load_ui_settings(self.path).font_scale, 1.5)
        self.window._scale_up_button.click()
        self.assertEqual(dialog.fields["global_scale"].value(), 105)
        self.assertEqual(self.window._scale_label.text(), "Scale UI: 105%")
        self.window._show_ui_settings()
        self.assertIs(self.window._ui_settings_dialog, dialog)
        dialog._restore_defaults()
        self.assertEqual(self.window._ui_settings, UiSettings())

    def test_larger_font_keeps_unit_columns_readable_with_smaller_elements(self) -> None:
        self.window._set_ui_settings(UiSettings(font_scale=2, element_scale=0.5))
        labels = list(self.window._modification_unit_labels.values())
        self.assertEqual(len({label.width() for label in labels}), 1)
        self.assertGreaterEqual(labels[0].width(), labels[0].fontMetrics().horizontalAdvance("\u00b5m"))

    def test_new_window_restores_settings_without_font_rounding_drift(self) -> None:
        settings = UiSettings(global_scale=0.85, font_scale=1.35, element_scale=0.8, preview_scale=0.6)
        self.window._set_ui_settings(settings)
        before = self.window._shift_inputs["X"].font().pointSizeF()
        for _ in range(4):
            self.window._change_ui_scale(0.05)
            self.window._change_ui_scale(-0.05)
        self.assertAlmostEqual(self.window._shift_inputs["X"].font().pointSizeF(), before)
        other = MainWindow(self.manager, settings_path=self.path)
        try:
            self.assertEqual(other._ui_settings, settings)
            self.assertAlmostEqual(other._shift_inputs["X"].font().pointSizeF(), before)
        finally:
            other.close()
            other._pattern_executor.shutdown(wait=True)

    def test_monitor_heading_and_details_are_top_aligned(self) -> None:
        title = self.window._associated_monitor_titles[0]
        card = self.window._associated_monitor_cards[0]
        card.show()
        card.resize(400, 500)
        card.layout().activate()
        self.assertTrue(title.font().bold())
        self.assertTrue(title.alignment() & Qt.AlignmentFlag.AlignTop)
        self.assertLessEqual(title.y(), card.layout().contentsMargins().top() + 2)
        self.assertTrue(card.layout().itemAt(1).layout().formAlignment() & Qt.AlignmentFlag.AlignTop)
        self.assertTrue(self.window._associated_monitor_fields[0]["name"].alignment() & Qt.AlignmentFlag.AlignTop)

    def test_export_includes_ui_factors_and_legacy_configuration_remains_valid(self) -> None:
        uid = "test-screen"
        self.window._modification_inputs_by_screen[uid] = self.window._default_modification_inputs.copy()
        self.window._zernike_inputs_by_screen[uid] = self.window._default_zernike_inputs.copy()
        record = Mock(screen_uid=uid, width=12, height=8, display_name="test", serial_number="", screen_name="test",
                      manufacturer="", model="", port_name="", refresh_rate=60, physical_size_x=100, physical_size_y=80)
        display = Mock()
        display.getPatternFlipStates.return_value = (False,) * 6
        display.isHeroEnabled.return_value = False
        display.getPatternInclusion.return_value = {key: False for key in ("base", "hologram", "zernike", "modification")}
        import numpy as np
        pattern = np.zeros((8, 12), dtype=np.float32)
        settings = UiSettings(font_scale=1.3, preview_scale=0.7)
        self.window._set_ui_settings(settings)
        configuration = self.window._configuration_snapshot(record, display, pattern, pattern)
        exported = Path(self.folder.name) / "configuration.json"
        save_configuration(exported, configuration)
        controls = self.window._configuration_controls(load_configuration(exported))
        self.assertEqual(UiSettings.from_mapping(controls["ui"]), settings)
        self.window._set_ui_settings(UiSettings())
        self.window._update_modification_pattern = Mock()
        self.window._update_zernike_pattern = Mock()
        self.window.updatePreview = Mock()
        self.window._sync_pattern_active_checks = Mock()
        self.window._sync_pattern_flip_checks = Mock()
        self.window._apply_configuration(uid, display, configuration, controls, import_patterns=False, source_path=str(exported))
        self.assertEqual(self.window._ui_settings, settings)
        self.assertEqual(load_ui_settings(self.path), settings)
        del controls["ui"]
        self.window._apply_configuration(uid, display, configuration, controls, import_patterns=False, source_path=str(exported))
        self.assertEqual(self.window._ui_settings, settings)
