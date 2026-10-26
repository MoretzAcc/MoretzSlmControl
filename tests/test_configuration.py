from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from moretzslmcontrol.util.config_file import (
    FORMAT_NAME,
    FORMAT_VERSION,
    decode_pattern,
    encode_pattern,
    load_configuration,
    save_configuration,
)


class ConfigurationFileTest(unittest.TestCase):
    def test_pattern_round_trip_preserves_float32_data(self) -> None:
        pattern = np.array([[0.0, 1.25], [-2.5, np.pi]], dtype=np.float32)

        decoded = decode_pattern(encode_pattern(pattern))

        self.assertEqual(decoded.dtype, np.float32)
        np.testing.assert_array_equal(decoded, pattern)

    def test_load_configuration_rejects_invalid_pattern_dimensions(self) -> None:
        configuration = {
            "format": FORMAT_NAME,
            "format_version": FORMAT_VERSION,
            "slm": {"width": 0, "height": 1080},
            "controls": {},
            "patterns": {},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            save_configuration(path, configuration)

            with self.assertRaisesRegex(ValueError, "width"):
                load_configuration(path)
if __name__ == "__main__":
    unittest.main()
