"""
Author: Moritz van Eimern
Date: 05.03.2026
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import logging

from numpy.typing import NDArray
import numpy as np

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)

def pixelResizeArray[T: np.generic](array: NDArray[T], targetShape: tuple[int, int], acceptableRatio: float = 1.2, defaultValue: int=128) -> NDArray[T] | None:
    targetH, targetW = targetShape
    h, w = array.shape
    if targetH != h or targetW != w:
        relativeH = targetH / h
        relativeW = targetW / w
        if acceptableRatio > relativeH > 1 / acceptableRatio and acceptableRatio > relativeW > 1 / acceptableRatio:
            logger.warning(f" Client size is not equal to image size! Client: {targetH}x{targetW} Image: {h}x{w}."
                            f"\nImage will be cropped or padded to fit the client size.")
            diffH = targetH - h
            hCorrectedArray = np.full((targetH, w), defaultValue, dtype=array.dtype)
            if diffH > 0:
                # Padding H
                lower = diffH // 2
                upper = lower + h
                hCorrectedArray[lower:upper, :] = array
            elif diffH < 0:
                # Cropping H
                lower = (-diffH) // 2
                upper = lower + targetH
                hCorrectedArray = array[lower:upper, :]
            else:
                hCorrectedArray = array
            diffW = targetW - w
            wCorrectedArray = np.full((targetH, targetW), defaultValue, dtype=array.dtype)
            if diffW > 0:
                # Padding W
                left = diffW // 2
                right = left + w
                wCorrectedArray[:, left:right] = hCorrectedArray
            elif diffW < 0:
                # Cropping W
                left = (-diffW) // 2
                right = left + targetW
                wCorrectedArray = hCorrectedArray[:, left:right]
            else:
                wCorrectedArray = hCorrectedArray
            return wCorrectedArray
        else:
            logger.error(f" Client size is not equal to image size! Client: {targetH}x{targetW} Image: {h}x{w}."
                          f"\nImage dimensions are too different for automatic correction.")
            return None
    else:
        return np.asarray(array, dtype=array.dtype, copy=True)