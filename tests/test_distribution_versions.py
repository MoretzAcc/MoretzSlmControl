"""Keep the server and standalone client distribution versions in sync."""

from __future__ import annotations

from pathlib import Path
import tomllib
import unittest


_REPOSITORY_ROOT = Path(__file__).parents[1]
_VERSION_FILE = _REPOSITORY_ROOT / "VERSION"


def _distribution_version(pyproject_path: Path) -> str:
    with pyproject_path.open("rb") as pyproject_file:
        metadata = tomllib.load(pyproject_file)
    return metadata["project"]["version"]


class DistributionVersionTest(unittest.TestCase):
    def test_distribution_versions_match_the_repository_version(self) -> None:
        server_version = _distribution_version(_REPOSITORY_ROOT / "pyproject.toml")
        client_version = _distribution_version(_REPOSITORY_ROOT / "client" / "pyproject.toml")
        repository_version = _VERSION_FILE.read_text(encoding="utf-8").strip()

        self.assertTrue(repository_version, "VERSION must not be empty.")
        self.assertEqual(server_version, repository_version, "Run dev/sync_version.py after changing VERSION.")
        self.assertEqual(client_version, repository_version, "Run dev/sync_version.py after changing VERSION.")
