"""Validated, per-user UI preferences, independent of SLM output dimensions."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
import json
import logging
from math import isfinite
import os
from pathlib import Path
import shutil
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)


def ui_settings_path() -> Path:
    return Path.home() / ".config" / "moretzslmcontrol" / "settings.json"


@dataclass(frozen=True)
class UiSettings:
    global_scale: float = 1.0
    font_scale: float = 1.0
    element_scale: float = 1.0
    preview_scale: float = 1.0

    def __post_init__(self) -> None:
        for name, value in self.to_dict().items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or not 0.25 <= value <= 3:
                raise ValueError(f"UI {name} must be a finite factor between 0.25 and 3")

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, value: object) -> UiSettings:
        if not isinstance(value, Mapping):
            raise ValueError("UI settings must be an object")
        defaults = cls().to_dict()
        return cls(**{name: value.get(name, default) for name, default in defaults.items()})


def save_ui_settings(path: Path, settings: UiSettings) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            json.dump({"format_version": 1, "ui": settings.to_dict()}, temporary, indent=2, allow_nan=False)
            temporary.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def load_ui_settings(path: Path) -> UiSettings:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or data.get("format_version") != 1:
                raise ValueError("Unsupported UI settings format")
            return UiSettings.from_mapping(data["ui"])
        except (ValueError, KeyError) as error:
            backup = path.with_name(f"settings.invalid.{datetime.now():%Y%m%d-%H%M%S-%f}.json")
            shutil.copy2(path, backup)
            logger.warning("Invalid UI settings preserved at %s; using defaults: %s", backup, error)
    settings = UiSettings()
    save_ui_settings(path, settings)
    return settings
