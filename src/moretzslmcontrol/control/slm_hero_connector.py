"""
Author: Moritz van Eimern
Date: 18.07.26
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import logging

from heros import LocalHERO

if TYPE_CHECKING:
    from moretzslmcontrol.control.slm_connector import SlmConnector

logger = logging.getLogger(__name__)


class SlmHeroConnector(LocalHERO):
    def __init__(self, slm_connector: SlmConnector, heros_name: str, *args, **kwargs) -> None:
        super().__init__(heros_name, *args, **kwargs)
        self.slm_connector = slm_connector
        logger.info(f"SLM is available as a Hero with name: {heros_name}")
