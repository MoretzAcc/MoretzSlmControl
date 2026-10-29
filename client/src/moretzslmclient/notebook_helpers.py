"""Fast notebook display helpers for SLM phase patterns."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def plotHologram(hologram: NDArray[np.float32], show_scale: bool = True) -> None:
    """Display a two-dimensional SLM phase pattern without resampling it."""
    if hologram.ndim != 2:
        raise ValueError("plotHologram expects a two-dimensional hologram")
    try:
        from matplotlib import pyplot as plt
    except ImportError as error:
        message = "plotHologram requires matplotlib. Install it with 'uv add matplotlib'."
        raise ImportError(message) from error

    with plt.ioff():
        figure, axes = plt.subplots(dpi=100)
        image = axes.imshow(
            hologram,
            cmap="gray",
            origin="lower",
            interpolation="nearest",
            aspect="equal",
            resample=False,
        )
        if show_scale:
            figure.colorbar(image, ax=axes, label="Phase (rad)")

    plt.show()
