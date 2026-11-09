"""Native Windows display inventory and reproducible application review.

Run in the signed-in desktop session, not a Windows service/session 0.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import time
import traceback
from unittest.mock import patch


def inventory() -> dict:
    import win32api
    import win32con
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    devices = []
    for index in range(32):
        try:
            device = win32api.EnumDisplayDevices(None, index)
        except win32api.error:
            break
        if not device.StateFlags & win32con.DISPLAY_DEVICE_ATTACHED_TO_DESKTOP:
            continue
        current = win32api.EnumDisplaySettings(device.DeviceName, win32con.ENUM_CURRENT_SETTINGS)
        modes = set()
        for mode_index in range(512):
            try:
                mode = win32api.EnumDisplaySettings(device.DeviceName, mode_index)
            except win32api.error:
                break
            modes.add((mode.PelsWidth, mode.PelsHeight, mode.DisplayFrequency))
        devices.append({
            "name": device.DeviceName, "description": device.DeviceString,
            "primary": bool(device.StateFlags & win32con.DISPLAY_DEVICE_PRIMARY_DEVICE),
            "current": [current.PelsWidth, current.PelsHeight, current.DisplayFrequency],
            "position": [current.Position_x, current.Position_y], "modes": sorted(modes),
        })
    return {
        "platform": sys.platform,
        "qt_platform": app.platformName(),
        "screens": [{"name": screen.name(), "geometry": screen.geometry().getRect(),
                     "available": screen.availableGeometry().getRect(), "dpr": screen.devicePixelRatio()}
                    for screen in app.screens()],
        "devices": devices,
    }


def run_matrix(output: Path) -> bool:
    import numpy as np
    import win32api
    import win32con
    from PIL import Image
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QFileDialog
    from heros import zenoh
    # Import the real entrypoint before creating Qt so its Windows settings apply.
    from moretzslmcontrol.app import MainWindow, MonitorManager, create_platform_adapter
    from moretzslmcontrol.monitor_stuff.platform.windows_edid.windows_hmonitor import get_hmonitor
    from moretzslmcontrol.monitor_stuff.platform.windows_peek import exclude_from_peek
    from moretzslmcontrol.util.bit_map_util import phaseToByte
    from moretzslmcontrol.util.config_file import load_configuration

    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    initial = inventory()
    (output / "environment.json").write_text(json.dumps(initial, indent=2), encoding="utf-8")
    targets = [device for device in initial["devices"]
               if device["description"] == "Virtual Display Driver" and not device["primary"]]
    if not targets:
        raise RuntimeError("No active secondary Virtual Display Driver output; refusing to change the primary display")
    device_name = targets[0]["name"]
    original = win32api.EnumDisplaySettings(device_name, win32con.ENUM_CURRENT_SETTINGS)
    scenarios = [("small", 800, 600), ("hd", 1366, 768), ("full-hd", 1920, 1080),
                 ("qhd", 2560, 1440), ("4k", 3840, 2160), ("portrait", 1080, 1920),
                 ("ultrawide", 3440, 1440)]
    reports = []

    def spin(seconds: float = 0.1) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            app.processEvents()
            time.sleep(0.005)

    def wait_for(condition, timeout: float = 30) -> bool:
        end = time.monotonic() + timeout
        while not condition() and time.monotonic() < end:
            spin(0.02)
        return bool(condition())

    def target_screen():
        for screen in app.screens():
            if win32api.GetMonitorInfo(get_hmonitor(screen))["Device"] == device_name:
                return screen
        raise RuntimeError(f"Qt did not expose {device_name}")

    def set_mode(width: int, height: int) -> None:
        mode = win32api.EnumDisplaySettings(device_name, win32con.ENUM_CURRENT_SETTINGS)
        mode.PelsWidth, mode.PelsHeight, mode.DisplayFrequency = width, height, 60
        mode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT | win32con.DM_DISPLAYFREQUENCY
        result = win32api.ChangeDisplaySettingsEx(device_name, mode, 0)
        if result != win32con.DISP_CHANGE_SUCCESSFUL:
            raise RuntimeError(f"ChangeDisplaySettingsEx returned {result} for {width}x{height}")
        if not wait_for(lambda: (target_screen().geometry().width(), target_screen().geometry().height()) == (width, height)):
            raise RuntimeError("Qt geometry did not follow the native mode change")
        spin(0.2)

    def compare_bytes(actual, expected) -> dict:
        # Phase wrapping can move float32 ties by one circular gray level.
        delta = (actual.astype(np.int16) - expected.astype(np.int16) + 128) % 256 - 128
        maximum = int(np.max(np.abs(delta)))
        return {"pass": maximum <= 1, "max_circular_gray_error": maximum,
                "differing_pixels": int(np.count_nonzero(delta))}

    try:
        for name, width, height in scenarios:
            report = {"scenario": name, "resolution": [width, height], "checks": []}
            reports.append(report)
            manager = window = None

            def check(label: str, passed: bool, **details) -> None:
                report["checks"].append({"name": label, "pass": bool(passed), **details})
                (output / f"{name}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

            try:
                set_mode(width, height)
                screen = target_screen()
                manager = MonitorManager(app, create_platform_adapter(app.platformName()))
                for view in manager.iter_debug_views():
                    manager.set_heros_enabled(view.screen_uid, False)
                window = MainWindow(manager)
                window.show()
                window.move(screen.availableGeometry().topLeft())
                spin(0.3)
                views = manager.iter_debug_views()
                check("one distinct record per native Qt screen", len(views) == len(app.screens()),
                      qt_screens=len(app.screens()), records=len(views))
                uid = next(view.screen_uid for view in views if view.screen_name == screen.name())
                for index in range(window._list_widget.count()):
                    if window._list_widget.item(index).data(Qt.ItemDataRole.UserRole) == uid:
                        window._list_widget.setCurrentRow(index)
                        break
                spin()
                check("control window fits target work area", screen.availableGeometry().contains(window.frameGeometry()),
                      frame=window.frameGeometry().getRect(), available=screen.availableGeometry().getRect())
                window.grab().save(str(output / f"{name}-ui.png"))
                display = manager.ensure_displayer(uid)
                check("native buffer dimensions", display.shape == (height, width), shape=list(display.shape))
                for component in ("base", "zernike", "modification"):
                    window._pattern_active_checks[component].setChecked(False)
                window._pattern_active_checks["hologram"].setChecked(True)
                phase = np.broadcast_to(np.linspace(-np.pi, np.pi, width, endpoint=False, dtype=np.float32), (height, width)).copy()
                with tempfile.TemporaryDirectory() as temp:
                    folder = Path(temp)
                    np.save(folder / "ramp.npy", phase)
                    Image.fromarray(phaseToByte(phase)).save(folder / "ramp.bmp")
                    with patch.object(QFileDialog, "getOpenFileName", return_value=(str(folder / "ramp.npy"), "")):
                        window._choose_pattern_file("hologram")
                    spin()
                    npy_match = compare_bytes(display.getLastFrameSnapshot()[1], phaseToByte(phase))
                    check("NPY import produces expected output", npy_match.pop("pass"), **npy_match)
                    window._pattern_flip_checks[("hologram", "horizontal")].setChecked(True)
                    flip_started = time.monotonic()
                    expected_flip = phaseToByte(phase[:, ::-1])
                    wait_for(lambda: compare_bytes(display.getLastFrameSnapshot()[1], expected_flip)["pass"])
                    flipped_match = compare_bytes(display.getLastFrameSnapshot()[1], phaseToByte(phase[:, ::-1]))
                    check("horizontal flip changes output", flipped_match.pop("pass"), **flipped_match,
                          completion_seconds=round(time.monotonic() - flip_started, 3))
                    with patch.object(QFileDialog, "getOpenFileName", return_value=(str(folder / "ramp.bmp"), "")):
                        window._choose_pattern_file("base")
                    check("BMP correction import", window._loaded_patterns[uid]["base"].shape == (height, width))
                    window.raise_()
                    window.activateWindow()
                    spin()
                    QTest.mouseClick(window._slm_window_button, Qt.MouseButton.LeftButton)
                    spin(0.3)
                    session = manager.get_session(uid)
                    check("SLM output visible", session.window.isVisible())
                    check("output covers exactly target screen", session.window.geometry() == screen.geometry(),
                          actual=session.window.geometry().getRect(), target=screen.geometry().getRect())
                    pixmap = session.window._label.pixmap()
                    check("output pixmap has native dimensions", (pixmap.width(), pixmap.height()) == (width, height))
                    check("output preserves control window focus", app.activeWindow() == window,
                          active=app.activeWindow().windowTitle() if app.activeWindow() else None)
                    # These DWM attributes are write-only; GetWindowAttribute returns E_INVALIDARG.
                    check("native DWM accepts Peek exclusions", exclude_from_peek(int(session.window.winId())))
                    session.window.grab().save(str(output / f"{name}-output.png"))
                    manager.deactivate_monitor(uid)
                    spin()
                    check("SLM output hides on disable", not session.window.isVisible())
                    config_path = folder / "configuration.json"
                    with patch.object(QFileDialog, "getSaveFileName", return_value=(str(config_path), "")):
                        window._export_configuration()
                    config = load_configuration(config_path)
                    check("configuration export records native dimensions", (config["slm"]["width"], config["slm"]["height"]) == (width, height))
                    if width * height <= 2_100_000:
                        with patch.object(QFileDialog, "getOpenFileName", return_value=(str(config_path), "")):
                            window._import_configuration()
                        check("configuration import calculations finish", wait_for(lambda: not window._pending_pattern_calculations))
                        check("configuration roundtrip preserves flip", display.getPatternFlipStates()[2])
                        field = window._zernike_parameter_fields["defocus"]
                        field.setText("0.25")
                        field.editingFinished.emit()
                        check("Zernike edit calculates asynchronously", wait_for(lambda: not window._pending_pattern_calculations)
                              and display._zernike_aberrations.get("defocus") == 0.25)
                        slider = window._shift_sliders["X"]
                        slider.setSliderDown(True)
                        slider.setSliderPosition(50)
                        spin()
                        check("shift field changes during drag", float(window._shift_inputs["X"].text()) != 0)
                        slider.setSliderDown(False)
                        slider.sliderReleased.emit()
                        check("modification edit calculations finish", wait_for(lambda: not window._pending_pattern_calculations))
                    if name == "full-hd":
                        manager.set_heros_enabled(uid, True)
                        code = ("from moretzslmclient import SlmHeroApi\n"
                                f"with SlmHeroApi({session.heros_name!r}) as remote:\n"
                                "    remote.setModificationX(25)\n")
                        remote = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        completed = wait_for(lambda: remote.poll() is not None, timeout=30)
                        if not completed:
                            remote.kill()
                        remote_stdout, remote_stderr = remote.communicate(timeout=5)
                        spin()
                        check("separate client process controls local HEROS", completed and remote.returncode == 0,
                              returncode=remote.returncode, stdout=remote_stdout[-2000:], stderr=remote_stderr[-2000:])
                        check("remote modification synchronizes desktop field", float(window._shift_inputs["X"].text()) == 25)
                        manager.set_heros_enabled(uid, False)
                        sessions = [manager.activate_monitor(view.screen_uid) for view in views]
                        spin(0.2)
                        check("independent output on every monitor", all(item.window.isVisible() for item in sessions)
                              and len({item.heros_name for item in sessions}) == len(app.screens()))
                        for item in sessions:
                            manager.deactivate_monitor(item.session_id)
                        old_uid = uid
                        set_mode(1024, 768)
                        spin(0.3)
                        check("live resolution change preserves screen identity", old_uid in manager._records_by_id
                              and manager._records_by_id[old_uid].is_connected)
                        check("live resolution change resizes existing buffer", display.shape == (768, 1024))
                        set_mode(width, height)
            except Exception:
                report["exception"] = traceback.format_exc()
            finally:
                if window is not None:
                    window.close()
                    window._pattern_executor.shutdown(wait=True)
                if manager is not None:
                    manager.shutdown()
                    app.screenAdded.disconnect(manager._on_screen_added)
                    app.screenRemoved.disconnect(manager._on_screen_removed)
                    for observed in manager._observed_screens:
                        try:
                            observed.geometryChanged.disconnect(manager._on_screen_geometry_changed)
                            observed.logicalDotsPerInchChanged.disconnect(manager._on_screen_geometry_changed)
                            observed.physicalDotsPerInchChanged.disconnect(manager._on_screen_geometry_changed)
                        except RuntimeError:
                            pass
                spin()
                (output / f"{name}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    finally:
        restored = win32api.ChangeDisplaySettingsEx(device_name, original, 0)
        (output / "restore.json").write_text(json.dumps({"result": restored}), encoding="utf-8")
        zenoh.session_manager.force_close()
    passed = all(not report.get("exception") and all(check["pass"] for check in report["checks"]) for report in reports)
    (output / "summary.json").write_text(json.dumps({"pass": passed, "scenarios": reports}, indent=2), encoding="utf-8")
    return passed


def run_hotplug(output: Path) -> bool:
    """Coordinate driver removal/reconnection with an elevated external runner."""
    from PySide6.QtWidgets import QApplication
    from heros import zenoh
    from moretzslmcontrol.app import MainWindow, MonitorManager, create_platform_adapter

    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    manager = MonitorManager(app, create_platform_adapter(app.platformName()))
    views = manager.iter_debug_views()
    virtual = [view for view in views if "VDD" in view.screen_name]
    if len(virtual) < 2:
        raise RuntimeError("Hotplug review requires two native VDD screens")
    for view in views:
        manager.set_heros_enabled(view.screen_uid, False)
    window = MainWindow(manager)
    window.show()
    sessions = {view.screen_uid: manager.activate_monitor(view.screen_uid) for view in virtual}
    report = {"checks": [], "initial_ids": list(sessions)}

    def wait_for(condition, timeout: float = 20) -> bool:
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            app.processEvents()
            if condition():
                return True
            time.sleep(0.02)
        return False

    def check(name: str, passed: bool) -> None:
        report["checks"].append({"name": name, "pass": bool(passed)})

    try:
        check("both virtual outputs visible before disconnect", wait_for(lambda: all(item.window.isVisible() for item in sessions.values())))
        (output / "ready.flag").write_text("ready", encoding="utf-8")
        disconnected = wait_for(lambda: all(not manager._records_by_id[uid].is_connected for uid in sessions))
        check("native disconnect marks virtual screens disconnected", disconnected)
        check("native disconnect hides corresponding output windows", all(not item.window.isVisible() for item in sessions.values()))
        check("primary display remains connected", any(record.is_connected for uid, record in manager._records_by_id.items() if uid not in sessions))
        (output / "disconnected.flag").write_text("disconnected", encoding="utf-8")
        connected = wait_for(lambda: all(manager._records_by_id[uid].is_connected for uid in sessions))
        check("native reconnect restores original screen identities", connected)
        check("native reconnect reuses original sessions", all(manager.get_session(uid) is item for uid, item in sessions.items()))
        check("native reconnect restores enabled output windows", all(item.window.isVisible() for item in sessions.values()))
        report["final_connected_ids"] = [uid for uid, record in manager._records_by_id.items() if record.is_connected]
        report["qt_screens_after_reconnect"] = [{"name": screen.name(), "geometry": screen.geometry().getRect()} for screen in app.screens()]
        manager.rescan_screens()
        wait_for(lambda: all(item.window.isVisible() for item in sessions.values()), timeout=5)
        check("manual refresh restores original screen identities", all(manager._records_by_id[uid].is_connected for uid in sessions))
        check("manual refresh restores enabled output windows", all(item.window.isVisible() for item in sessions.values()))
        report["connected_ids_after_refresh"] = [uid for uid, record in manager._records_by_id.items() if record.is_connected]
    finally:
        window.close()
        window._pattern_executor.shutdown(wait=True)
        manager.shutdown()
        zenoh.session_manager.force_close()
        (output / "hotplug.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return all(check["pass"] for check in report["checks"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--hotplug", action="store_true")
    args = parser.parse_args()
    if args.matrix or args.hotplug:
        args.output.mkdir(parents=True, exist_ok=True)
        with (args.output / "runtime.log").open("w", encoding="utf-8", buffering=1) as log, redirect_stdout(log), redirect_stderr(log):
            try:
                passed = run_hotplug(args.output) if args.hotplug else run_matrix(args.output)
            except Exception:
                traceback.print_exc()
                passed = False
            raise SystemExit(0 if passed else 1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory(), indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
