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


def discover_slm_heros() -> list[str]:
    """Discover on demand and release the network session before returning."""
    with HEROObserver() as observer:
        heros = observer.known_objects
        return [hero["name"] for hero in heros.values() if hero.get("class") == "SlmHeroConnector"]
