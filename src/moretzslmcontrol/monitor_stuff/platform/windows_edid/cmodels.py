"""
Author: Moritz van Eimern
Date: 18.07.2026
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import ctypes
from ctypes import wintypes


if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)


UINT16 = wintypes.WORD
UINT32 = wintypes.DWORD
UINT64 = ctypes.c_uint64

QDC_ONLY_ACTIVE_PATHS = 0x00000002

DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME = 1
DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME = 2

ERROR_SUCCESS = 0
ERROR_INSUFFICIENT_BUFFER = 122

EDID_IDS_VALID = 0x00000004


class LUID(ctypes.Structure):
    _fields_ = [
        ("LowPart", wintypes.DWORD),
        ("HighPart", wintypes.LONG),
    ]


class DISPLAYCONFIG_RATIONAL(ctypes.Structure):
    _fields_ = [
        ("Numerator", UINT32),
        ("Denominator", UINT32),
    ]


class DISPLAYCONFIG_2DREGION(ctypes.Structure):
    _fields_ = [
        ("cx", UINT32),
        ("cy", UINT32),
    ]


class POINTL(ctypes.Structure):
    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG),
    ]


class RECTL(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class DISPLAYCONFIG_VIDEO_SIGNAL_INFO(ctypes.Structure):
    _fields_ = [
        ("pixelRate", UINT64),
        ("hSyncFreq", DISPLAYCONFIG_RATIONAL),
        ("vSyncFreq", DISPLAYCONFIG_RATIONAL),
        ("activeSize", DISPLAYCONFIG_2DREGION),
        ("totalSize", DISPLAYCONFIG_2DREGION),
        ("videoStandard", UINT32),
        ("scanLineOrdering", UINT32),
    ]


class DISPLAYCONFIG_TARGET_MODE(ctypes.Structure):
    _fields_ = [
        ("targetVideoSignalInfo", DISPLAYCONFIG_VIDEO_SIGNAL_INFO),
    ]


class DISPLAYCONFIG_SOURCE_MODE(ctypes.Structure):
    _fields_ = [
        ("width", UINT32),
        ("height", UINT32),
        ("pixelFormat", UINT32),
        ("position", POINTL),
    ]


class DISPLAYCONFIG_DESKTOP_IMAGE_INFO(ctypes.Structure):
    _fields_ = [
        ("PathSourceSize", DISPLAYCONFIG_2DREGION),
        ("DesktopImageRegion", RECTL),
        ("DesktopImageClip", RECTL),
    ]


class DISPLAYCONFIG_MODE_INFO_UNION(ctypes.Union):
    _fields_ = [
        ("targetMode", DISPLAYCONFIG_TARGET_MODE),
        ("sourceMode", DISPLAYCONFIG_SOURCE_MODE),
        ("desktopImageInfo", DISPLAYCONFIG_DESKTOP_IMAGE_INFO),
    ]


class DISPLAYCONFIG_MODE_INFO(ctypes.Structure):
    _anonymous_ = ("mode",)

    _fields_ = [
        ("infoType", UINT32),
        ("id", UINT32),
        ("adapterId", LUID),
        ("mode", DISPLAYCONFIG_MODE_INFO_UNION),
    ]


class DISPLAYCONFIG_PATH_SOURCE_INFO_UNION(ctypes.Union):
    _fields_ = [
        ("modeInfoIdx", UINT32),
    ]


class DISPLAYCONFIG_PATH_SOURCE_INFO(ctypes.Structure):
    _anonymous_ = ("mode",)

    _fields_ = [
        ("adapterId", LUID),
        ("id", UINT32),
        ("mode", DISPLAYCONFIG_PATH_SOURCE_INFO_UNION),
        ("statusFlags", UINT32),
    ]


class DISPLAYCONFIG_PATH_TARGET_INFO_UNION(ctypes.Union):
    _fields_ = [
        ("modeInfoIdx", UINT32),
    ]


class DISPLAYCONFIG_PATH_TARGET_INFO(ctypes.Structure):
    _anonymous_ = ("mode",)

    _fields_ = [
        ("adapterId", LUID),
        ("id", UINT32),
        ("mode", DISPLAYCONFIG_PATH_TARGET_INFO_UNION),
        ("outputTechnology", UINT32),
        ("rotation", UINT32),
        ("scaling", UINT32),
        ("refreshRate", DISPLAYCONFIG_RATIONAL),
        ("scanLineOrdering", UINT32),
        ("targetAvailable", wintypes.BOOL),
        ("statusFlags", UINT32),
    ]


class DISPLAYCONFIG_PATH_INFO(ctypes.Structure):
    _fields_ = [
        ("sourceInfo", DISPLAYCONFIG_PATH_SOURCE_INFO),
        ("targetInfo", DISPLAYCONFIG_PATH_TARGET_INFO),
        ("flags", UINT32),
    ]


class DISPLAYCONFIG_DEVICE_INFO_HEADER(ctypes.Structure):
    _fields_ = [
        ("type", UINT32),
        ("size", UINT32),
        ("adapterId", LUID),
        ("id", UINT32),
    ]


class DISPLAYCONFIG_SOURCE_DEVICE_NAME(ctypes.Structure):
    _fields_ = [
        ("header", DISPLAYCONFIG_DEVICE_INFO_HEADER),
        ("viewGdiDeviceName", wintypes.WCHAR * 32),
    ]


class DISPLAYCONFIG_TARGET_DEVICE_NAME(ctypes.Structure):
    _fields_ = [
        ("header", DISPLAYCONFIG_DEVICE_INFO_HEADER),
        ("flags", UINT32),
        ("outputTechnology", UINT32),
        ("edidManufactureId", UINT16),
        ("edidProductCodeId", UINT16),
        ("connectorInstance", UINT32),
        ("monitorFriendlyDeviceName", wintypes.WCHAR * 64),
        ("monitorDevicePath", wintypes.WCHAR * 128),
    ]


assert ctypes.sizeof(LUID) == 8
assert ctypes.sizeof(DISPLAYCONFIG_PATH_SOURCE_INFO) == 20
assert ctypes.sizeof(DISPLAYCONFIG_PATH_TARGET_INFO) == 48
assert ctypes.sizeof(DISPLAYCONFIG_PATH_INFO) == 72
assert ctypes.sizeof(DISPLAYCONFIG_MODE_INFO) == 64
assert ctypes.sizeof(DISPLAYCONFIG_DEVICE_INFO_HEADER) == 20
assert ctypes.sizeof(DISPLAYCONFIG_SOURCE_DEVICE_NAME) == 84
assert ctypes.sizeof(DISPLAYCONFIG_TARGET_DEVICE_NAME) == 420
