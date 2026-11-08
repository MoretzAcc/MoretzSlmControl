from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from moretzslmclient.discover_heros import discover_slm_heros


class DiscoverHerosTest(unittest.TestCase):
    def test_discovery_returns_only_slm_connectors_and_closes_observer(self) -> None:
        observer = Mock()
        observer.known_objects = {
            'slm-a': {'name': 'slm-a', 'class': 'SlmHeroConnector'},
            'other': {'name': 'other', 'class': 'OtherConnector'},
        }
        observer.__enter__ = Mock(return_value=observer)
        observer.__exit__ = Mock(return_value=False)
        with patch('moretzslmclient.discover_heros.HEROObserver', return_value=observer) as factory:
            self.assertEqual(discover_slm_heros(), ['slm-a'])
        factory.assert_called_once_with()
        observer.__enter__.assert_called_once_with()
        observer.__exit__.assert_called_once_with(None, None, None)
