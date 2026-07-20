"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from dataclasses import dataclass
from enum import StrEnum

if TYPE_CHECKING:
    from moretzslmcontrol.monitor_stuff.platform.base import MonitorEdid


class SessionState(StrEnum):
    INACTIVE_CONNECTED = "inactive_connected"
    INACTIVE_DISCONNECTED = "inactive_disconnected"
    ACTIVE_CONNECTED = "active_connected"
    ACTIVE_DISCONNECTED = "active_disconnected"

    @staticmethod
    def to_string(state: SessionState) -> str:
        if state == SessionState.INACTIVE_CONNECTED:
            return "Connected - Inactive"
        if state == SessionState.INACTIVE_DISCONNECTED:
            return "Disconnected - Inactive"
        if state == SessionState.ACTIVE_CONNECTED:
            return "Connected - Active"
        if state == SessionState.ACTIVE_DISCONNECTED:
            return "Disconnected - Active"
        raise ValueError(f"Unknown SessionState: {state}")


@dataclass(slots=True)
class ScreenRecord: # A screen can be shown on multiple monitors!
    screen_uid: str
    display_name: str
    serial_number: str
    screen_name: str
    manufacturer: str
    model: str
    port_name: str
    width: int
    height: int
    geometry_x: int
    geometry_y: int
    physical_size_x: float
    physical_size_y: float
    refresh_rate: float
    associated_monitors: list[MonitorEdid]
    is_connected: bool = True
    was_ever_activated: bool = False
    last_error: str = ""
    session_id: str | None = None

    @property
    def resolution_text(self) -> str:
        return f"{self.width}x{self.height}"


@dataclass(slots=True)
class SessionStats:
    submitted_count: int = 0
    accepted_count: int = 0
    invalid_count: int = 0
    displayed_count: int = 0
    latest_revision: int = 0
    last_displayed_revision: int = 0


@dataclass(slots=True)
class SessionDebugView:
    session_id: str
    heros_name: str
    state: SessionState
    ready_for_frames: bool
    has_screen_attached: bool
    screen_uid: str
    display_name: str
    serial_number: str
    screen_name: str
    manufacturer: str
    model: str
    port_name: str
    resolution: str
    physical_size: str
    refresh_rate: str
    submitted_count: int
    accepted_count: int
    invalid_count: int
    displayed_count: int
    latest_revision: int
    last_displayed_revision: int
    last_error: str = ""


@dataclass(slots=True)
class ScreenDescriptor:
    display_name: str
    screen_uid: str
    serial_number: str # Obsolete through edid
    screen_name: str # QScreen.name is connector name for linux, arbitrary for windows tho
    manufacturer: str # Obsolete through edid
    model: str # Obsolete through edid
    port_name: str
    width: int
    height: int
    refresh_rate: float
    geometry_x: int
    geometry_y: int
    physical_size_x: float
    physical_size_y: float
    associated_monitors: list[MonitorEdid]

""" copy here for reference

class Edid(NamedTuple):
    '''Parsed EDID object'''
    manufacturer_id: int
    manufacturer: str
    manufacturer_pnp_id: str
    product_id: int
    year: int
    week: int
    edid_version: str
    type: str
    width: float
    height: float
    gamma: float
    dpms_standby: bool
    dpms_suspend: bool
    dpms_activeoff: bool
    resolutions: List[Tuple[int, int, float]]
    name: Optional[str]
    serial: Union[str, int]

"""
