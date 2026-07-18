"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations

from typing import TYPE_CHECKING
# imports here

from abc import ABC, abstractstaticmethod, abstractmethod

from PySide6.QtCore import Qt

from moretzslmcontrol.monitor_stuff.models import ScreenDescriptor
from pyedid import Edid

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from PySide6.QtGui import QScreen
    from PySide6.QtWidgets import QWidget


class PlatformAdapter(ABC):  # noqa: B024

    @abstractmethod
    def get_screen_edids(self, screen: QScreen) -> Edid | None:
        pass

    def describe_screen(self, screen: QScreen) -> ScreenDescriptor:
        edids = self.get_screen_edids(screen) # TODO what now? put extra info into descriptor? Especially since edid might be None?
        dpr = screen.devicePixelRatio()
        geometry = screen.geometry()
        width = round(geometry.width() * dpr)
        height = round(geometry.height() * dpr)
        serial_number = screen.serialNumber().strip()
        monitor_id = (
            serial_number
            or f"{screen.name()}_{width}x{height}_{screen.physicalSize().width()}mm_{screen.physicalSize().height()}mm"
        )
        descriptor = ScreenDescriptor(
            monitor_id=monitor_id,
            serial_number=serial_number,
            connector_name=screen.name().strip(),
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
        return descriptor

    def configure_display_window(self, window: QWidget) -> None:
        window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

    def attach_window_to_screen(self, window: QWidget, screen: QScreen) -> None:
        handle = window.windowHandle()
        if handle is not None:
            handle.setScreen(screen)
        window.setGeometry(screen.geometry())
        window.showFullScreen()
        window.raise_()
        window.activateWindow()

    def detach_window_from_screen(self, window: QWidget) -> None:
        window.showNormal()
        window.hide()

    def keep_window_in_focus(self, window: QWidget) -> None:
        if window.isVisible():
            window.raise_()
            window.activateWindow()
