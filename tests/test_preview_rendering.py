from __future__ import annotations

import unittest
import numpy as np
from moretzslmcontrol.userinterface.ui_util.cross_out_preview import disabled_preview


class PreviewRenderingTest(unittest.TestCase):
    def test_off_overlay_is_local_and_has_dark_text_on_light_background(self) -> None:
        source = np.full((90, 160), 128, dtype=np.uint8)
        result = disabled_preview(source)
        self.assertEqual(result.shape, source.shape)
        self.assertEqual(result.dtype, np.uint8)
        self.assertLess(result.min(), 64)
        self.assertGreater(result.max(), 200)
        self.assertEqual(result[0, 0], 128)
        self.assertEqual(result[-1, -1], 128)
        np.testing.assert_array_equal(source, np.full_like(source, 128))

    def test_tiny_preview_remains_valid(self) -> None:
        for shape in ((1, 1), (2, 10), (10, 2)):
            self.assertEqual(disabled_preview(np.zeros(shape, dtype=np.uint8)).shape, shape)
