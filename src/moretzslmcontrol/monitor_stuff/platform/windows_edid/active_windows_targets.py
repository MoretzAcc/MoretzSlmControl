"""
Author: Moritz van Eimern
Date: 18.07.2026
"""

from __future__ import annotations

import ctypes
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from moretzslmcontrol.monitor_stuff.platform.windows_edid.cmodels import (
    DISPLAYCONFIG_SOURCE_DEVICE_NAME,
    DISPLAYCONFIG_PATH_SOURCE_INFO,
    LUID,
    DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME,
    ERROR_SUCCESS,
    DISPLAYCONFIG_PATH_INFO,
    DISPLAYCONFIG_TARGET_DEVICE_NAME,
    DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME,
    EDID_IDS_VALID,
    QDC_ONLY_ACTIVE_PATHS,
    ERROR_INSUFFICIENT_BUFFER,
    DISPLAYCONFIG_MODE_INFO,
    UINT32,
)

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)


user32 = ctypes.WinDLL("user32", use_last_error=True)

def copy_luid(destination: LUID, source: LUID) -> None:
    destination.LowPart = source.LowPart
    destination.HighPart = source.HighPart


def get_source_device_name(
        source: DISPLAYCONFIG_PATH_SOURCE_INFO,
) -> str:
    request = DISPLAYCONFIG_SOURCE_DEVICE_NAME()

    request.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME
    request.header.size = ctypes.sizeof(request)
    copy_luid(request.header.adapterId, source.adapterId)
    request.header.id = source.id

    result = user32.DisplayConfigGetDeviceInfo(
        ctypes.byref(request)
    )

    if result != ERROR_SUCCESS:
        raise ctypes.WinError(result)

    return request.viewGdiDeviceName


@dataclass(frozen=True)
class WindowsDisplayTarget:
    gdi_device_name: str
    friendly_name: str
    monitor_device_path: str

    adapter_low_part: int
    adapter_high_part: int
    source_id: int
    target_id: int

    output_technology: int
    connector_instance: int

    edid_ids_valid: bool
    edid_manufacturer_id: int | None
    edid_product_id: int | None


def get_display_target(
        path: DISPLAYCONFIG_PATH_INFO,
) -> WindowsDisplayTarget:
    request = DISPLAYCONFIG_TARGET_DEVICE_NAME()

    request.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME
    request.header.size = ctypes.sizeof(request)
    copy_luid(
        request.header.adapterId,
        path.targetInfo.adapterId,
    )
    request.header.id = path.targetInfo.id

    result = user32.DisplayConfigGetDeviceInfo(
        ctypes.byref(request)
    )

    if result != ERROR_SUCCESS:
        raise ctypes.WinError(result)

    gdi_device_name = get_source_device_name(path.sourceInfo)
    edid_ids_valid = bool(request.flags & EDID_IDS_VALID)

    return WindowsDisplayTarget(
        gdi_device_name=gdi_device_name,
        friendly_name=request.monitorFriendlyDeviceName,
        monitor_device_path=request.monitorDevicePath,
        adapter_low_part=path.targetInfo.adapterId.LowPart,
        adapter_high_part=path.targetInfo.adapterId.HighPart,
        source_id=path.sourceInfo.id,
        target_id=path.targetInfo.id,
        output_technology=request.outputTechnology,
        connector_instance=request.connectorInstance,
        edid_ids_valid=edid_ids_valid,
        edid_manufacturer_id=(
            request.edidManufactureId
            if edid_ids_valid
            else None
        ),
        edid_product_id=(
            request.edidProductCodeId
            if edid_ids_valid
            else None
        ),
    )

def query_active_display_paths() -> list[DISPLAYCONFIG_PATH_INFO]:
    for _ in range(5):
        path_count = UINT32()
        mode_count = UINT32()

        result = user32.GetDisplayConfigBufferSizes(
            QDC_ONLY_ACTIVE_PATHS,
            ctypes.byref(path_count),
            ctypes.byref(mode_count),
        )

        if result != ERROR_SUCCESS:
            raise ctypes.WinError(result)

        path_array = (
                DISPLAYCONFIG_PATH_INFO * path_count.value
        )()

        mode_array = (
                DISPLAYCONFIG_MODE_INFO * mode_count.value
        )()

        result = user32.QueryDisplayConfig(
            QDC_ONLY_ACTIVE_PATHS,
            ctypes.byref(path_count),
            path_array,
            ctypes.byref(mode_count),
            mode_array,
            None,
        )

        if result == ERROR_INSUFFICIENT_BUFFER:
            continue

        if result != ERROR_SUCCESS:
            raise ctypes.WinError(result)

        return [
            path_array[index]
            for index in range(path_count.value)
        ]

    raise RuntimeError(
        "Die Displaykonfiguration hat sich während der Abfrage "
        "wiederholt geändert."
    )

def request_active_windows_targets() -> list[WindowsDisplayTarget]:
    return [
        get_display_target(path)
        for path in query_active_display_paths()
        if path.targetInfo.targetAvailable
    ]