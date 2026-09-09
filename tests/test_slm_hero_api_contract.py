"""Keep the standalone SLM client protocol aligned with the server HERO."""

from __future__ import annotations

import unittest
from importlib.util import module_from_spec, spec_from_file_location
from inspect import signature
from pathlib import Path
from typing import get_type_hints

from moretzslmcontrol.control.slm_hero_connector import SlmHeroConnector as ServerSlmHeroConnector


_CLIENT_TYPES_PATH = Path(__file__).parents[1] / "client" / "src" / "moretzslmclient" / "types.py"
_client_types_spec = spec_from_file_location("moretzslmclient_types_contract", _CLIENT_TYPES_PATH)
if _client_types_spec is None or _client_types_spec.loader is None:
    raise ImportError("Could not load the standalone client contract")
_client_types_module = module_from_spec(_client_types_spec)
_client_types_spec.loader.exec_module(_client_types_module)
ClientSlmHeroConnector = _client_types_module.SlmHeroConnector


class SlmHeroApiContractTest(unittest.TestCase):
    def test_client_protocol_methods_are_exposed_by_server_hero(self) -> None:
        client_methods = {
            name for name, value in vars(ClientSlmHeroConnector).items() if callable(value) and not name.startswith("_")
        }
        server_methods = {
            name for name, value in vars(ServerSlmHeroConnector).items() if callable(value) and not name.startswith("_")
        }

        self.assertTrue(client_methods <= server_methods)
        for name in client_methods:
            client_parameters = tuple(signature(getattr(ClientSlmHeroConnector, name)).parameters)
            server_parameters = tuple(signature(getattr(ServerSlmHeroConnector, name)).parameters)
            self.assertEqual(client_parameters, server_parameters, name)

    def test_named_pattern_inclusion_contract(self) -> None:
        self.assertEqual(
            get_type_hints(ClientSlmHeroConnector.getPatternInclusion)["return"],
            dict[str, bool],
        )
        self.assertEqual(
            get_type_hints(ServerSlmHeroConnector.getPatternInclusion)["return"],
            dict[str, bool],
        )
        self.assertEqual(
            get_type_hints(ClientSlmHeroConnector.getPatternSnapshots)["return"],
            get_type_hints(ServerSlmHeroConnector.getPatternSnapshots)["return"],
        )
