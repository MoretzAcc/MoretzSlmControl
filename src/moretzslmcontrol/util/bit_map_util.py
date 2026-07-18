"""
Author: Moritz van Eimern
Date: 18.07.26
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from moretzslmcontrol.util.useful_constants import PI32

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    ...

def phaseToByte(phase: NDArray[np.float32]) -> NDArray[np.uint8]:
    """
    Converts an array ranging from -pi to pi into a byte array ranging from 0 to 255
    """

    if phase.dtype != np.float32:
        raise ValueError("byteToPhase expects a uint8 array")
    val = np.asarray(phase, dtype=np.float32) * 128 / PI32 + 128
    return np.mod(val.round(), 256).astype(np.uint8)

def byteToPhase(byte: NDArray[np.uint8]) -> NDArray[np.float32]:
    """
    Converts a byte array ranging from 0 to 255 into a phase array ranging from -pi to pi
    """
    if byte.dtype != np.uint8:
        raise ValueError("byteToPhase expects a uint8 array")
    val = np.mod(np.asarray(byte, dtype=np.uint8).astype(np.uint32), 256)
    return val * (PI32 / 128)  - PI32
