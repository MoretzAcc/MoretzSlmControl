from __future__ import annotations

import os
from threading import Event
import time
import unittest
from unittest.mock import Mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication
from moretzslmcontrol.userinterface.main_window import MainWindow


class CalculationSchedulingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.manager = Mock()
        self.manager.iter_debug_views.return_value = []
        self.window = MainWindow(self.manager)
        self.release = Event()

    def tearDown(self) -> None:
        self.release.set()
        self.window._pattern_executor.shutdown(wait=True)
        self.app.processEvents()
        self.window.close()

    def drain(self, predicate: object) -> None:
        end = time.monotonic() + 3
        while not predicate() and time.monotonic() < end:
            self.app.processEvents()
            time.sleep(0.001)
        self.assertTrue(predicate())

    def test_zernike_only_runs_first_and_latest_request(self) -> None:
        entered = Event()
        calls = []
        def calculate(value: int) -> tuple[None, None, dict[str, int]]:
            calls.append(value)
            entered.set()
            self.release.wait(3)
            return None, None, {'defocus': value}
        self.window._start_pattern_calculation('screen', 'zernike', (0,), calculate, 0)
        self.assertTrue(entered.wait(1))
        for value in range(1, 7):
            self.window._start_pattern_calculation('screen', 'zernike', (value,), calculate, value)
        self.assertEqual(self.window._pattern_executor._work_queue.qsize(), 0)
        self.release.set()
        self.drain(lambda: not self.window._pending_pattern_calculations)
        self.assertEqual(calls, [0, 6])
        self.assertEqual(self.window._last_zernike_parameters['screen'], (6,))
        self.assertEqual(self.manager.ensure_displayer.return_value.setComputedZernikePattern.call_count, 1)

    def test_return_to_applied_value_invalidates_inflight_result(self) -> None:
        self.window._selected_screen_uid = lambda: 'screen'
        display = self.manager.ensure_displayer.return_value
        display.shape = (8, 8)
        display.getZernikeCartGridIfAvailable.return_value = None
        fields = self.window._zernike_parameter_fields
        initial = tuple(float(f.text()) for f in fields.values())
        self.window._last_zernike_parameters['screen'] = initial
        def calculate(aberrations: dict[str, float], *_: object) -> tuple[None, None, dict[str, float]]:
            self.release.wait(3)
            return None, None, aberrations
        self.window._calculate_zernike_pattern = calculate
        fields['defocus'].setText('0.9')
        self.window._update_zernike_pattern()
        fields['defocus'].setText('0')
        self.window._update_zernike_pattern()
        # Avoid preview rendering; this test checks actual scheduling and application calls.
        self.window._selected_screen_uid = lambda: None
        self.release.set()
        self.drain(lambda: not self.window._pending_pattern_calculations)
        self.assertEqual(display.setComputedZernikePattern.call_args.args[1]['defocus'], 0)

    def test_modification_only_applies_latest_request(self) -> None:
        entered = Event()
        calls = []
        def calculate(value: int) -> int:
            calls.append(value)
            entered.set()
            self.release.wait(3)
            return value
        self.window._start_pattern_calculation('screen', 'modification', (0,), calculate, 0)
        self.assertTrue(entered.wait(1))
        for value in range(1, 7):
            self.window._start_pattern_calculation('screen', 'modification', (value,), calculate, value)
        self.assertEqual(self.window._pattern_executor._work_queue.qsize(), 0)
        self.release.set()
        self.drain(lambda: not self.window._pending_pattern_calculations)
        self.assertEqual(calls, [0, 6])
        self.manager.ensure_displayer.return_value.setModificationPattern.assert_called_once_with(6)

    def test_reset_discards_queued_work_and_prevents_session_recreation(self) -> None:
        self.window._start_pattern_calculation('screen', 'modification', (1,), self.release.wait, 3)
        self.window._start_pattern_calculation('screen', 'modification', (2,), self.release.wait, 3)
        self.window._discard_session_state('screen')
        self.release.set()
        self.drain(lambda: not self.window._running_pattern_calculations)
        self.manager.ensure_displayer.assert_not_called()

    def test_drag_updates_text_before_release_without_starting_calculation(self) -> None:
        self.window._update_modification_pattern = Mock()
        slider = self.window._shift_sliders['X']
        slider.setSliderDown(True)
        slider.setSliderPosition(42)
        self.assertEqual(self.window._shift_inputs['X'].text(), '42')
        self.window._update_modification_pattern.assert_not_called()
        slider.setSliderDown(False)
        self.window._update_modification_pattern.assert_called_once()

    def test_non_drag_slider_changes_are_debounced(self) -> None:
        self.window._update_modification_pattern = Mock()
        slider = self.window._shift_sliders['Y']
        for value in (1, 2, 3):
            slider.setValue(value)
        self.assertEqual(self.window._shift_inputs['Y'].text(), '3')
        self.window._update_modification_pattern.assert_not_called()
        self.drain(lambda: self.window._update_modification_pattern.called)
        self.window._update_modification_pattern.assert_called_once()

    def test_small_window_preserves_numeric_control_height(self) -> None:
        self.window._content_stack.setCurrentWidget(self.window._details_page)
        self.window._pattern_tabs.setCurrentIndex(2)
        self.window.resize(1024, 768)
        self.window.show()
        self.app.processEvents()
        self.assertLessEqual(self.window.width(), 1024)
        for field in self.window._zernike_parameter_fields.values():
            self.assertGreaterEqual(field.height(), field.fontMetrics().height()*1.7)
            self.assertGreaterEqual(field.width(), 100)

    def test_output_action_distinguishes_state_from_action(self) -> None:
        from moretzslmcontrol.monitor_stuff.models import SessionState
        self.window._update_slm_window_button(SessionState.ACTIVE_CONNECTED)
        self.assertEqual(self.window._slm_output_status.text(), 'Output on')
        self.assertEqual(self.window._slm_window_button.text(), 'Disable SLM output')
        self.assertTrue(self.window._slm_window_button.isChecked())
        self.window._update_slm_window_button(SessionState.INACTIVE_DISCONNECTED)
        self.assertEqual(self.window._slm_output_status.text(), 'Output disconnected')
        self.assertFalse(self.window._slm_window_button.isEnabled())
