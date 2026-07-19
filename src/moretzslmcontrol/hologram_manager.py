"""
Author: Moritz van Eimern
Date: 23.03.2026
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING


import threading
from dataclasses import replace
from typing import Any

import numpy as np
from numpy.typing import NDArray

from moretzslmcontrol.control.slm_hero_connector import SlmHeroConnector
from moretzslmcontrol.monitor_stuff.models import SessionStats
from moretzslmcontrol.util.adapt_array import pixelResizeArray
from moretzslmcontrol.util.bit_map_util import phaseToByte
from moretzslmcontrol.util.math_util import wrap_phase


if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    from moretzslmcontrol.userinterface.display_bridge import DisplayBridge


logger = logging.getLogger(__name__)


class PatternSizeMismatchError(Exception):
    """Raised when a pattern cannot be resized to the SLM dimensions."""


class HologramManager:
    def __init__(self, H: int, W: int, herosName: str, bridge: DisplayBridge) -> None:
        logger.info(f"Initializing SLM DisplayerV2 with resolution: {W}x{H}")
        self.herosName = herosName
        self.shape = (H, W)
        self._bridge = bridge
        self._lock = threading.Lock()

        self._correctionPattern: NDArray[np.float32] = np.zeros(self.shape, dtype=np.float32)
        self._hologramPattern: NDArray[np.float32] = np.zeros(self.shape, dtype=np.float32)
        self._modificationPattern: NDArray[np.float32] = np.zeros(self.shape, dtype=np.float32)
        self._totalPattern: NDArray[np.float32] = np.zeros(self.shape, dtype=np.float32)

        self._includeCorrectionPattern: bool = True
        self._includeHologramPattern: bool = True
        self._includeModificationPattern: bool = True

        self._flipCorrectionPatternHorizontally: bool = False
        self._flipHologramPatternHorizontally: bool = False
        self._flipModificationPatternHorizontally: bool = False
        self._flipCorrectionPatternVertically: bool = False
        self._flipHologramPatternVertically: bool = False
        self._flipModificationPatternVertically: bool = False

        self._latestFrame: NDArray[np.uint8] = np.zeros(self.shape, dtype=np.uint8)
        self._latestRevision: int = 0
        self._stats = SessionStats()
        self.heroConnector = SlmHeroConnector(self, self.herosName) # TODO make this toggleable somehow


    def enableCorrectionPattern(self, value: bool = True, update: bool = True) -> None:
        with self._lock:
            self._includeCorrectionPattern = value
        if update:
            self.publishCurrentPattern()

    def enableHologramPattern(self, value: bool = True, update: bool = True) -> None:
        with self._lock:
            self._includeHologramPattern = value
        if update:
            self.publishCurrentPattern()

    def enableModificationPattern(self, value: bool = True, update: bool = True) -> None:
        with self._lock:
            self._includeModificationPattern = value
        if update:
            self.publishCurrentPattern()

    def setFlipCorrectionPatternHorizontally(self, value: bool, update: bool = True) -> None:
        self._set_pattern_flip("correction", "horizontal", value, update)

    def setFlipCorrectionPatternVertically(self, value: bool, update: bool = True) -> None:
        self._set_pattern_flip("correction", "vertical", value, update)

    def setFlipHologramPatternHorizontally(self, value: bool, update: bool = True) -> None:
        self._set_pattern_flip("hologram", "horizontal", value, update)

    def setFlipHologramPatternVertically(self, value: bool, update: bool = True) -> None:
        self._set_pattern_flip("hologram", "vertical", value, update)

    def setFlipModificationPatternHorizontally(self, value: bool, update: bool = True) -> None:
        self._set_pattern_flip("modification", "horizontal", value, update)

    def setFlipModificationPatternVertically(self, value: bool, update: bool = True) -> None:
        self._set_pattern_flip("modification", "vertical", value, update)

    def setCorrectionPattern(self, phaseArr: NDArray[np.floating] | None, update: bool = True) -> None:
        if phaseArr is None:
            hologram = self._getBlankPattern()
        else:
            hologram = self._validate_and_resize(phaseArr, "correction pattern", warn_on_resize=True)
        with self._lock:
            self._correctionPattern = self._flip_imported_pattern(
                wrap_phase(hologram),
                self._flipCorrectionPatternHorizontally,
                self._flipCorrectionPatternVertically,
            )
        if update:
            self.publishCurrentPattern()

    def setHologramPattern(self, phaseArr: NDArray[np.floating] | None, update: bool = True) -> None:
        if phaseArr is None:
            hologram = self._getBlankPattern()
        else:
            hologram = self._validate_and_resize(phaseArr, "hologram pattern", warn_on_resize=True)
        with self._lock:
            self._hologramPattern = self._flip_imported_pattern(
                wrap_phase(hologram),
                self._flipHologramPatternHorizontally,
                self._flipHologramPatternVertically,
            )
        if update:
            self.publishCurrentPattern()

    def setModificationPattern(self, phaseArr: NDArray[np.floating] | None, update: bool = True) -> None:
        if phaseArr is None:
            hologram = self._getBlankPattern()
        else:
            hologram = self._validate_and_resize(phaseArr, "modification pattern", warn_on_resize=True)
        with self._lock:
            self._modificationPattern = self._flip_imported_pattern(
                wrap_phase(hologram),
                self._flipModificationPatternHorizontally,
                self._flipModificationPatternVertically,
            )
        if update:
            self.publishCurrentPattern()

    def publishCurrentPattern(self) -> bool:
        with (self._lock):
            self._stats.submitted_count += 1
            self._totalPattern = np.zeros_like(self._totalPattern, dtype=np.float32)
            if self._includeCorrectionPattern:
                self._totalPattern += self._correctionPattern
            if self._includeHologramPattern:
                self._totalPattern += self._hologramPattern
            if self._includeModificationPattern:
                self._totalPattern += self._modificationPattern

            self._totalPattern = wrap_phase(self._totalPattern)
            total_pattern = self._totalPattern.copy()

        img = np.ascontiguousarray(phaseToByte(total_pattern), dtype=np.uint8)

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
            return replace(self._stats) # essentially a copy

    def close(self) -> None:
        """Release external control resources owned by this display manager."""
        self.heroConnector.close()

    def write_to_console(self, message: str, level: str = "info") -> None:
        """Forward a screen-scoped message to the shared console and application logger."""
        self._bridge.notify_console(level, message)

    def getPatternSnapshots(
        self,
    ) -> tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
        """Return safe copies of the correction, hologram, modification, and total patterns."""
        with self._lock:
            return (
                self._correctionPattern.copy(),
                self._hologramPattern.copy(),
                self._modificationPattern.copy(),
                self._totalPattern.copy(),
            )

    def getPatternInclusion(self) -> tuple[bool, bool, bool]:
        """Return whether correction, hologram, and modification patterns are included."""
        with self._lock:
            return (
                self._includeCorrectionPattern,
                self._includeHologramPattern,
                self._includeModificationPattern,
            )

    def getPatternFlipStates(self) -> tuple[bool, bool, bool, bool, bool, bool]:
        """Return horizontal and vertical flip states for all three component patterns."""
        with self._lock:
            return (
                self._flipCorrectionPatternHorizontally,
                self._flipCorrectionPatternVertically,
                self._flipHologramPatternHorizontally,
                self._flipHologramPatternVertically,
                self._flipModificationPatternHorizontally,
                self._flipModificationPatternVertically,
            )

    def _set_pattern_flip(
        self,
        component: str,
        direction: str,
        value: bool,
        update: bool,
    ) -> None:
        flag_name = f"_flip{component.capitalize()}Pattern{direction.capitalize()}ly"
        pattern_name = f"_{component}Pattern"
        with self._lock:
            if getattr(self, flag_name) == value:
                return
            pattern = getattr(self, pattern_name)
            flipped_pattern = np.fliplr(pattern) if direction == "horizontal" else np.flipud(pattern)
            setattr(self, pattern_name, np.ascontiguousarray(flipped_pattern, dtype=np.float32))
            setattr(self, flag_name, value)
        if update:
            self.publishCurrentPattern()

    @staticmethod
    def _flip_imported_pattern(
        pattern: NDArray[np.float32],
        flip_horizontally: bool,
        flip_vertically: bool,
    ) -> NDArray[np.float32]:
        if flip_horizontally:
            pattern = np.fliplr(pattern)
        if not flip_vertically: # Deliberate extra flip to make sure the 0,0 coordinate is at the bottom left by default.
            pattern = np.flipud(pattern)
        return np.ascontiguousarray(pattern, dtype=np.float32)

    def _getBlankPattern(self) -> NDArray[np.float32]:
        return np.zeros(self.shape, dtype=np.float32)

    def _validate_and_resize(
        self,
        arr: NDArray[Any],
        arg_name: str,
        warn_on_resize: bool = False,
    ) -> NDArray[np.float32]:
        if not isinstance(arr, np.ndarray) or arr.ndim != 2:
            message = f"{arg_name} must be a 2D numpy array"
            self._mark_invalid(message)
            raise ValueError(message)

        with self._lock:
            self._stats.submitted_count += 1

        if arr.shape != self.shape and warn_on_resize:
            self._bridge.notify_console("warning", f"{arg_name} shape {arr.shape} is different than SLM size {self.shape}. Trying to resize to SLM resolution.")

        resized = pixelResizeArray(arr, self.shape)
        if resized is None:
            message = f"{arg_name} shape {arr.shape} cannot be resized to SLM size {self.shape}"
            self._mark_invalid(message)
            raise PatternSizeMismatchError(message)
        return np.asarray(resized, dtype=np.float32)

    def _mark_invalid(self, reason: str) -> None:
        with self._lock:
            self._stats.invalid_count += 1
        self._bridge.notify_stats_changed()
        self._bridge.notify_console("error", reason)
