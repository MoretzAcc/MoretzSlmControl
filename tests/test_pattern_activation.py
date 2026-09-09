from __future__ import annotations

import unittest
from threading import Lock

import numpy as np

from moretzslmcontrol.hologram_manager import HologramManager


class PatternActivationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = object.__new__(HologramManager)
        self.manager.shape = (4, 4)
        self.manager._lock = Lock()
        self.manager._includeCorrectionPattern = False
        self.manager._includeHologramPattern = False
        self.manager._includeZernikePattern = False
        self.manager._includeModificationPattern = False
        self.manager._flipCorrectionPatternHorizontally = False
        self.manager._flipCorrectionPatternVertically = False
        self.manager._flipHologramPatternHorizontally = False
        self.manager._flipHologramPatternVertically = False
        self.manager._flipModificationPatternHorizontally = False
        self.manager._flipModificationPatternVertically = False

    def test_setting_patterns_activates_them(self) -> None:
        self.manager.setCorrectionPattern(None, update=False)
        self.manager.setHologramPattern(None, update=False)
        self.manager.setZernikePattern(None, update=False)
        self.manager.setModificationPattern(None, update=False)

        self.assertEqual(
            self.manager.getPatternInclusion(),
            {"base": True, "hologram": True, "zernike": True, "modification": True},
        )

    def test_flipping_pattern_activates_it(self) -> None:
        self.manager._correctionPattern = np.zeros(self.manager.shape, dtype=np.float32)

        self.manager.setFlipCorrectionPatternHorizontally(True, update=False)

        self.assertTrue(self.manager.getPatternInclusion()["base"])


if __name__ == "__main__":
    unittest.main()
