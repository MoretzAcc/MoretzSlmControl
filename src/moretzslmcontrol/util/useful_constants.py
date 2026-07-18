"""
Author: Moritz van Eimern
Date: 23.02.26
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    # Type hinting Imports in here when cyclic imports occur
    ...

PI32 = np.float32(np.pi)
INV_E2 = np.float32(np.exp(-2))
