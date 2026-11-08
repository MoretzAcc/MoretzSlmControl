"""Exercise the real Qt UI on isolated Xorg dummy outputs; no production patches."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'xcb'

import numpy as np
from PIL import Image
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog

from moretzslmcontrol.monitor_stuff.platform import create_platform_adapter
from moretzslmcontrol.monitor_stuff.monitor_manager import MonitorManager
from moretzslmcontrol.userinterface.main_window import MainWindow
from moretzslmcontrol.util.bit_map_util import phaseToByte
from moretzslmcontrol.util.config_file import load_configuration
from heros import zenoh

parser = argparse.ArgumentParser()
parser.add_argument('--name', required=True)
parser.add_argument('--slow', action='store_true')
parser.add_argument('--collision-only', action='store_true')
parser.add_argument('--hotplug', action='store_true')
parser.add_argument('--no-desktop', action='store_true')
args = parser.parse_args()
out = Path(__file__).parent / 'results'
out.mkdir(exist_ok=True)
report = {'scenario': args.name, 'checks': []}
app = QApplication([])
app.setQuitOnLastWindowClosed(False)


def spin(seconds=0.1):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.005)


def check(name, condition, **details):
    report['checks'].append({'name': name, 'pass': bool(condition), **details})
    print(name, 'PASS' if condition else 'FAIL', details, flush=True)


def wait_for(condition, timeout=20):
    end = time.monotonic() + timeout
    while not condition() and time.monotonic() < end:
        spin(0.02)
    return bool(condition())


def matches_grayscale(actual, expected):
    # Phase wrapping and uint8 conversion can differ by one circular gray level.
    delta = (actual.astype(np.int16)-expected.astype(np.int16)+128) % 256-128
    return bool(np.max(np.abs(delta)) <= 1)


adapter = create_platform_adapter(app.platformName())
manager = MonitorManager(app, adapter)
window = MainWindow(manager)
window.show()
spin(0.3)
report['screens'] = [{'name': s.name(), 'geometry': s.geometry().getRect(), 'dpr': s.devicePixelRatio()} for s in app.screens()]
report['records'] = [{'uid': v.screen_uid, 'name': v.screen_name, 'resolution': v.resolution} for v in manager.iter_debug_views()]
window.move(app.primaryScreen().geometry().topLeft())
window.resize(app.primaryScreen().availableGeometry().size())
window.showMaximized()
spin(0.2)
window.grab().save(str(out / f'{args.name}-ui.png'))
if not args.no_desktop:
    app.primaryScreen().grabWindow(0).save(str(out / f'{args.name}-desktop.png'))
report['window_geometry'] = window.geometry().getRect()
report['numeric_field_widths'] = {k: f.width() for k, f in window._zernike_parameter_fields.items()}
check('distinct records for each Qt screen', len(manager.iter_debug_views()) == len(app.screens()), qt_screens=len(app.screens()), records=len(manager.iter_debug_views()))
check('control window fits available screen', app.primaryScreen().availableGeometry().contains(window.geometry()), window=window.geometry().getRect(), available=app.primaryScreen().availableGeometry().getRect())

try:
    if not args.collision_only:
        uid = window._selected_screen_uid()
        display = manager.ensure_displayer(uid)
        h, w = display.shape
        check('allocated buffer matches selected screen', (w, h) == (app.screens()[0].geometry().width(), app.screens()[0].geometry().height()), shape=[h,w])
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            pattern = np.broadcast_to(np.linspace(-np.pi, np.pi, w, endpoint=False, dtype=np.float32), (h,w)).copy()
            np.save(folder / 'ramp.npy', pattern)
            Image.fromarray(phaseToByte(pattern)).save(folder / 'ramp.bmp')
            with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(folder / 'ramp.npy'), '')):
                window._choose_pattern_file('hologram')
            spin()
            actual = display.getLastFrameSnapshot()[1]
            check('NPY import produces expected grayscale bytes', matches_grayscale(actual, phaseToByte(pattern)))
            with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(folder / 'ramp.bmp'), '')):
                window._choose_pattern_file('base')
            QTest.mouseClick(window._pattern_active_checks['base'], Qt.MouseButton.LeftButton)
            spin()
            check('BMP import and component toggle', not display.getPatternInclusion()['base'] and matches_grayscale(display.getLastFrameSnapshot()[1], phaseToByte(pattern)))
            flip = window._pattern_flip_checks[('hologram', 'horizontal')]
            QTest.mouseClick(flip, Qt.MouseButton.LeftButton)
            spin()
            check('horizontal flip updates output', matches_grayscale(display.getLastFrameSnapshot()[1], phaseToByte(pattern[:, ::-1])))
            window.raise_()
            window.activateWindow()
            spin()
            QTest.mouseClick(window._slm_window_button, Qt.MouseButton.LeftButton)
            spin(0.2)
            session = manager.get_session(uid)
            check('output window enabled', session.window.isVisible())
            check('output geometry matches target', session.window.geometry() == app.screens()[0].geometry(), actual=session.window.geometry().getRect(), target=app.screens()[0].geometry().getRect())
            check('output pixmap has native resolution', (session.window._label.pixmap().width(), session.window._label.pixmap().height()) == (w,h))
            session.window.grab().save(str(out / f'{args.name}-output.png'))
            check('output does not steal control-window focus', app.activeWindow() == window, active=app.activeWindow().windowTitle() if app.activeWindow() else None)
            manager.deactivate_monitor(uid)
            spin()
            check('output window disabled', not session.window.isVisible())
            config_path = folder / 'configuration.json'
            with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(config_path), '')):
                window._export_configuration()
            config = load_configuration(config_path)
            check('configuration export records resolution', (config['slm']['width'], config['slm']['height']) == (w,h))
            # A full import schedules actual pattern calculations; keep it to <= full HD.
            if w*h <= 2073600:
                with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(config_path), '')):
                    window._import_configuration()
                check('configuration import calculations complete', wait_for(lambda: not window._pending_pattern_calculations))
                check('configuration roundtrip restores flip state', display.getPatternFlipStates()[2])
                fields = list(window._zernike_parameter_fields.values())
                fields[0].setFocus()
                QTest.keyClick(fields[0], Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
                QTest.keyClicks(fields[0], '0.25')
                QTest.keyClick(fields[0], Qt.Key.Key_Tab)
                check('Zernike edit applied', wait_for(lambda: display._zernike_aberrations.get('defocus') == 0.25))
                slider = window._shift_sliders['X']
                before = window._shift_inputs['X'].text()
                slider.setSliderDown(True)
                slider.setSliderPosition(50)
                spin()
                check('slider updates numeric text during drag', window._shift_inputs['X'].text() != before, before=before, during_drag=window._shift_inputs['X'].text(), slider_value=slider.value())
                slider.setSliderDown(False)
                check('modification recalculation completes', wait_for(lambda: not window._pending_pattern_calculations))
                check('modification shift applied on release', float(window._shift_inputs['X'].text()) == 50)
                window.grab().save(str(out / f'{args.name}-edited.png'))
        if args.slow:
            component_calls = []
            original = window._calculate_zernike_pattern
            def slow(*arguments):
                component_calls.append(time.monotonic())
                time.sleep(5)
                return original(*arguments)
            window._calculate_zernike_pattern = slow
            fields = list(window._zernike_parameter_fields.values())
            ticks = []
            timer = QTimer()
            timer.timeout.connect(lambda: ticks.append(time.monotonic()))
            timer.start(20)
            started = time.monotonic()
            for i in range(6):
                fields[i].setFocus()
                QTest.keyClick(fields[i], Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
                QTest.keyClicks(fields[i], str(0.1*(i+1)))
                QTest.keyClick(fields[i], Qt.Key.Key_Tab)
                spin(0.03)
            elapsed = time.monotonic()-started
            window.grab().save(str(out / f'{args.name}-calculating.png'))
            check('can edit six Zernike fields while computation takes 5 seconds', elapsed < 2, edit_seconds=round(elapsed,3), values=[f.text() for f in fields[:6]])
            queued = window._pattern_executor._work_queue.qsize()
            check('updates coalesced to at most one pending calculation', queued <= 1, queued=queued)
            finished = wait_for(lambda: not window._pending_pattern_calculations, timeout=35)
            timer.stop()
            check('latest requested Zernike values eventually applied', finished and abs(display._zernike_aberrations['primary spherical'] - 0.6) < 1e-6, seconds=round(time.monotonic()-started,2), calls=len(component_calls), timer_ticks=len(ticks))
        if args.slow:
            # Returning to the previously applied value must invalidate an in-flight edit.
            saved = fields[0].text()
            fields[0].setText('0.9')
            window._update_zernike_pattern()
            fields[0].setText(saved)
            window._update_zernike_pattern()
            wait_for(lambda: not window._pending_pattern_calculations)
            check('return to cached Zernike value cancels obsolete work', abs(display._zernike_aberrations['defocus']-float(saved)) < 1e-6, requested=saved, applied=display._zernike_aberrations['defocus'])
            modification_calls = []
            original_modification = window._calculate_modification_pattern
            def slow_modification(*arguments):
                modification_calls.append(time.monotonic())
                time.sleep(5)
                return original_modification(*arguments)
            window._calculate_modification_pattern = slow_modification
            started = time.monotonic()
            for value in range(6):
                f = window._shift_inputs['Y']
                f.setFocus()
                QTest.keyClick(f, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
                QTest.keyClicks(f, str(value+1))
                QTest.keyClick(f, Qt.Key.Key_Tab)
                spin(0.03)
            check('can edit modification fields while computation takes 5 seconds', time.monotonic()-started < 2, edit_seconds=round(time.monotonic()-started,3))
            queued = window._pattern_executor._work_queue.qsize()
            check('modification updates coalesced', queued <= 1, queued=queued)
            finished = wait_for(lambda: not window._pending_pattern_calculations, timeout=35)
            check('latest modification value applied', finished and window._last_modification_parameters[uid][1] == 6, seconds=round(time.monotonic()-started,2), calls=len(modification_calls))
        if args.hotplug:
            old_shape = display.shape
            subprocess.run(['xrandr','--output','DUMMY0','--mode','1280x800'],check=True)
            spin(0.4)
            manager.rescan_screens()
            record = manager.get_screen_record(uid)
            check('record refreshes resolution after mode change', (record.height,record.width)==(800,1280), record=[record.height,record.width])
            check('existing session buffer resizes after mode change', display.shape==(800,1280), buffer=display.shape, previous=old_shape)
            window.grab().save(str(out / f'{args.name}-after-mode-change.png'))
            subprocess.run(['xrandr','--addmode','DUMMY1','1024x768'],check=True)
            subprocess.run(['xrandr','--output','DUMMY1','--mode','1024x768','--pos','1280x0'],check=True)
            spin(0.4)
            check('hot-added screen gets separate record', len(manager.iter_debug_views())==len(app.screens()), qt_screens=len(app.screens()), records=len(manager.iter_debug_views()))
            subprocess.run(['xrandr','--output','DUMMY1','--off'],check=True)
            spin(0.4)
            check('remaining monitor record stays connected after secondary removal', manager.get_screen_record(uid).is_connected)
        manager.reset_session(uid)
        spin()
        check('reset releases session', manager.get_session(uid) is None)
except Exception as error:
    import traceback
    report['exception'] = traceback.format_exc()
    print(report['exception'], flush=True)
finally:
    window._pattern_executor.shutdown(wait=True,cancel_futures=True)
    manager.shutdown()
    window.hide()
    zenoh.session_manager.force_close()
    (out / f'{args.name}.json').write_text(json.dumps(report,indent=2))
    print('Saved',out / f'{args.name}.json',flush=True)
