"""Helpers for displaying holograms in notebooks and interactive sessions."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def plotHologram(hologram: NDArray[np.float32]) -> None:
    """Display a phase hologram using a grayscale colour map."""
    try:
        from matplotlib import pyplot as plt
    except ImportError as error:
        message = "plotHologram requires matplotlib. Install it with 'uv add matplotlib'."
        raise ImportError(message) from error

    fig, ax = plt.subplots()
    image = ax.imshow(hologram, cmap="gray")
    ax.invert_yaxis()
    #fig.colorbar(image, ax=ax)
    plt.show()
