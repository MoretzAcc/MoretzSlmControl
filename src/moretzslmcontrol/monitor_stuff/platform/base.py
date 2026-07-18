"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations

from typing import TYPE_CHECKING
# imports here

from abc import ABC

from PySide6.QtCore import Qt

from moretzslmcontrol.monitor_stuff.models import ScreenDescriptor

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from PySide6.QtGui import QScreen
    from PySide6.QtWidgets import QWidget


class PlatformAdapter(ABC):  # noqa: B024

    @staticmethod
    def describe_screen(screen: QScreen) -> ScreenDescriptor:
        dpr = screen.devicePixelRatio()
        geometry = screen.geometry()
        width = round(geometry.width() * dpr)
        height = round(geometry.height() * dpr)
        serial_number = screen.serialNumber().strip()
        monitor_id = serial_number or f"{screen.name()}_{width}x{height}_{screen.physicalSize().width()}mm_{screen.physicalSize().height()}mm"
        return ScreenDescriptor(
            monitor_id=monitor_id,
            serial_number=serial_number,
            screen_name=screen.name().strip(),
            manufacturer=screen.manufacturer().strip(),
            model=screen.model().strip(),
            port_name="",
            width=width,
            height=height,
            refresh_rate=screen.refreshRate(),
            geometry_x=geometry.x(),
            geometry_y=geometry.y(),
            physical_size_x=screen.physicalSize().width(),
            physical_size_y=screen.physicalSize().height(),
        )

    @staticmethod
    def configure_display_window(window: QWidget) -> None:
        window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

    @staticmethod
    def attach_window_to_screen(window: QWidget, screen: QScreen) -> None:
        handle = window.windowHandle()
        if handle is not None:
            handle.setScreen(screen)
        window.setGeometry(screen.geometry())
        window.showFullScreen()
        window.raise_()
        window.activateWindow()

    @staticmethod
    def detach_window_from_screen(window: QWidget) -> None:
        window.showNormal()
        window.hide()

    @staticmethod
    def keep_window_in_focus(window: QWidget) -> None:
        if window.isVisible():
            window.raise_()
            window.activateWindow()
