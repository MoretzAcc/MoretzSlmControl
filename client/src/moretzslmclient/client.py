"""HEROS client connection helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast

from heros import RemoteHERO

from moretzslmclient.types import SlmHeroConnector


class SlmHeroNotFoundError(NameError):
    """Raised when the requested SLM HERO is not discoverable."""


@contextmanager
def SlmHeroApi(hero_name: str) -> Iterator[SlmHeroConnector]:
    """Connect to one SLM HERO and release the remote connection afterwards."""
    try:
        with RemoteHERO(hero_name) as hero:
            yield cast(SlmHeroConnector, hero)
    except NameError as error:
        if str(error).startswith("Remote Object with name"):
            raise SlmHeroNotFoundError(
                f"HEROS could not detect the SLM with name '{hero_name}' on the network."
            ) from error
        raise
