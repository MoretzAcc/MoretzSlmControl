"""Pattern frame with a console fitted into the unused lower-left area."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QPaintEvent, QPainter, QPainterPath, QPalette, QPen, QRegion, QResizeEvent
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLayout, QSizePolicy, QStyle, QStyleOptionGroupBox, QStylePainter, QWidget


class PatternCompositionGroup(QGroupBox):
    """The console is deliberately excluded from the pattern layout's size hints."""

    def __init__(self, title: str) -> None:
        super().__init__(title)
        self._console_widget: QWidget | None = None
        self._grid: QGridLayout | None = None
        self._file_controls: tuple[QWidget, QWidget] | None = None
        self._padding_reference: QLayout | None = None
        self._notch: QPointF | None = None
        self._positioning = False
        self._position_timer = QTimer(self)
        self._position_timer.setSingleShot(True)
        self._position_timer.timeout.connect(self._position_console)

    def embed_console(
        self, console: QWidget, grid: QGridLayout, file_controls: tuple[QWidget, QWidget], padding_reference: QLayout | None = None,
    ) -> None:
        self._console_widget = console
        self._grid = grid
        self._file_controls = file_controls
        self._padding_reference = padding_reference
        console.setParent(self)
        console.setMinimumSize(0, 0)
        console.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        console.layout().setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        console.show()
        self._position_timer.start(0)

    def _frame_option(self) -> tuple[QStyleOptionGroupBox, QRect]:
        option = QStyleOptionGroupBox()
        self.initStyleOption(option)
        frame = self.style().subControlRect(QStyle.ComplexControl.CC_GroupBox, option, QStyle.SubControl.SC_GroupBoxFrame, self)
        return option, frame

    def event(self, event: QEvent) -> bool:
        result = super().event(event)
        if event.type() == QEvent.Type.LayoutRequest and hasattr(self, "_position_timer") and not self._positioning:
            self._position_timer.start(0)
        return result

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_position_timer"):
            self._position_timer.start(0)

    def _position_console(self) -> None:
        if self._positioning or self._console_widget is None or self._grid is None or self._file_controls is None:
            return
        self._positioning = True
        try:
            self._grid.activate()
            _, frame = self._frame_option()
            gap = max(2, self._grid.spacing())
            # Match the adjacent monitor section's side insets on both sides of
            # the vertical notch. The console never determines column geometry.
            reference = self._padding_reference if self._padding_reference is not None else self._grid
            side_padding = max(2, reference.contentsMargins().right())
            x = self._grid.cellRect(2, 4).left() - side_padding
            y = max(control.geometry().bottom() for control in self._file_controls) + 2 * gap
            rectangle = QRect(frame.left(), y + gap, max(0, x - frame.left() - side_padding), max(0, frame.bottom() - y - gap + 1))
            self._notch = QPointF(x, y) if rectangle.width() > 0 and rectangle.height() > 0 else None
            if self._notch is not None:
                if self._console_widget.geometry() != rectangle:
                    self._console_widget.setGeometry(rectangle)
                self._console_widget.show()
            else:
                self._console_widget.hide()
            self.update()
        finally:
            self._positioning = False

    def paintEvent(self, event: QPaintEvent) -> None:
        if self._notch is None:
            super().paintEvent(event)
            return
        option, frame = self._frame_option()
        bounds = QRectF(frame).adjusted(0.5, 0.5, -0.5, -0.5)
        left, top, right, bottom = bounds.left(), bounds.top(), bounds.right(), bounds.bottom()
        notch_x, notch_y = self._notch.x(), self._notch.y()
        radius = min(3.0, (right - notch_x) / 2, (notch_y - top) / 2, (bottom - notch_y) / 2)
        path = QPainterPath(QPointF(left + radius, top))
        path.lineTo(right - radius, top)
        path.quadTo(right, top, right, top + radius)
        path.lineTo(right, bottom - radius)
        path.quadTo(right, bottom, right - radius, bottom)
        path.lineTo(notch_x + radius, bottom)
        path.quadTo(notch_x, bottom, notch_x, bottom - radius)
        path.lineTo(notch_x, notch_y + radius)
        path.quadTo(notch_x, notch_y, notch_x - radius, notch_y)
        path.lineTo(left + radius, notch_y)
        path.quadTo(left, notch_y, left, notch_y - radius)
        path.lineTo(left, top + radius)
        path.quadTo(left, top, left + radius, top)
        path.closeSubpath()

        painter = QStylePainter(self)
        label_rect = self.style().subControlRect(QStyle.ComplexControl.CC_GroupBox, option, QStyle.SubControl.SC_GroupBoxLabel, self)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setClipRegion(QRegion(self.rect()).subtracted(QRegion(label_rect.adjusted(-2, 0, 2, 0))))
        painter.setPen(QPen(self.palette().color(QPalette.ColorRole.Mid), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        painter.restore()
        option.subControls = QStyle.SubControl.SC_GroupBoxLabel
        painter.drawComplexControl(QStyle.ComplexControl.CC_GroupBox, option)
