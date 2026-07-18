"""
Author: Moritz van Eimern
Date: 18.07.26
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import logging

import sys
from typing import Any
from dataclasses import dataclass

import pyedid

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LinuxMonitor:
    connector_name: str
    edid: Any


def get_linux_edids() -> list[LinuxMonitor]:
    if not sys.platform.startswith("linux"):
        raise OSError("This function only works on Linux.")

    drm_root = Path("/sys/class/drm")

    if not drm_root.is_dir():
        raise OSError("/sys/class/drm is not available.")

    monitors: list[LinuxMonitor] = []

    # Beispielsweise:
    # card0-DP-1
    # card0-HDMI-A-1
    # card1-eDP-1
    for connector in sorted(drm_root.glob("card*-*")):
        status_path = connector / "status"
        edid_path = connector / "edid"

        if not status_path.is_file() or not edid_path.is_file():
            continue

        try:
            status = status_path.read_text(encoding="ascii").strip()
        except OSError as error:
            logger.warning(f"{connector.name}: Connector status could not be read: {error}")
            continue

        if status != "connected":
            continue

        try:
            edid = edid_path.read_bytes()
        except OSError as error:
            logger.warning(f"{connector.name}: EDID could not be read: {error}")
            continue

        if not edid:
            logger.warning(
                f"{connector.name}: Connector found but does not provide any EDID.",
            )
            continue

        try:
            parsed_edid = pyedid.parse_edid(edid)
        except Exception as error:
            # Best Effort. Only include monitors that can be parsed.
            logger.warning(f"{connector.name}: Unable to parse EDID: {error}")
            continue

        monitors.append(
            LinuxMonitor(
                connector_name=connector.name.split("-", maxsplit=1)[1],
                edid=parsed_edid,
            )
        )

    return monitors
