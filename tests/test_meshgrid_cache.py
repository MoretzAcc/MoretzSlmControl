from __future__ import annotations

import unittest

from moretzslmcontrol.util.patterns.meshgrid import getMeshGrid


class MeshGridCacheTest(unittest.TestCase):
    def test_reuses_read_only_grids_for_identical_dimensions(self) -> None:
        getMeshGrid.cache_clear()

        first_x, first_y = getMeshGrid(4, 3, 1.0, 2.0)
        second_x, second_y = getMeshGrid(4, 3, 1.0, 2.0)

        self.assertIs(first_x, second_x)
        self.assertIs(first_y, second_y)
        self.assertFalse(first_x.flags.writeable)
        self.assertFalse(first_y.flags.writeable)


if __name__ == "__main__":
    unittest.main()
