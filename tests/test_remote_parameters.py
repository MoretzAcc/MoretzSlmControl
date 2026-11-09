from __future__ import annotations

import os
from threading import Thread
import unittest
from unittest.mock import Mock

import numpy as np

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from moretzslmcontrol.control.slm_hero_connector import SlmHeroConnector
from moretzslmcontrol.hologram_manager import HologramManager
from moretzslmcontrol.userinterface.display_bridge import DisplayBridge
from moretzslmcontrol.userinterface.main_window import MainWindow


class RemoteParametersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.bridge = DisplayBridge("screen")
        self.displayer = HologramManager(8, 12, "test", "test", self.bridge, Mock(), heros_enabled=False)
        manager = Mock()
        manager.iter_debug_views.return_value = []
        self.window = MainWindow(manager)
        self.window._selected_screen_uid = lambda: "screen"
        self.window.updatePreview = Mock()
        self.window._sync_pattern_active_checks = Mock()
        self.bridge.parametersChanged.connect(self.window._on_remote_parameters_changed)
        self.connector = object.__new__(SlmHeroConnector)
        self.connector._hologram_manager = self.displayer

    def tearDown(self) -> None:
        self.window.close()
        self.window._pattern_executor.shutdown(wait=True)
        self.app.processEvents()

    def test_remote_zernike_updates_ui_from_worker_thread(self) -> None:
        worker = Thread(target=self.connector.setZernikeAstigmatism0, args=(0.2,))
        worker.start()
        worker.join(timeout=3)
        self.assertFalse(worker.is_alive())
        self.app.processEvents()
        self.assertEqual(self.window._zernike_parameter_fields["asti 0"].text(), "0.2")
        self.assertTrue(np.any(self.displayer.getPatternSnapshots()[2]))

    def test_modification_parameters_update_pattern_fields_and_slider_range(self) -> None:
        for suffix, key, value in (
            ("X", "X", 1250), ("Y", "Y", -2300), ("Z", "Z", 3507),
            ("Wavelength", "wavelength", 780), ("FocalLength", "focal_length", 30),
            ("Magnification", "magnification", 3), ("PixelPitch", "pixel_pitch", 6),
        ):
            getattr(self.connector, f"setModification{suffix}")(value)
            fields = {**self.window._shift_inputs, **self.window._modification_parameter_fields}
            self.assertEqual(float(fields[key].text()), value)
        self.assertEqual(float(fields["max_shift"].text()), 3507)
        self.assertTrue(np.any(self.displayer.getPatternSnapshots()[3]))
        for axis, value in (("X", 1250), ("Y", -2300), ("Z", 3507)):
            slider = self.window._shift_sliders[axis]
            tick = self.window._slider_tick_size(3507)
            self.assertLessEqual(abs(slider.value() * tick - value), tick / 2)
        self.connector.setModificationX(10)
        self.assertEqual(float(fields["max_shift"].text()), 3507)

    def test_remote_setter_keeps_parameters_previously_applied_by_gui(self) -> None:
        self.displayer.rememberModificationParameters((20, 30, 40, 900, 25, 4, 6))
        self.connector.setModificationWavelength(780)
        values = self.window._modification_inputs_by_screen["screen"]
        self.assertEqual(values["X"], "20")
        self.assertEqual(values["focal_length"], "25")
        self.assertEqual(values["wavelength"], "780")

    def test_update_false_synchronizes_fields_without_publishing_frame(self) -> None:
        revision = self.displayer.getLastFrameSnapshot()[0]
        self.connector.setModificationX(500, update=False)
        self.assertEqual(self.window._shift_inputs["X"].text(), "500")
        self.assertEqual(self.displayer.getLastFrameSnapshot()[0], revision)

    def test_invalid_parameters_and_remote_slider_limit_are_rejected(self) -> None:
        original = self.displayer.getPatternSnapshots()[3]
        for values in ({"wavelength": 0}, {"X": float("nan")}, {"max_shift": 1000}):
            with self.assertRaises(ValueError):
                self.displayer.setModificationParameters(values)
        self.assertFalse(hasattr(SlmHeroConnector, "setModificationMaxShift"))
        np.testing.assert_array_equal(self.displayer.getPatternSnapshots()[3], original)

    def test_remote_change_invalidates_pending_gui_result(self) -> None:
        key = "screen", "zernike"
        self.window._pattern_calculation_revisions[key] = 1
        self.window._pending_pattern_calculations.add(key)
        self.window._queued_pattern_calculations[key] = ()
        self.connector.setZernikeAstigmatism0(0.2)
        self.window._on_pattern_calculation_finished("screen", "zernike", 1, None)
        self.assertNotIn(key, self.window._pending_pattern_calculations)
        self.assertNotIn(key, self.window._queued_pattern_calculations)

    def test_background_screen_values_are_restored_on_selection(self) -> None:
        self.window._selected_screen_uid = lambda: "other"
        self.connector.setModificationX(-1500)
        self.connector.setZernikeAstigmatism0(0.2)
        self.assertEqual(self.window._shift_inputs["X"].text(), "0")
        self.window._load_modification_inputs("screen")
        self.window._load_zernike_inputs("screen")
        self.assertEqual(self.window._shift_inputs["X"].text(), "-1500")
        self.assertEqual(self.window._zernike_parameter_fields["asti 0"].text(), "0.2")
