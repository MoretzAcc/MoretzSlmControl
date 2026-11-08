from __future__ import annotations

import unittest
from unittest.mock import patch
import numpy as np
from moretzslmclient.preview import sample_phase


class PreviewSamplingTest(unittest.TestCase):
    def test_sampling_is_bounded_includes_edges_and_preserves_source(self) -> None:
        source = np.arange(100*200, dtype=np.float32).reshape(100, 200)
        preview = sample_phase(source, 40, 20)
        self.assertEqual(preview.shape, (20, 40))
        self.assertEqual(preview[0, 0], source[0, 0])
        self.assertEqual(preview[-1, -1], source[-1, -1])
        preview[:] = 0
        self.assertEqual(source[-1, -1], 19999)

    def test_notebook_preview_retains_native_extent_and_supports_full_resolution(self) -> None:
        import matplotlib
        matplotlib.use('Agg')
        from matplotlib import pyplot as plt
        from moretzslmclient.notebook_helpers import plotHologram
        phase = np.ones((600, 800), dtype=np.float32)
        with patch.object(plt, 'show'):
            plotHologram(phase, max_preview_pixels=12000)
            image = plt.gcf().axes[0].images[0]
            self.assertLessEqual(image.get_array().size, 12000)
            self.assertEqual(tuple(image.get_extent()), (0, 800, 0, 600))
            plt.close('all')
            plotHologram(phase, show_scale=False, max_preview_pixels=None)
            self.assertEqual(plt.gcf().axes[0].images[0].get_array().shape, phase.shape)
            plt.close('all')
