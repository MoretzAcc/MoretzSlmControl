from __future__ import annotations

import unittest
from threading import Lock
from unittest.mock import patch

import numpy as np

from moretzslmcontrol.hologram_manager import HologramManager
from moretzslmcontrol.util.patterns.zernike import makeCartGrid


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
        self.manager._zernike_aberrations = {
            "defocus": 0.0,
            "primary spherical": 0.0,
        }
        self.manager._zernike_cart_grid = makeCartGrid(Nx=4, Ny=4, dx=1.0, dy=1.0)

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

    def test_setting_zernike_aberration_regenerates_and_activates_pattern(self) -> None:
        self.manager.setZernikeAberrations({"defocus": 1.25}, update=False)

        self.assertEqual(self.manager._zernike_aberrations["defocus"], 1.25)
        self.assertTrue(self.manager.getPatternInclusion()["zernike"])
        self.assertEqual(self.manager._zernikePattern.shape, self.manager.shape)

    def test_unavailable_zernike_aberration_is_rejected_without_change(self) -> None:
        with patch("moretzslmcontrol.hologram_manager.zernike_order", 3):
            with self.assertRaisesRegex(ValueError, "requires order 4"):
                self.manager.setZernikeAberrations({"primary spherical": 1.0}, update=False)

        self.assertEqual(self.manager._zernike_aberrations["primary spherical"], 0.0)


if __name__ == "__main__":
    unittest.main()
