from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np
from moretzslmcontrol.hologram_manager import HologramManager
from moretzslmcontrol.util.config_file import FORMAT_NAME, load_configuration, save_configuration


class HerosToggleTest(unittest.TestCase):
    def test_disabling_external_control_preserves_patterns_and_frames(self) -> None:
        with patch('moretzslmcontrol.hologram_manager.SlmHeroConnector') as connector:
            manager = HologramManager(4, 4, 'test', 'test', Mock(), Mock(), heros_enabled=False)
            connector.assert_not_called()
            manager.setHologramPattern(np.ones((4, 4), dtype=np.float32))
            frame = manager.getLastFrameSnapshot()[1]
            manager.setHeroEnabled(True)
            manager.setHeroEnabled(True)
            connector.assert_called_once()
            manager.setHeroEnabled(False)
            connector.return_value.close.assert_called_once()
            self.assertFalse(manager.isHeroEnabled())
            np.testing.assert_array_equal(manager.getLastFrameSnapshot()[1], frame)
            manager.setHeroEnabled(True)
            self.assertEqual(connector.call_count, 2)
            manager.close()

    def test_configuration_accepts_legacy_and_current_connection_settings(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'config.json'
            for version in (1, 2):
                configuration = {'format': FORMAT_NAME, 'format_version': version,
                                 'slm': {'width': 4, 'height': 4}, 'controls': {}, 'patterns': {}}
                if version == 2:
                    configuration['controls']['connections'] = {'heros': False}
                save_configuration(path, configuration)
                self.assertEqual(load_configuration(path), configuration)
