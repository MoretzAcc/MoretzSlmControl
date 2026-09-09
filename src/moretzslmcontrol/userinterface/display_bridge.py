"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations
from typing import TYPE_CHECKING
# imports here

from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    ...


class DisplayBridge(QObject):
    frameAvailable = Signal(str, int)
    statsChanged = Signal(str)
    consoleMessage = Signal(str, str, str)
    slmWindowEnableRequested = Signal(str, bool)

    def __init__(self, session_id: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._session_id = session_id

    @property
    def session_id(self) -> str:
        return self._session_id

    def notify_new_frame(self, revision: int) -> None:
        self.frameAvailable.emit(self._session_id, revision)

    def notify_stats_changed(self) -> None:
        self.statsChanged.emit(self._session_id)

    def notify_console(self, level: str, message: str) -> None:
        self.consoleMessage.emit(self._session_id, level, message)

    def request_slm_window_enable(self, value: bool) -> None:
        self.slmWindowEnableRequested.emit(self._session_id, value)
