"""
Author: Moritz van Eimern
Date: 18.07.26
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, cast
from collections.abc import Iterator

from heros import RemoteHERO


if TYPE_CHECKING:
    from moretzslmcontrol.control.slm_connector import SlmConnector
    from moretzslmcontrol.control.slm_hero_connector import SlmHeroConnector

logger = logging.getLogger(__name__)


class SlmHeroNotFoundError(NameError):
    pass


@contextmanager
def SlmHeroApi(hero_name: str) -> Iterator[SlmConnector]:
    try:
        with RemoteHERO(hero_name) as hero:
            # noinspection PyUnnecessaryCast
            yield cast(SlmHeroConnector, hero).slm_connector
    except NameError as e:
        raise SlmHeroNotFoundError(
            f"HEROS could detect the SLM with name '{hero_name}' on the network."
        ) from e
