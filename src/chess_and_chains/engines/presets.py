"""Data-driven bot presets and handshake-based UCI option negotiation.

Preset values are *requests* to an engine. Only options the engine actually
advertised in its UCI handshake, with values inside the advertised range, are
sent. No preset implies a measured Elo strength.
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import resources
from typing import Mapping

from .uci import UCIOption

OptionValue = int | bool | str


class PresetError(ValueError):
    """A bot preset definition is invalid."""


@dataclass(frozen=True, slots=True)
class BotPreset:
    id: str
    label_key: str
    movetime_ms: int
    skill_level: int | None = None
    limit_elo: int | None = None
    threads: int = 1
    hash_mb: int = 16
    extra_options: tuple[tuple[str, OptionValue], ...] = ()

    def __post_init__(self) -> None:
        if not self.id or not self.id.replace("-", "").isalnum():
            raise PresetError(f"Invalid preset id {self.id!r}.")
        for name in ("movetime_ms", "threads", "hash_mb"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise PresetError(f"{self.id}: {name} must be a positive integer.")
        if self.movetime_ms > 60_000:
            raise PresetError(f"{self.id}: movetime_ms above 60 s is not allowed.")
        for name in ("skill_level", "limit_elo"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                raise PresetError(f"{self.id}: {name} must be a non-negative integer or null.")


@dataclass(frozen=True, slots=True)
class OptionPlan:
    apply: tuple[tuple[str, OptionValue], ...]
    skipped: tuple[tuple[str, str], ...] = field(default=())


def load_presets(text: str | None = None) -> tuple[BotPreset, ...]:
    """Load and validate presets from JSON (bundled file when ``text`` is None)."""
    if text is None:
        text = resources.files(__package__).joinpath("bot_presets.json").read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise PresetError(f"Preset file is not valid JSON: {error}") from error
    if data.get("schema_version") != 1:
        raise PresetError("Unsupported preset schema version.")
    presets = []
    for raw in data.get("presets", []):
        if not isinstance(raw, dict):
            raise PresetError("Each preset must be an object.")
        known = {"id", "label_key", "movetime_ms", "skill_level", "limit_elo", "threads", "hash_mb", "extra_options"}
        unknown = set(raw) - known
        if unknown:
            raise PresetError(f"Unknown preset fields: {sorted(unknown)}")
        extra = tuple((str(k), v) for k, v in (raw.get("extra_options") or {}).items())
        presets.append(BotPreset(
            id=raw.get("id", ""),
            label_key=raw.get("label_key", ""),
            movetime_ms=raw.get("movetime_ms", 0),
            skill_level=raw.get("skill_level"),
            limit_elo=raw.get("limit_elo"),
            threads=raw.get("threads", 1),
            hash_mb=raw.get("hash_mb", 16),
            extra_options=extra,
        ))
    ids = [p.id for p in presets]
    if len(set(ids)) != len(ids):
        raise PresetError("Duplicate preset ids.")
    if len(presets) < 6:
        raise PresetError("At least six presets are required.")
    return tuple(presets)


def _check(option: UCIOption | None, name: str, value: OptionValue) -> str | None:
    """Return a skip reason, or None if ``value`` is acceptable for ``option``."""
    if option is None:
        return "not advertised by engine"
    if option.kind == "spin":
        if not isinstance(value, int) or isinstance(value, bool):
            return "requires integer"
        if (option.minimum is not None and value < option.minimum) or (
            option.maximum is not None and value > option.maximum
        ):
            return f"outside advertised range {option.minimum}..{option.maximum}"
        return None
    if option.kind == "check":
        return None if isinstance(value, bool) else "requires boolean"
    if option.kind == "combo":
        return None if isinstance(value, str) and value in option.choices else "not an advertised choice"
    if option.kind == "string":
        return None if isinstance(value, str) and "\n" not in value and "\r" not in value else "invalid string"
    return f"unsupported option kind {option.kind}"


def plan_options(preset: BotPreset, advertised: Mapping[str, UCIOption]) -> OptionPlan:
    """Map a preset onto the engine's advertised options; never guess unsupported ones."""
    wanted: list[tuple[str, OptionValue]] = [("Threads", preset.threads), ("Hash", preset.hash_mb)]
    if preset.limit_elo is not None:
        if "UCI_LimitStrength" in advertised and "UCI_Elo" in advertised:
            wanted += [("UCI_LimitStrength", True), ("UCI_Elo", preset.limit_elo)]
        else:
            wanted += [("UCI_Elo", preset.limit_elo)]
    if preset.skill_level is not None:
        wanted.append(("Skill Level", preset.skill_level))
    wanted += list(preset.extra_options)

    apply: list[tuple[str, OptionValue]] = []
    skipped: list[tuple[str, str]] = []
    for name, value in wanted:
        reason = _check(advertised.get(name), name, value)
        if reason is None:
            apply.append((name, value))
        else:
            skipped.append((name, reason))
    # UCI_Elo without a working UCI_LimitStrength switch has no defined effect.
    if ("UCI_LimitStrength", True) in apply and not any(n == "UCI_Elo" for n, _ in apply):
        apply.remove(("UCI_LimitStrength", True))
        skipped.append(("UCI_LimitStrength", "UCI_Elo value not applicable"))
    return OptionPlan(tuple(apply), tuple(skipped))
