"""Fast notebook display helpers for SLM phase patterns."""

from __future__ import annotations

from math import sqrt

import numpy as np
from numpy.typing import NDArray

from moretzslmclient.preview import sample_phase


def plotHologram(hologram: NDArray[np.float32], show_scale: bool = True, *, max_preview_pixels: int | None = 1_000_000) -> None:
    """Display a bounded phase preview; pass max_preview_pixels=None for native sampling."""
    if hologram.ndim != 2 or min(hologram.shape) < 1:
        raise ValueError("plotHologram expects a two-dimensional hologram")
    try:
        from matplotlib import pyplot as plt
    except ImportError as error:
        message = "plotHologram requires matplotlib. Install it with 'uv add matplotlib'."
        raise ImportError(message) from error

    height, width = hologram.shape
    preview = hologram
    if max_preview_pixels is not None:
        if max_preview_pixels < 1:
            raise ValueError("max_preview_pixels must be positive or None")
        scale = min(1.0, sqrt(max_preview_pixels / hologram.size))
        preview = sample_phase(hologram, max(1, int(width*scale)), max(1, int(height*scale)))
    with plt.ioff():
        figure, axes = plt.subplots(dpi=100)
        image = axes.imshow(
            preview,
            cmap="gray",
            extent=(0, width, 0, height),
            vmin=float(np.nanmin(hologram)),
            vmax=float(np.nanmax(hologram)),
            origin="lower",
            interpolation="nearest",
            aspect="equal",
            resample=False,
        )
        if show_scale:
            figure.colorbar(image, ax=axes, label="Phase (rad)")

    plt.show()
