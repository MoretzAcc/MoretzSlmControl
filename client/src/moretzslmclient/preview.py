"""Bounded preview sampling without changing native SLM output arrays."""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def sample_phase(pattern: NDArray[np.floating], max_width: int, max_height: int) -> NDArray[np.float32]:
    if pattern.ndim != 2 or min(pattern.shape) < 1:
        raise ValueError("Preview phase must be a non-empty two-dimensional array")
    if max_width < 1 or max_height < 1:
        raise ValueError("Preview bounds must be positive")
    height, width = pattern.shape
    scale = min(max_width / width, max_height / height, 1.0)
    rows = np.linspace(0, height-1, max(1, int(height*scale)), dtype=np.intp)
    columns = np.linspace(0, width-1, max(1, int(width*scale)), dtype=np.intp)
    return np.ascontiguousarray(pattern[np.ix_(rows, columns)], dtype=np.float32)
