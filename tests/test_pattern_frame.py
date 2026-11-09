"""Compare the notched frame with native group boxes under available Qt styles."""
from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtCore import QPointF, QRect
from PySide6.QtGui import QFont, QImage
from PySide6.QtWidgets import QApplication, QGroupBox, QStyleFactory, QWidget

from moretzslmcontrol.userinterface.pattern_composition_group import PatternCompositionGroup


class PatternFrameTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def assert_rendering_matches(self, actual: QImage, expected: QImage, region: QRect) -> None:
        ratio = actual.devicePixelRatio()
        area = QRect(round(region.x() * ratio), round(region.y() * ratio), round(region.width() * ratio), round(region.height() * ratio))
        actual = actual.copy(area).convertToFormat(QImage.Format.Format_RGB32)
        expected = expected.copy(area).convertToFormat(QImage.Format.Format_RGB32)
        first = np.frombuffer(actual.constBits(), dtype=np.uint8).astype(np.int16)
        second = np.frombuffer(expected.constBits(), dtype=np.uint8).astype(np.int16)
        # Compositing a transparent frame can round a channel by one gray level.
        self.assertLessEqual(int(np.max(np.abs(first - second))), 1)

    def test_title_and_outer_edges_match_native_group_boxes(self) -> None:
        for style_name in QStyleFactory.keys():
            for font_factor in (1, 1.5):
                with self.subTest(style=style_name, font_factor=font_factor):
                    parent = QWidget()
                    style = QStyleFactory.create(style_name)
                    style.setParent(parent)
                    parent.setStyle(style)
                    parent.resize(800, 300)
                    native = QGroupBox("Pattern composition", parent)
                    notched = PatternCompositionGroup("Pattern composition")
                    notched.setParent(parent)
                    font = QFont(self.app.font())
                    font.setPointSizeF(font.pointSizeF() * font_factor)
                    for widget in (native, notched):
                        widget.setStyle(style)
                        widget.setFont(font)
                        widget.resize(360, 260)
                    notched.move(400, 0)
                    notched._notch = QPointF(190, 130)
                    try:
                        parent.show()
                        self.app.processEvents()
                        expected = native.grab().toImage()
                        actual = notched.grab().toImage()
                        self.assert_rendering_matches(actual, expected, QRect(0, 0, 360, 60))
                        self.assert_rendering_matches(actual, expected, QRect(350, 0, 10, 260))
                        self.assert_rendering_matches(actual, expected, QRect(200, 250, 160, 10))
                        # The original lower-left border must be absent.
                        ratio = actual.devicePixelRatio()
                        cutout = QRect(0, round(180 * ratio), round(10 * ratio), round(30 * ratio))
                        self.assertNotEqual(actual.copy(cutout), expected.copy(cutout))
                    finally:
                        parent.close()
                        parent.deleteLater()
                        self.app.processEvents()
