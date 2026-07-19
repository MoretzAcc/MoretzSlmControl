"""
Author: Moritz van Eimern
Date: 23.03.2026
"""

# ruff: noqa: E402

from __future__ import annotations

import logging
import os

from typing import TYPE_CHECKING

import sys
import platform as _platform

from moretzslmcontrol.util.moretz_logger import SetColorfulLogging

system_name = _platform.system().lower()

# Initial configuration BEFORE Qt
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"

if system_name == "linux":
    os.environ["QT_QPA_PLATFORM"] = "xcb"
elif system_name == "windows":
    os.environ["QT_WIN_DISABLE_ACCESSIBILITY_CHECKING"] = "1"
else:
    raise Exception(f"Unsupported platform: {system_name}")


from heros import zenoh

configChanges = {
    "listen/endpoints": ["tcp/0.0.0.0:56102"]
}
zenoh.session_manager.update_config(configChanges)


# Import Qt
from PySide6.QtWidgets import QApplication

from moretzslmcontrol.userinterface.main_window import MainWindow
from moretzslmcontrol.monitor_stuff.monitor_manager import MonitorManager
from moretzslmcontrol.monitor_stuff.platform import create_platform_adapter

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    ...

SetColorfulLogging(showLevel=logging.DEBUG, deleteOtherHandlers=True)


def run(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv
    app = QApplication(argv)
    platform_adapter = create_platform_adapter(app.platformName())
    monitor_manager = MonitorManager(app=app, platform_adapter=platform_adapter)
    main_window = MainWindow(monitor_manager=monitor_manager)
    main_window.show()
    try:
        return app.exec()
    finally:
        monitor_manager.shutdown()
        zenoh.session_manager.force_close()

def main() -> None:
    print("Hello from moretzslmcontrol!")
    raise SystemExit(run())
