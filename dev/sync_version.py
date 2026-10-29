"""Synchronize distribution metadata from the repository version file."""

from __future__ import annotations

from pathlib import Path
import re


REPOSITORY_ROOT = Path(__file__).parents[1]
VERSION_FILE = REPOSITORY_ROOT / "VERSION"
PYPROJECT_FILES = (REPOSITORY_ROOT / "pyproject.toml", REPOSITORY_ROOT / "client" / "pyproject.toml")
VERSION_LINE = re.compile(r'^(version\s*=\s*)"[^"]*"$', flags=re.MULTILINE)


def main() -> None:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not version or any(character.isspace() for character in version):
        raise ValueError("VERSION must contain one non-empty version string")

    for pyproject_file in PYPROJECT_FILES:
        original = pyproject_file.read_text(encoding="utf-8")
        updated, replacements = VERSION_LINE.subn(rf'\g<1>"{version}"', original, count=1)
        if replacements != 1:
            raise ValueError(f"Could not find one project version in {pyproject_file}")
        pyproject_file.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
