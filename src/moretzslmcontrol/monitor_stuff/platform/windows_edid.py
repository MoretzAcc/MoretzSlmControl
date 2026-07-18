"""
Author: Moritz van Eimern
Date: 18.07.2026
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    ...

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WindowsMonitor:
    instance_name: str  # Name as shown by Windows. Nice for debugging, but as I did not find an equivalent in linux, I won't use it.
    edid: bytes  # EDID-Bytes
    complete: bool  # True, if all blocks were read successfully


def request_windows_edids() -> list[WindowsMonitor]:
    if sys.platform != "win32":
        raise OSError("This function only works on Windows.")

    import pywintypes
    import win32com.client

    locator = win32com.client.Dispatch("WbemScripting.SWbemLocator")
    service = locator.ConnectServer(".", r"root\wmi")

    query_result = service.ExecQuery(
        "SELECT * FROM WmiMonitorDescriptorMethods WHERE Active = TRUE"
    )

    monitors: list[WindowsMonitor] = []

    for monitor in query_result:
        instance_name = str(monitor.InstanceName)

        try:
            base_block = _read_edid_block(service, monitor, 0)
            _validate_edid_block(base_block, 0)
        except (pywintypes.com_error, RuntimeError, ValueError) as error:
            logger.exception(f"{instance_name}: Unable to read Base Block: {error}")
            continue

        if len(base_block) != 128:
            logger.error(f"{instance_name}: Invalid Base Block length: {len(base_block)} Bytes")
            continue

        extension_count = base_block[126]
        blocks = [base_block]
        complete = True

        for block_id in range(1, extension_count + 1):
            try:
                block = _read_edid_block(service, monitor, block_id)
                _validate_edid_block(block, block_id)
            except (pywintypes.com_error, RuntimeError, ValueError) as error:
                logger.exception(f"{instance_name}: Unable to read Block {block_id}: {error}")
                complete = False
                break

            if len(block) != 128:
                logger.error(
                    f"{instance_name}: Invalid Block length for Block {block_id}: "
                    f"{len(base_block)} Bytes"
                )
                complete = False
                break

            blocks.append(block)

        monitors.append(
            WindowsMonitor(instance_name=instance_name, edid=b"".join(blocks), complete=complete)
        )

    return monitors


def _read_edid_block(
    service: Any,  # noqa: ANN401
    monitor: Any,  # noqa: ANN401
    block_id: int,
) -> bytes:
    method_name = "WmiGetMonitorRawEEdidV1Block"

    method = monitor.Methods_(method_name)
    in_parameters = method.InParameters.SpawnInstance_()
    in_parameters.Properties_.Item("BlockId").Value = block_id

    out_parameters = service.ExecMethod(
        monitor.Path_.Path,
        method_name,
        in_parameters,
    )

    properties = {str(prop.Name): prop.Value for prop in out_parameters.Properties_}

    # I am not sure if the type is 100% accurate.
    return_value: int | None = properties.get("ReturnValue")

    if return_value is not None and int(return_value) != 0:
        raise RuntimeError(f"{method_name} returned {int(return_value)} which is not 0")

    if "BlockContent" not in properties:
        available = ", ".join(sorted(properties)) or "<none>"

        raise RuntimeError(
            f"{method_name} did not return BlockContent. Available Output-Properties: {available}"
        )

    content = properties["BlockContent"]

    if content is None:
        raise RuntimeError(f"{method_name} did not return any content for Block {block_id}.")

    try:
        return bytes(content)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"Could not convert BlockContent of Block {block_id} into bytes:"
            f"{type(content).__name__}"
        ) from error


EDID_HEADER = b"\x00\xff\xff\xff\xff\xff\xff\x00"


def _validate_edid_block(block: bytes, block_id: int) -> None:
    if len(block) != 128:
        raise ValueError(f"EDID-Block {block_id} has {len(block)} Bytes. Expected 128 Bytes.")

    if block_id == 0 and not block.startswith(EDID_HEADER):
        raise ValueError("EDID Base Block has an invalid header.")

    if sum(block) & 0xFF:
        logger.warning(f"EDID Block {block_id} has an invalid Checksum.")
