"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from moretzslmcontrol.userinterface.platform import PlatformAdapter

# imports here

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from PySide6.QtWidgets import QWidget


class WindowsPlatformAdapter(PlatformAdapter):

    def detach_window_from_screen(self, window: QWidget) -> None:
        window.showMinimized()
        window.hide()

    def keep_window_in_focus(self, window: QWidget) -> None:
        super().keep_window_in_focus(window)

