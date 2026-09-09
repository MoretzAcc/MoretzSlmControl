"""
Author: Moritz van Eimern
Date: 19.07.26
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import logging

import numpy as np
from numpy.typing import NDArray

from moretzslmcontrol.util.patterns.meshgrid import getMeshGrid
from moretzslmcontrol.util.useful_constants import PI32

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)


def makeSlmPhaseForSingleFocalSpot(
        x: float,
        y: float,
        z: float,
        wavelength: float,
        f_objective: float,
        magnification: float,
        Nx: int,
        Ny: int,
        dx: float,
        dy: float,
) -> NDArray[np.float32]:
    """
    Returns the pattern to shift the intensity in the image plane.
    """
    x = np.float32(x)
    y = np.float32(y)
    z = np.float32(z)

    telescopeFocalLength = np.float32(f_objective / magnification)

    meshBaseX, meshBaseY = getMeshGrid(Nx, Ny, dx, dy)

    focalPlaneShiftPattern = (
            np.float32(2) * PI32 / (wavelength * telescopeFocalLength) * (x * meshBaseX + y * meshBaseY)
    )
    if z != 0:
        fresnelPattern = (
                z
                * PI32
                / (wavelength * telescopeFocalLength * telescopeFocalLength)
                * (meshBaseX * meshBaseX + meshBaseY * meshBaseY)
        )
    else:
        fresnelPattern = 0
    return np.asarray(focalPlaneShiftPattern + fresnelPattern, dtype=np.float32)
