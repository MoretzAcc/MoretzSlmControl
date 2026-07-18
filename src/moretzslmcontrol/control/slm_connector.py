"""
Author: Moritz van Eimern
Date: 23.03.2026
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING


import threading
import warnings
from dataclasses import replace
from typing import Any

import numpy as np
from numpy.typing import NDArray

from moretzslmcontrol.control.slm_hero_connector import SlmHeroConnector
from moretzslmcontrol.userinterface.models import SessionStats
from moretzslmcontrol.util.adapt_array import pixelResizeArray
from moretzslmcontrol.util.bit_map_util import phaseToByte
from moretzslmcontrol.util.math_util import wrap_phase


if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from moretzslmcontrol.userinterface.display_bridge import DisplayBridge


logger = logging.getLogger(__name__)


class SlmConnector:
    def __init__(self, H: int, W: int, herosName: str, bridge: DisplayBridge) -> None:
        logger.info(f"Initializing SLM DisplayerV2 with resolution: {W}x{H}")
        self.herosName = herosName
        self.shape = (H, W)
        self._bridge = bridge
        self._lock = threading.Lock()

        self._baseHologram: NDArray[np.float64] = np.zeros(self.shape, dtype=np.float64)
        self._slmCorrectionPattern: NDArray[np.float64] = np.zeros(self.shape, dtype=np.float64)
        self._hologramPhasePattern: NDArray[np.float64] = np.zeros(self.shape, dtype=np.float64)

        self._includeCorrectionPattern: bool = True
        self._includeHologramPhasePattern: bool = True

        self._latestFrame: NDArray[np.uint8] = np.zeros(self.shape, dtype=np.uint8)
        self._latestRevision: int = 0
        self._stats = SessionStats()
        self.heroConnector = SlmHeroConnector(self, self.herosName) # TODO make this toggleable somehow


    def enableCorrectionPattern(self, value: bool = True) -> None:
        with self._lock:
            self._includeCorrectionPattern = value

    def enableHologramPhasePattern(self, value: bool = True) -> None:
        with self._lock:
            self._includeHologramPhasePattern = value

    def setBaseHologram(self, phaseArr: NDArray[Any] | None, update: bool = True) -> bool:
        if phaseArr is None:
            hologram = self._getBlankPattern()
        else:
            hologram = self._validate_and_resize(phaseArr, "base hologram")
            if hologram is None:
                return False
        with self._lock:
            self._baseHologram = hologram
        if update:
            self.publishCurrentPattern()
        return True

    def setHologramPhase(self, phaseArr: NDArray[Any] | None, update: bool = True) -> bool:
        if phaseArr is None:
            hologram = self._getBlankPattern()
        else:
            hologram = self._validate_and_resize(phaseArr, "phaseArr", warn_on_resize=True)
            if hologram is None:
                return False
        with self._lock:
            self._hologramPhasePattern = hologram
        if update:
            self.publishCurrentPattern()
        return True

    def setCorrectionPattern(self, phaseArr: NDArray[Any] | None, update: bool = True) -> bool:
        if phaseArr is None:
            hologram = self._getBlankPattern()
        else:
            hologram = self._validate_and_resize(phaseArr, "correction pattern", warn_on_resize=True)
            if hologram is None:
                return False
        with self._lock:
            self._slmCorrectionPattern = wrap_phase(hologram)
        if update:
            self.publishCurrentPattern()
        return True

    def setRawFrame(self, bmpArr: NDArray[Any], notify: bool = True) -> bool:
        with self._lock:
            self._stats.submitted_count += 1
        if not isinstance(bmpArr, np.ndarray) or bmpArr.ndim != 2:
            self._mark_invalid("raw frame must be a 2D numpy array")
            return False
        resized = pixelResizeArray(bmpArr, self.shape)
        if resized is None:
            self._mark_invalid("could not resize raw frame to SLM resolution")
            return False
        img = np.asarray(resized, dtype=np.uint8)
        with self._lock:
            self._latestFrame = np.ascontiguousarray(img)
            self._latestRevision += 1
            self._stats.accepted_count += 1
            self._stats.latest_revision = self._latestRevision
            revision = self._latestRevision
        self._bridge.notify_stats_changed()
        if notify:
            self._bridge.notify_new_frame(revision)
        return True

    def publishCurrentPattern(self) -> bool:
        with self._lock:
            self._stats.submitted_count += 1
            totalPhase = self._baseHologram.copy()
            if self._includeCorrectionPattern:
                totalPhase += self._slmCorrectionPattern
            if self._includeHologramPhasePattern:
                totalPhase += self._hologramPhasePattern

        totalPhase = wrap_phase(totalPhase)
        img = np.ascontiguousarray(phaseToByte(totalPhase), dtype=np.uint8)

        img = np.flipud(img) # To flip the image vertically. Like this the 0,0 coordinate is at the bottom left.

        with self._lock:
            self._latestFrame = img
            self._latestRevision += 1
            self._stats.accepted_count += 1
            self._stats.latest_revision = self._latestRevision
            revision = self._latestRevision
        self._bridge.notify_stats_changed()
        self._bridge.notify_new_frame(revision)
        return True

    def getLastFrameSnapshot(self) -> tuple[int, NDArray[np.uint8]]:
        with self._lock:
            return self._latestRevision, self._latestFrame.copy()

    def getFrameIfNewer(self, last_seen_revision: int) -> tuple[int, NDArray[np.uint8] | None]:
        with self._lock:
            if self._latestRevision <= last_seen_revision:
                return self._latestRevision, None
            return self._latestRevision, self._latestFrame.copy()

    def markFrameDisplayed(self, revision: int) -> None:
        with self._lock:
            if revision > self._stats.last_displayed_revision:
                self._stats.last_displayed_revision = revision
                self._stats.displayed_count += 1
        self._bridge.notify_stats_changed()

    def getStatsSnapshot(self) -> SessionStats:
        with self._lock:
            return replace(self._stats)

    def _getBlankPattern(self) -> NDArray[np.float64]:
        return np.zeros(self.shape, dtype=np.float64)

    def _validate_and_resize(
        self,
        arr: NDArray[Any],
        arg_name: str,
        warn_on_resize: bool = False,
    ) -> NDArray[np.float64] | None:
        if not isinstance(arr, np.ndarray) or arr.ndim != 2:
            self._mark_invalid(f"{arg_name} must be a 2D numpy array")
            return None

        with self._lock:
            self._stats.submitted_count += 1

        if arr.shape != self.shape and warn_on_resize:
            warnings.warn(
                f"{arg_name} shape {arr.shape} is different than SLM size {self.shape}. Trying to resize to SLM resolution.",
                RuntimeWarning, stacklevel=2,
            )

        resized = pixelResizeArray(arr, self.shape)
        if resized is None:
            self._mark_invalid(f"could not resize {arg_name} to SLM resolution")
            return None
        return np.asarray(resized, dtype=np.float64)

    def _mark_invalid(self, reason: str) -> None:
        logger.warning(f"DisplayerV2 rejected frame update: {reason}")
        with self._lock:
            self._stats.invalid_count += 1
        self._bridge.notify_stats_changed()
