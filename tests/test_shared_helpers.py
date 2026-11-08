from __future__ import annotations

import unittest
import subprocess
import sys
import numpy as np
from moretzslmclient.bit_map_util import byteToPhase, phaseToByte
from moretzslmclient.file_util import importNpyHologram
from moretzslmcontrol.util import bit_map_util, file_util


class SharedHelpersTest(unittest.TestCase):
    def test_all_gray_levels_roundtrip_with_float32_and_shared_implementation(self) -> None:
        values = np.arange(256, dtype=np.uint8).reshape(16, 16)
        phase = byteToPhase(values)
        self.assertEqual(phase.dtype, np.float32)
        np.testing.assert_array_equal(phaseToByte(phase), values)
        self.assertIs(bit_map_util.phaseToByte, phaseToByte)
        self.assertIs(file_util.importNpyHologram, importNpyHologram)

    def test_importing_helpers_does_not_open_a_persistent_network_session(self) -> None:
        result = subprocess.run([sys.executable, '-c',
            'import sys; import moretzslmclient; assert "PySide6" not in sys.modules; assert "moretzslmcontrol" not in sys.modules'],
            capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
