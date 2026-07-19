"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
# imports here

from abc import ABC, abstractmethod

from PySide6.QtCore import Qt
from moretzslmcontrol.monitor_stuff.models import ScreenDescriptor
from pyedid import Edid
from hashlib import sha256

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from PySide6.QtGui import QScreen
    from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class MonitorEdid:
    os_identifier: str
    parsed_edid: Edid


class PlatformAdapter(ABC):
    @abstractmethod
    def get_screen_edids(self, screen: QScreen) -> list[MonitorEdid]:
        pass

    def describe_screen(self, screen: QScreen) -> ScreenDescriptor:
        edids = self.get_screen_edids(screen)
        dpr = screen.devicePixelRatio()
        geometry = screen.geometry()
        width = round(geometry.width() * dpr)
        height = round(geometry.height() * dpr)
        serial_number = screen.serialNumber().strip()
        display_name = "_".join(
            f"{edid.parsed_edid.manufacturer_pnp_id} - {f'{edid.parsed_edid.name if edid.parsed_edid.name is not None else edid.parsed_edid.product_id}'.replace(' ', '_')}"
            for edid in edids
        )
        uid_source = "_".join(
            (
                display_name,
                *(edid.os_identifier for edid in edids),
                *(f"{edid.parsed_edid.year}/{edid.parsed_edid.week}" for edid in edids),
            )
        )
        screen_uid = sha256(uid_source.encode("utf-8")).hexdigest()[:8]
        descriptor = ScreenDescriptor(
            display_name=display_name,
            screen_uid=screen_uid,
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
            associated_monitors=edids,
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
