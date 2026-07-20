"""Utilities for reading hologram files without a server dependency."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray


def importNpyHologram(path: Path | str) -> NDArray[np.float32]:
    """Load a two-dimensional floating-point hologram from a NumPy file."""
    path = Path(path)
    if path.suffix.lower() != ".npy":
        raise ValueError("Only .npy files are supported")
    array = np.load(path)
    if array.ndim != 2:
        raise ValueError(f"Expected a two-dimensional hologram, got shape {array.shape}")
    if not np.issubdtype(array.dtype, np.floating):
        raise ValueError(f"Expected array.dtype to be np.floating, got {array.dtype} instead.")
    return array
