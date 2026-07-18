"""
Author: Moritz van Eimern
Date: 26.01.2026
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Type hinting Imports in here
    ...


def SetColorfulLogging(
        showLevel: int = logging.DEBUG, deleteOtherHandlers: bool = True) -> None:
    if deleteOtherHandlers:
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

    from colorlog import ColoredFormatter
    handler = logging.StreamHandler()

    formatter = ColoredFormatter(
        "%(log_color)s[%(levelname)s]%(reset)s %(message)s",
        log_colors={
            "DEBUG": "white",
            "INFO": "light_white",
            "WARNING": "light_yellow",
            "ERROR": "light_red",
            "CRITICAL": "bold_light_red",
        }
    )

    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(showLevel)
    logger.addHandler(handler)