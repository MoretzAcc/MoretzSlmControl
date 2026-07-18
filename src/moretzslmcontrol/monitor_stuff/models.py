"""
Author: Moritz van Eimern
Date: 23.03.2026
Generated using ChatGPT
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from dataclasses import dataclass
from enum import StrEnum

if TYPE_CHECKING:  # Type hinting imports in here when cyclic imports occur
    ...


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
class MonitorRecord:
    monitor_id: str
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
    monitor_id: str
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
    monitor_id: str
    serial_number: str
    screen_name: str
    manufacturer: str
    model: str
    port_name: str
    width: int
    height: int
    refresh_rate: float
    geometry_x: int
    geometry_y: int
    physical_size_x: float
    physical_size_y: float