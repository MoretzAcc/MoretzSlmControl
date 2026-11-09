from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import numpy as np
from moretzslmcontrol.hologram_manager import HologramManager


class ResolutionChangeTest(unittest.TestCase):
    def test_resize_resets_pixel_state_without_replacing_external_identity(self) -> None:
        with patch('moretzslmcontrol.hologram_manager.SlmHeroConnector'):
            manager = HologramManager(4, 8, 'test', 'test', Mock(), Mock())
        identity = manager.heroConnector
        manager.setHologramPattern(np.ones((4, 8), dtype=np.float32))
        old_revision = manager.getLastFrameSnapshot()[0]
        manager.resize(6, 10)
        self.assertEqual(manager.shape, (6, 10))
        self.assertIs(manager.heroConnector, identity)
        self.assertIsNone(manager.getZernikeCartGridIfAvailable())
        revision, frame = manager.getLastFrameSnapshot()
        self.assertGreater(revision, old_revision)
        np.testing.assert_array_equal(frame, np.full((6, 10), 128, dtype=np.uint8))
        for pattern in manager.getPatternSnapshots():
            self.assertEqual(pattern.shape, (6, 10))
            self.assertTrue(np.all(pattern == 0))
        with self.assertRaises(ValueError):
            manager.resize(0, 10)
        self.assertEqual(manager.shape, (6, 10))
