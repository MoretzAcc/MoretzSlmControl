"""
Author: Moritz van Eimern
Date: 20.07.2026
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from heros import HEROObserver

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)


observer = HEROObserver()

def discover_slm_heros() -> list[str]:
    heros = observer._discover()
    return [
        hero["name"]
        for hero in heros.values()
        if hero.get("class") == "SlmHeroConnector"
    ]