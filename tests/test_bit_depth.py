from __future__ import annotations

import unittest
from moretzslmcontrol.monitor_stuff.bit_depth import edid_bits_per_channel, depth_summary


def edid(depth_code: int, revision: int = 4, digital: bool = True) -> bytes:
    block = bytearray(128)
    block[:8] = b'\x00\xff\xff\xff\xff\xff\xff\x00'
    block[18:21] = bytes((1, revision, (0x80 if digital else 0) | depth_code << 4))
    block[127] = -sum(block) % 256
    return bytes(block)


class BitDepthTest(unittest.TestCase):
    def test_valid_digital_depths_and_unknown_encodings(self) -> None:
        for code, expected in enumerate((None, 6, 8, 10, 12, 14, 16, None)):
            self.assertEqual(edid_bits_per_channel(edid(code)), expected)
        self.assertIsNone(edid_bits_per_channel(edid(3, revision=3)))
        self.assertIsNone(edid_bits_per_channel(edid(3, digital=False)))
        self.assertIsNone(edid_bits_per_channel(b''))
        self.assertIsNone(edid_bits_per_channel(edid(3)[:-1]+b'\x01'))

    def test_warning_distinguishes_capability_from_precision(self) -> None:
        self.assertIn('Unknown', depth_summary([])[0])
        self.assertIn('>8-bit', depth_summary([8, 10])[1])
        self.assertIn('optical', depth_summary([8])[1])
