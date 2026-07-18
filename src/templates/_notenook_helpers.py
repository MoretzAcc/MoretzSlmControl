
"""
Author: Moritz van Eimern
Date: 18.07.26
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import logging

import numpy as np
from matplotlib import pyplot as plt
from numpy.typing import NDArray

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)


def plotHologram(hologram: NDArray[np.float32]) -> None:
    fig, ax = plt.subplots()

    im = ax.imshow(hologram, cmap="gray")
    ax.invert_yaxis()
    fig.colorbar(im, ax=ax)

    plt.show()