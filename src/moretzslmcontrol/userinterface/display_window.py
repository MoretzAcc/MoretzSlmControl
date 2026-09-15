"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QCloseEvent, QImage, QMouseEvent, QPixmap, QResizeEvent
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from PySide6.QtGui import QScreen
    from moretzslmcontrol.hologram_manager import HologramManager
    from moretzslmcontrol.monitor_stuff.platform.base import PlatformAdapter



class DisplayWindow(QWidget):
    closed = Signal()
    closeRequested = Signal()

    _EXIT_ACTIVATION_CLICK_COUNT = 3
    _EXIT_ACTIVATION_WINDOW_MS = 1_200
    _CLOSE_CONTROL_TIMEOUT_MS = 5_000
    _CLOSE_CONTROL_SIZE_RATIO = 0.05

    def __init__(
        self,
        session_id: str,
        display_name: str,
        displayer: HologramManager,
        platform_adapter: PlatformAdapter,
    ) -> None:
        super().__init__(None)
        self._session_id = session_id
        self._displayer = displayer
        self._platform_adapter = platform_adapter
        self._lastDisplayedRevision = 0
        self._attachedScreen: QScreen | None = None
        self._exitActivationClicks = 0
        self._exitActivationTimer = QTimer(self)
        self._exitActivationTimer.setSingleShot(True)
        self._exitActivationTimer.timeout.connect(self._reset_exit_activation)
        self._closeControlTimer = QTimer(self)
        self._closeControlTimer.setSingleShot(True)
        self._closeControlTimer.timeout.connect(self._hide_close_control)

        self._label = QLabel("No frame yet")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setScaledContents(True)
        self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._closeButton = QPushButton("\u00d7", self)
        self._closeButton.setAccessibleName("Close SLM display")
        self._closeButton.setStyleSheet(
            "background-color: rgba(25, 25, 25, 220);"
            "border: 1px solid rgba(255, 255, 255, 180);"
            "color: white;"
            "font-weight: bold;"
        )
        self._closeButton.clicked.connect(self.closeRequested.emit)
        self._closeButton.hide()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        self.setLayout(layout)
        self.setWindowTitle(f"{display_name} - {session_id}")
        self._platform_adapter.configure_display_window(self)

    def attach_to_screen(self, screen: QScreen) -> None:
        self._attachedScreen = screen
        self._platform_adapter.attach_window_to_screen(self, screen)
        self.refresh_from_displayer(force=True)

    def detach_from_screen(self) -> None:
        self._attachedScreen = None
        self._reset_exit_control()
        self._platform_adapter.detach_window_from_screen(self)

    def closeEvent(self, event: QCloseEvent) -> None:
        event.accept()
        self.closed.emit()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() in (
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.RightButton,
        ):
            self._register_exit_activation_click()
            event.accept()
            return
        super().mousePressEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._position_close_control()

    def _register_exit_activation_click(self) -> None:
        if self._closeButton.isVisible():
            return
        self._exitActivationClicks += 1
        if self._exitActivationClicks == 1:
            self._exitActivationTimer.start(self._EXIT_ACTIVATION_WINDOW_MS)
        if self._exitActivationClicks < self._EXIT_ACTIVATION_CLICK_COUNT:
            return
        self._reset_exit_activation()
        self._show_close_control()

    def _reset_exit_activation(self) -> None:
        self._exitActivationClicks = 0

    def _show_close_control(self) -> None:
        self._position_close_control()
        self._closeButton.show()
        self._closeButton.raise_()
        self._closeControlTimer.start(self._CLOSE_CONTROL_TIMEOUT_MS)

    def _hide_close_control(self) -> None:
        self._closeButton.hide()

    def _reset_exit_control(self) -> None:
        self._exitActivationTimer.stop()
        self._closeControlTimer.stop()
        self._reset_exit_activation()
        self._hide_close_control()

    def _position_close_control(self) -> None:
        size = round(min(self.width(), self.height()) * self._CLOSE_CONTROL_SIZE_RATIO)
        self._closeButton.setGeometry(self.width() - size, 0, size, size)

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
