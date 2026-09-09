"""
Author: Moritz van Eimern
Date: 09.09.26
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import logging

import numpy as np
from numpy.typing import NDArray
from zernike import RZern

from moretzslmcontrol.util.patterns.meshgrid import getMeshGrid

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)

# Hard Coded Max Zernike order
zernike_order = 4

# Hard Coded Zernike modes and Names
zernike_modes = {
    "defocus": (2, 0),
    "asti 0": (2, 2),
    "asti 45": (2, -2),
    "coma 0": (3, 1),
    "coma 90": (3, -1),
    "primary spherical": (4, 0),
    "trefoil 0": (3, 3),
    "trefoil 90": (3, -3),
    "asti 2nd 0": (4, 2),
    "asti 2nd 45": (4, -2),
    "coma 2nd 0": (5, 1),
    "coma 2nd 90": (5, -1),
    "secondary spherical": (6, 0),
}

def makeCartGrid(
        Nx: int,
        Ny: int,
        dx: float,
        dy: float,
        unit_radius: float = 1.0
) -> RZern:
    cart = RZern(zernike_order)
    cart.numpy_dtype = "float32"

    meshX, meshY = getMeshGrid(Nx, Ny, dx, dy)
    scaled_radius = np.minimum(meshX.max(), meshY.max()) * unit_radius

    zernMeshX = meshX / scaled_radius
    zernMeshY = meshY / scaled_radius

    cart.make_cart_grid(zernMeshX, zernMeshY, unit_circle=False)
    return cart


def makeZernikeCoefficients(cart: RZern, aberrations: dict[str, float]) -> NDArray[np.float32]:
    c = np.zeros(cart.nk, dtype=np.float32)

    for name, value in aberrations.items():
        n, m = zernike_modes[name]
        if n > cart.n:
            continue
        c[cart.nm2noll(n, m) - 1] = value
    return c

def makePattern(cart: RZern, aberrations: dict[str, float]) -> NDArray[np.float32]:
    c = makeZernikeCoefficients(cart, aberrations)
    return cart.eval_grid(c, matrix=True)