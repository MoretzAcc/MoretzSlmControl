"""
Author: Moritz van Eimern
Date: 19.07.26
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import logging

import numpy as np
from numpy.typing import NDArray

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

    meshBaseX, meshBaseY = getMeshGrid(Nx,Ny,dx,dy)

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
