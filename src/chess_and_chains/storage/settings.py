"""Validated, atomically written JSON user preferences."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime, timezone
from pathlib import Path

from glide_shell import window_geometry

SETTINGS_SCHEMA = 1
LOCALES = (None, "en", "de")
ORIENTATIONS = ("white", "black", "auto")
PLAY_MODES = ("human-vs-human", "human-vs-bot-white", "human-vs-bot-black")
BACKGROUND_CHOICES = (
    "default", "surface", "accent", "clear", "due_action",
    "export", "flag", "delete", "import", "muted",
)
ACCENT_CHOICES = (
    "accent", "clear", "due_action", "export",
    "flag", "delete", "import", "muted",
)
RADIUS_CHOICES = ("large", "standard", "subtle", "flat")
FONT_SCALE_CHOICES = ("compact", "standard", "large")
FONT_WEIGHT_CHOICES = ("auto", "standard", "bold")
BOARD_DESIGN_CHOICES = ("standard", "marble")
BOARD_PERSPECTIVES = ("2d", "3d")
PIECE_VIEWS = ("front", "top")
PIECE_SET_CHOICES = ("original", "top", "classic")
DEFAULT_PIECE_SET = "original"


class SettingsError(ValueError):
    """A settings value is invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    schema_version: int = SETTINGS_SCHEMA
    locale: str | None = None            # None = follow the operating system
    theme_id: str = "w06-provisional"
    piece_set_id: str = "geometric-test"
    board_orientation: str = "auto"
    board_design_choice: str = "standard"
    board_perspective: str = "2d"
    piece_view: str = "front"
    piece_set: str = "original"
    engine_path: str | None = None
    bot_preset_id: str = "level-3"
    play_mode: str = "human-vs-human"
    last_pack_id: str | None = None
    window_geometry: str | None = None
    compact_window: str | None = None
    sidebar_visible: bool = True
    sidebar_narrow: bool = False
    background_choice: str = "default"
    accent_choice: str = "accent"
    radius_choice: str = "standard"
    font_scale_choice: str = "standard"
    font_weight_choice: str = "standard"
    animations_enabled: bool = True
    hints_visible: bool = True

    def validate(self) -> Settings:
        if self.schema_version != SETTINGS_SCHEMA:
            raise SettingsError("Unsupported settings schema.")
        if self.locale not in LOCALES:
            raise SettingsError(f"Unsupported locale {self.locale!r}.")
        if self.board_orientation not in ORIENTATIONS:
            raise SettingsError(f"Unsupported orientation {self.board_orientation!r}.")
        if self.board_design_choice not in BOARD_DESIGN_CHOICES:
            raise SettingsError(f"Unsupported board design {self.board_design_choice!r}.")
        if self.board_perspective not in BOARD_PERSPECTIVES:
            raise SettingsError(f"Unsupported board perspective {self.board_perspective!r}.")
        if self.piece_view not in PIECE_VIEWS:
            raise SettingsError(f"Unsupported piece view {self.piece_view!r}.")
        if self.piece_set not in PIECE_SET_CHOICES:
            raise SettingsError(f"Unsupported piece set {self.piece_set!r}.")
        if self.play_mode not in PLAY_MODES:
            raise SettingsError(f"Unsupported play mode {self.play_mode!r}.")
        for name in ("theme_id", "piece_set_id", "bot_preset_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or len(value) > 64:
                raise SettingsError(f"Invalid {name}.")
        for name in ("sidebar_visible", "sidebar_narrow", "animations_enabled", "hints_visible"):
            if not isinstance(getattr(self, name), bool):
                raise SettingsError(f"Invalid {name}.")
        if self.background_choice not in BACKGROUND_CHOICES:
            raise SettingsError(f"Unsupported background choice {self.background_choice!r}.")
        if self.accent_choice not in ACCENT_CHOICES:
            raise SettingsError(f"Unsupported accent choice {self.accent_choice!r}.")
        if self.radius_choice not in RADIUS_CHOICES:
            raise SettingsError(f"Unsupported radius choice {self.radius_choice!r}.")
        if self.font_scale_choice not in FONT_SCALE_CHOICES:
            raise SettingsError(f"Unsupported font scale {self.font_scale_choice!r}.")
        if self.font_weight_choice not in FONT_WEIGHT_CHOICES:
            raise SettingsError(f"Unsupported font weight {self.font_weight_choice!r}.")
        if self.engine_path is not None and (not isinstance(self.engine_path, str) or "\n" in self.engine_path):
            raise SettingsError("Invalid engine path.")
        if self.window_geometry is not None and window_geometry.parse(self.window_geometry) is None:
            raise SettingsError("Invalid window geometry.")
        if self.compact_window is not None and window_geometry.parse(self.compact_window) is None:
            raise SettingsError("Invalid compact window geometry.")
        return self


def load_settings(path: Path) -> tuple[Settings, str | None]:
    """Return settings plus an optional warning. A broken file is quarantined, never deleted."""
    if not path.exists():
        return Settings(), None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise SettingsError("Settings root must be an object.")
        # Migration: populate piece_set from legacy piece_view if missing or invalid
        if "piece_set" not in raw:
            raw["piece_set"] = "top" if raw.get("piece_view") == "top" else "original"
        elif raw["piece_set"] not in PIECE_SET_CHOICES:
            raw["piece_set"] = "original"
        # Keep piece_view in sync for backward compatibility
        raw["piece_view"] = "top" if raw["piece_set"] == "top" else "front"
        known = {f.name for f in fields(Settings)}
        settings = Settings(**{k: v for k, v in raw.items() if k in known}).validate()
        return settings, None
    except (OSError, ValueError, TypeError) as error:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        quarantine = path.with_name(f"{path.name}.invalid-{stamp}")
        try:
            path.rename(quarantine)
        except OSError:
            quarantine = path
        return Settings(), f"Settings were invalid ({error}); defaults loaded, original kept at {quarantine.name}."


def save_settings(path: Path, settings: Settings) -> None:
    settings.validate()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(asdict(settings), indent=2, sort_keys=True).encode("utf-8")
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def update_settings(path: Path, **changes) -> Settings:
    current, _ = load_settings(path)
    updated = replace(current, **changes).validate()
    save_settings(path, updated)
    return updated
