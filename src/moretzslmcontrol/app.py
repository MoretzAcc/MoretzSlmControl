"""
Author: Moritz van Eimern
Date: 23.03.2026
"""

# ruff: noqa: E402

from __future__ import annotations

import logging
import os
import signal
from pathlib import Path

from typing import TYPE_CHECKING

import sys
import platform as _platform

from moretzslmcontrol.util.moretz_logger import SetColorfulLogging
from moretzslmcontrol.util.shutdown_reason import ShutdownReason, shutdown_timestamp
from heros import zenoh

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

# Import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from moretzslmcontrol.userinterface.main_window import MainWindow
from moretzslmcontrol.monitor_stuff.monitor_manager import MonitorManager
from moretzslmcontrol.monitor_stuff.platform import create_platform_adapter

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    ...

SetColorfulLogging(showLevel=logging.INFO, deleteOtherHandlers=True)

logger = logging.getLogger(__name__)


def _install_signal_handlers(app: QApplication, shutdown_reason: ShutdownReason) -> None:
    """Request a clean Qt shutdown for signals supported on Linux and Windows."""
    def handle_signal(signal_number: int, _frame: object) -> None:
        signal_name = signal.Signals(signal_number).name
        shutdown_reason.record(f"received {signal_name}")
        app.exit(128 + signal_number)

    for signal_number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signal_number, handle_signal)


def run(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv
    app = QApplication(argv)
    shutdown_reason = ShutdownReason()
    _install_signal_handlers(app, shutdown_reason)
    app.commitDataRequest.connect(
        lambda _session_manager: shutdown_reason.record(
            "Closed by the OS desktop session manager."
        )
    )
    monitor_manager: MonitorManager | None = None
    try:
        BASE_DIR = Path(__file__).resolve().parent
        ICON_PATH = BASE_DIR / "assets" / "icon.png"
        app.setWindowIcon(QIcon(str(ICON_PATH)))

        platform_adapter = create_platform_adapter(app.platformName())
        monitor_manager = MonitorManager(app=app, platform_adapter=platform_adapter)
        main_window = MainWindow(
            monitor_manager=monitor_manager,
            on_close_requested=lambda: shutdown_reason.record("Manually closed by user."),
        )
        main_window.show()
        return app.exec()
    except KeyboardInterrupt:
        shutdown_reason.record("keyboard interrupt (SIGINT)")
        return 130
    except Exception as error:
        shutdown_reason.record(f"Unrecoverable crash: {type(error).__name__}: {error}")
        raise
    finally:
        logger.info("[%s] Closing application: %s", shutdown_timestamp(), shutdown_reason.value)
        if monitor_manager is not None:
            monitor_manager.shutdown()
        zenoh.session_manager.force_close()


def main() -> None:
    print("Starting moretzslmcontrol...")
    raise SystemExit(run())
