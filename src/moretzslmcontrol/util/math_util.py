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


def wrap_phase[T: np.floating](phase: NDArray[T]) -> NDArray[T]:
    return np.mod(phase + PI32, 2 * PI32) - PI32
