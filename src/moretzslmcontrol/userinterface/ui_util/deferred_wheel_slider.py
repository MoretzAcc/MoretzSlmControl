from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QSlider, QWidget


class DeferredWheelSlider(QSlider):
    wheelFinished = Signal()

    def __init__(self, orientation: Qt.Orientation, parent: QWidget | None = None) -> None:
        super().__init__(orientation, parent)
        self._wheel_timer = QTimer(self)
        self._wheel_timer.setSingleShot(True)
        self._wheel_timer.setInterval(150)
        self._wheel_timer.timeout.connect(self.wheelFinished.emit)

    def wheelEvent(self, event: QWheelEvent) -> None:
        previous_value = self.value()
        super().wheelEvent(event)
        if self.value() != previous_value:
            self._wheel_timer.start()

    def cancel_pending_wheel_update(self) -> None:
        self._wheel_timer.stop()
