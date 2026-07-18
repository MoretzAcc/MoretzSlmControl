"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from PySide6.QtGui import QScreen
    from moretzslmcontrol.control.slm_connector import SlmConnector
    from moretzslmcontrol.userinterface.platform.base import PlatformAdapter



class DisplayWindow(QWidget):
    def __init__(self, session_id: str, displayer: SlmConnector, platform_adapter: PlatformAdapter) -> None:
        super().__init__(None)
        self._session_id = session_id
        self._displayer = displayer
        self._platform_adapter = platform_adapter
        self._lastDisplayedRevision = 0
        self._attachedScreen: QScreen | None = None

        self._label = QLabel("No frame yet")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setScaledContents(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        self.setLayout(layout)
        self.setWindowTitle(f"SLM Display - {session_id}")
        self._platform_adapter.configure_display_window(self)

    def attach_to_screen(self, screen: QScreen) -> None:
        self._attachedScreen = screen
        self._platform_adapter.attach_window_to_screen(self, screen)
        self.refresh_from_displayer(force=True)

    def detach_from_screen(self) -> None:
        self._attachedScreen = None
        self._platform_adapter.detach_window_from_screen(self)

    def on_frame_available(self, session_id: str, revision: int) -> None:
        if session_id != self._session_id:
            return
        self.refresh_from_displayer(force=False)

    def refresh_from_displayer(self, force: bool = False) -> None:
        revision, frame = self._displayer.getFrameIfNewer(self._lastDisplayedRevision)
        if frame is None and not force:
            return
        if frame is None:
            revision, frame = self._displayer.getLastFrameSnapshot()
        if frame is None:
            return
        self._show_frame(frame)
        self._lastDisplayedRevision = revision
        self._displayer.markFrameDisplayed(revision)
        if self.isVisible():
            self._platform_adapter.keep_window_in_focus(self)

    def _show_frame(self, frame: np.ndarray) -> None:
        if frame.ndim != 2:
            return
        frame_c = np.ascontiguousarray(frame, dtype=np.uint8)
        h, w = frame_c.shape
        image = QImage(frame_c.data, w, h, frame_c.strides[0], QImage.Format.Format_Grayscale8).copy()
        pixmap = QPixmap.fromImage(image)
        self._label.setPixmap(pixmap)
