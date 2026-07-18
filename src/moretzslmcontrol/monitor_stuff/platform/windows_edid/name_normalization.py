"""
Author: Moritz van Eimern
Date: 18.07.2026
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)




def device_path_to_instance_prefix(device_path: str) -> str:
    path = device_path

    if path.startswith("\\\\?\\"):
        path = path[4:]

    # Interface-GUID am Ende entfernen:
    # DISPLAY#PHLC364#...#UID256#{e6f...}
    path = re.sub(
        r"#\{[0-9a-fA-F-]+}$",
        "",
        path,
    )

    return path.replace("#", "\\")


def instance_name_matches_device_path(
        instance_name: str,
        device_path: str,
) -> bool:
    """
    print()
    print("Names to compare:")
    print(f"Instance name: {instance_name}")
    print(f"Device path: {device_path}")
    print()
    """

    prefix = device_path_to_instance_prefix(device_path).casefold()
    instance = instance_name.casefold()

    return (
            instance == prefix
            or instance.startswith(prefix + "_")
    )