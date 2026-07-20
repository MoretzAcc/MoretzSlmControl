"""
Author: Moritz van Eimern
Date: 18.07.26
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import logging

import numpy as np
from PIL import Image
from numpy.typing import NDArray

from moretzslmclient.bit_map_util import byteToPhase

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)


def importNpyHologram(path: Path | str) -> NDArray[np.float32]:
    """
    Imports a hologram from a .npy file. Returns hologram as a 2D numpy array in range -pi to pi.
    """
    path = Path(path)
    if path.suffix.lower() != ".npy":
        raise ValueError("Only .npy files are supported")
    array = np.load(path)
    if array.ndim != 2:
        raise ValueError(f"Expected a two-dimensional hologram, got shape {array.shape}")
    if not np.issubdtype(array.dtype, np.floating):
        raise ValueError(f"Expected array.dtype to be np.floating, got {array.dtype} instead.")
    return array


def importBmpHologram(path: Path | str) -> NDArray[np.float32]:
    """
    Imports a hologram from a .npy file. Returns hologram as a 2D numpy array in range -pi to pi.
    """
    path = Path(path)
    if path.suffix.lower() != ".bmp":
        raise ValueError("Only .bmp files are supported")

    with Image.open(path) as image:
        if image.format != "BMP":
            raise ValueError("File does not contain a valid BMP image")
        array = np.array(image.convert("L"))
    if array.dtype != np.uint8:
        raise ValueError(f"As of now, only uint8 BMPs are supported, got {array.dtype} instead")
    return byteToPhase(array)
