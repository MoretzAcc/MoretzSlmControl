"""Keep the server and standalone client distribution versions in sync."""

from __future__ import annotations

from pathlib import Path
import tomllib
import unittest


_REPOSITORY_ROOT = Path(__file__).parents[1]


def _distribution_version(pyproject_path: Path) -> str:
    with pyproject_path.open("rb") as pyproject_file:
        metadata = tomllib.load(pyproject_file)
    return metadata["project"]["version"]


class DistributionVersionTest(unittest.TestCase):
    def test_server_and_client_versions_match(self) -> None:
        server_version = _distribution_version(_REPOSITORY_ROOT / "pyproject.toml")
        client_version = _distribution_version(_REPOSITORY_ROOT / "client" / "pyproject.toml")

        self.assertEqual(
            server_version,
            client_version,
            "Update the server and standalone client package versions together.",
        )
