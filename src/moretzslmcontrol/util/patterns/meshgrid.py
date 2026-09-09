"""
Author: Moritz van Eimern
Date: 09.09.26
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import logging

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)


def getMeshGrid(
        Nx: int,
        Ny: int,
        dx: float,
        dy: float,
) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    Nx = np.int32(Nx)
    Ny = np.int32(Ny)
    horizontalRange = np.arange(Nx, dtype=np.float32) - Nx // 2
    verticalRange = np.arange(Ny, dtype=np.float32) - Ny // 2

    # Create SLM Meshgrid
    dx: np.float32 = np.float32(dx)
    dy: np.float32 = np.float32(dy)
    x = horizontalRange * dx
    y = verticalRange * dy
    meshX, meshY = np.meshgrid(x, y)
    return meshX, meshY
