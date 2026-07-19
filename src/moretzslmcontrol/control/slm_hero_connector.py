"""
Author: Moritz van Eimern
Date: 18.07.26
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import logging

import numpy as np
from heros import LocalHERO
from numpy.typing import NDArray


if TYPE_CHECKING:
    from moretzslmcontrol.monitor_stuff.models import SessionStats
    from moretzslmcontrol.hologram_manager import HologramManager

logger = logging.getLogger(__name__)


class SlmHeroConnector(LocalHERO):
    def __init__(self, hologram_manager: HologramManager, heros_name: str, *args, **kwargs) -> None:
        super().__init__(heros_name, *args, **kwargs)
        self._hologram_manager = hologram_manager
        logger.info(f"SLM is available as a Hero with name: {heros_name}")

    def close(self) -> None:
        """Release the HERO queryables and its Zenoh session reference."""
        if getattr(self, "_hero_destroyed", False):
            return
        self._destroy_hero()

    def enableCorrectionPattern(self, value: bool = True, update: bool = True) -> None:
        self._log_setter("enableCorrectionPattern")
        self._hologram_manager.enableCorrectionPattern(value, update)

    def enableHologramPattern(self, value: bool = True, update: bool = True) -> None:
        self._log_setter("enableHologramPattern")
        self._hologram_manager.enableHologramPattern(value, update)

    def enableModificationPattern(self, value: bool = True, update: bool = True) -> None:
        self._log_setter("enableModificationPattern")
        self._hologram_manager.enableModificationPattern(value, update)

    def setFlipCorrectionPatternHorizontally(self, value: bool, update: bool = True) -> None:
        self._log_setter("setFlipCorrectionPatternHorizontally")
        self._hologram_manager.setFlipCorrectionPatternHorizontally(value, update)

    def setFlipCorrectionPatternVertically(self, value: bool, update: bool = True) -> None:
        self._log_setter("setFlipCorrectionPatternVertically")
        self._hologram_manager.setFlipCorrectionPatternVertically(value, update)

    def setFlipHologramPatternHorizontally(self, value: bool, update: bool = True) -> None:
        self._log_setter("setFlipHologramPatternHorizontally")
        self._hologram_manager.setFlipHologramPatternHorizontally(value, update)

    def setFlipHologramPatternVertically(self, value: bool, update: bool = True) -> None:
        self._log_setter("setFlipHologramPatternVertically")
        self._hologram_manager.setFlipHologramPatternVertically(value, update)

    def setFlipModificationPatternHorizontally(self, value: bool, update: bool = True) -> None:
        self._log_setter("setFlipModificationPatternHorizontally")
        self._hologram_manager.setFlipModificationPatternHorizontally(value, update)

    def setFlipModificationPatternVertically(self, value: bool, update: bool = True) -> None:
        self._log_setter("setFlipModificationPatternVertically")
        self._hologram_manager.setFlipModificationPatternVertically(value, update)

    def setCorrectionPattern(
        self, phaseArr: NDArray[np.floating] | None, update: bool = True
    ) -> None:
        self._log_setter("setCorrectionPattern")
        self._hologram_manager.setCorrectionPattern(phaseArr, update)

    def setHologramPattern(
        self, phaseArr: NDArray[np.floating] | None, update: bool = True
    ) -> None:
        self._log_setter("setHologramPattern")
        self._hologram_manager.setHologramPattern(phaseArr, update)

    def setModificationPattern(
        self, phaseArr: NDArray[np.floating] | None, update: bool = True
    ) -> None:
        self._log_setter("setModificationPattern")
        self._hologram_manager.setModificationPattern(phaseArr, update)

    def _log_setter(self, method_name: str) -> None:
        self._hologram_manager.write_to_console(f"Heros: {method_name} requested.")

    def getLastFrameSnapshot(self) -> tuple[int, NDArray[np.uint8]]:
        return self._hologram_manager.getLastFrameSnapshot()

    def getFrameIfNewer(self, last_seen_revision: int) -> tuple[int, NDArray[np.uint8] | None]:
        return self._hologram_manager.getFrameIfNewer(last_seen_revision)

    def getStatsSnapshot(self) -> SessionStats:
        return self._hologram_manager.getStatsSnapshot()

    def getPatternSnapshots(
        self,
    ) -> tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
        return self._hologram_manager.getPatternSnapshots()

    def getPatternInclusion(self) -> tuple[bool, bool, bool]:
        """Return whether correction, hologram, and modification patterns are included."""
        return self._hologram_manager.getPatternInclusion()

    def getPatternFlipStates(self) -> tuple[bool, bool, bool, bool, bool, bool]:
        """Return horizontal and vertical flip states for all three component patterns."""
        return self._hologram_manager.getPatternFlipStates()
