"""Pattern frame with a console fitted into the unused lower-left area."""
from __future__ import annotations

from math import ceil

from PySide6.QtCore import QEvent, QPointF, QRect, Qt, QTimer
from PySide6.QtGui import QPaintEvent, QPainter, QPixmap, QRegion, QResizeEvent
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
        notch_x, notch_y = round(self._notch.x()), round(self._notch.y())
        # Use the active style for every edge and for the title. In particular,
        # let Qt decide whether the title interrupts or sits above the border.
        # A small overlap includes native rounded corners and shaded borders.
        edge_width = max(4, 2 * self.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth, option, self))
        cutout = QRect(frame.left(), notch_y - edge_width, notch_x - frame.left() + edge_width, frame.bottom() - notch_y + edge_width + 1)
        horizontal_edge = QRect(frame.left(), notch_y - edge_width, notch_x - frame.left() + 1, edge_width + 1)
        vertical_edge = QRect(notch_x, notch_y, edge_width + 1, frame.bottom() - notch_y + 1)
        painter = QStylePainter(self)
        outer = QStyleOptionGroupBox(option)
        outer.subControls = QStyle.SubControl.SC_GroupBoxFrame
        self._draw_native_part(painter, outer, QRegion(self.rect()).subtracted(QRegion(cutout)))

        upper = QStyleOptionGroupBox(option)
        upper.rect.setBottom(notch_y)
        upper.subControls = QStyle.SubControl.SC_GroupBoxFrame
        self._draw_native_part(painter, upper, QRegion(horizontal_edge))

        right = QStyleOptionGroupBox(option)
        right.rect.setLeft(notch_x)
        right.subControls = QStyle.SubControl.SC_GroupBoxFrame
        self._draw_native_part(painter, right, QRegion(vertical_edge))

        # Draw text directly on the widget to retain the native font rendering.
        title = QStyleOptionGroupBox(option)
        title.subControls = QStyle.SubControl.SC_GroupBoxLabel
        self.style().drawComplexControl(QStyle.ComplexControl.CC_GroupBox, title, painter, self)

    def _draw_native_part(self, painter: QPainter, option: QStyleOptionGroupBox, region: QRegion) -> None:
        # Some styles replace the painter clip while drawing the title/frame.
        # Composite their output afterwards so they cannot repaint the cutout.
        bounds = region.boundingRect()
        ratio = self.devicePixelRatioF()
        layer = QPixmap(ceil(bounds.width() * ratio), ceil(bounds.height() * ratio))
        layer.setDevicePixelRatio(ratio)
        layer.fill(Qt.GlobalColor.transparent)
        native = QPainter(layer)
        native.setFont(self.font())
        native.setRenderHints(painter.renderHints())
        native.translate(-bounds.topLeft())
        self.style().drawComplexControl(QStyle.ComplexControl.CC_GroupBox, option, native, self)
        native.end()
        painter.save()
        painter.setClipRegion(region)
        painter.drawPixmap(bounds.topLeft(), layer)
        painter.restore()
