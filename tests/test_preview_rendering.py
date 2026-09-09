from __future__ import annotations

import unittest

import numpy as np

from moretzslmcontrol.userinterface.main_window import _cross_out_preview


class PreviewRenderingTest(unittest.TestCase):
    def test_cross_out_marks_both_diagonals(self) -> None:
        preview = np.full((101, 101), 128, dtype=np.uint8)

        crossed_out = _cross_out_preview(preview)

        self.assertNotEqual(crossed_out[0, 0], 128)
        self.assertNotEqual(crossed_out[0, -1], 128)
        self.assertNotEqual(crossed_out[50, 50], 128)
        self.assertEqual(crossed_out[20, 50], 128)

    def test_cross_out_preserves_the_input(self) -> None:
        preview = np.full((20, 40), 128, dtype=np.uint8)

        _cross_out_preview(preview)

        np.testing.assert_array_equal(preview, np.full_like(preview, 128))


if __name__ == "__main__":
    unittest.main()
