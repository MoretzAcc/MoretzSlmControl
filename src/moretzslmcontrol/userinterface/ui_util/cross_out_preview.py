from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

crossout_thickness = 0.08


def cross_out_preview(preview_bytes: NDArray[np.uint8]) -> NDArray[np.uint8]:
    """Overlay a relative-width X on a grayscale preview."""
    height, width = preview_bytes.shape
    rows = np.linspace(0.0, 1.0, height)[:, np.newaxis]
    columns = np.linspace(0.0, 1.0, width)[np.newaxis, :]
    cross_mask = (np.abs(rows - columns) <= crossout_thickness / 2) | (
        np.abs(rows + columns - 1) <= crossout_thickness / 2
    )
    cross_mask_wide = (np.abs(rows - columns) <= crossout_thickness) | (
        np.abs(rows + columns - 1) <= crossout_thickness
    )
    crossed_out = preview_bytes.copy()
    crossed_out[cross_mask_wide] = np.iinfo(crossed_out.dtype).max - 2
    crossed_out[cross_mask] = 1
    return crossed_out
