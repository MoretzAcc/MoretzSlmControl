"""Report EDID input capability separately from optical SLM phase precision.

Depth mapping follows Linux DRM's EDID 1.4 digital-depth definitions.
"""
from __future__ import annotations


def edid_bits_per_channel(edid: bytes) -> int | None:
    if len(edid) < 128 or edid[:8] != b'\x00\xff\xff\xff\xff\xff\xff\x00' or sum(edid[:128]) % 256:
        return None
    if edid[18] != 1 or edid[19] < 4 or not edid[20] & 0x80:
        return None
    return {1: 6, 2: 8, 3: 10, 4: 12, 5: 14, 6: 16}.get((edid[20] >> 4) & 7)


def depth_summary(depths: list[int | None]) -> tuple[str, str]:
    known = sorted({depth for depth in depths if depth is not None})
    description = ', '.join(str(depth) for depth in known) + ' bits/channel (EDID)' if known else 'Unknown (EDID unspecified)'
    if any(depth > 8 for depth in known):
        warning = 'Warning: >8-bit monitor capability detected. Output is limited to 8-bit; higher phase precision is unsupported.'
    elif any(depth < 8 for depth in known):
        warning = 'Warning: monitor advertises less than 8 bits/channel. Verify grayscale precision.'
    else:
        warning = '8-bit software output; optical SLM precision and active link depth must be verified separately.'
    return description, warning
