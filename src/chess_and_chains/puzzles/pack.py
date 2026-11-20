"""Versioned offline puzzle packs: ``puzzles.jsonl`` + ``manifest.json``.

Packs are read-only catalogue data and are kept separate from user progress
(SQLite, see ``storage``), raw source files and import reports.
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Iterable

from ..chess import ChessRules
from .importer import ImportReport
from .model import MIN_PUBLISHED_RATING, Puzzle, ValidationStatus

PACK_SCHEMA = 1
_PACK_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")


class PackError(ValueError):
    """A puzzle pack is missing, corrupt, or violates the pack contract."""


@dataclass(frozen=True, slots=True)
class PackManifest:
    pack_id: str
    version: str
    count: int
    sha256: str
    min_rating: int
    source: str
    license_note: str
    created_utc: str
    demo: bool = False

    def to_dict(self) -> dict:
        return {"schema": PACK_SCHEMA, **{k: getattr(self, k) for k in self.__slots__}}


@dataclass(frozen=True, slots=True)
class PuzzlePack:
    manifest: PackManifest
    puzzles: tuple[Puzzle, ...]


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def write_pack(
    directory: Path,
    puzzles: Iterable[Puzzle],
    *,
    pack_id: str,
    version: str,
    source: str,
    license_note: str,
    report: ImportReport | None = None,
    demo: bool = False,
) -> PackManifest:
    if not _PACK_ID.match(pack_id):
        raise PackError(f"Invalid pack id {pack_id!r}.")
    items = list(puzzles)
    if any(p.rating < MIN_PUBLISHED_RATING for p in items):
        raise PackError(f"Packs may only contain puzzles with Rating >= {MIN_PUBLISHED_RATING}.")
    if any(p.validation is not ValidationStatus.VALID for p in items):
        raise PackError("Packs may only contain validated puzzles.")
    ids = [p.puzzle_id for p in items]
    if len(set(ids)) != len(ids):
        raise PackError("Duplicate puzzle ids in pack.")
    body = "".join(json.dumps(p.to_record(), sort_keys=True, ensure_ascii=False) + "\n" for p in items).encode()
    manifest = PackManifest(
        pack_id=pack_id,
        version=version,
        count=len(items),
        sha256=hashlib.sha256(body).hexdigest(),
        min_rating=min((p.rating for p in items), default=MIN_PUBLISHED_RATING),
        source=source,
        license_note=license_note,
        created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        demo=demo,
    )
    _atomic_write(directory / "puzzles.jsonl", body)
    if report is not None:
        _atomic_write(directory / "import_report.json", json.dumps(report.to_dict(), indent=2).encode())
    _atomic_write(directory / "manifest.json", json.dumps(manifest.to_dict(), indent=2).encode())
    return manifest


def _parse_pack(manifest_text: str, body: bytes, revalidate: bool) -> PuzzlePack:
    try:
        raw = json.loads(manifest_text)
    except json.JSONDecodeError as error:
        raise PackError(f"Pack manifest is not JSON: {error}") from error
    if not isinstance(raw, dict) or raw.get("schema") != PACK_SCHEMA:
        raise PackError("Unsupported pack schema.")
    try:
        manifest = PackManifest(**{k: raw[k] for k in PackManifest.__slots__ if k in raw})
    except TypeError as error:
        raise PackError(f"Incomplete pack manifest: {error}") from error
    if hashlib.sha256(body).hexdigest() != manifest.sha256:
        raise PackError("Pack checksum mismatch; the pack is corrupt or modified.")
    rules = ChessRules()
    puzzles = []
    seen: set[str] = set()
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PackError("Pack body must be UTF-8.") from error
    validation = ValidationStatus.VALID if revalidate else ValidationStatus.UNVALIDATED
    for line_no, line in enumerate(text.splitlines(), 1):
        try:
            puzzle = Puzzle.from_record(json.loads(line), validation)
            if not puzzle.solution or len(puzzle.solution) % 2 == 0:
                raise PackError("The solution must end with a player move.")
            if revalidate:
                state = puzzle.initial_state()
                for move in (puzzle.setup_move, *puzzle.solution):
                    state = rules.apply(state, move)
        except (IndexError, KeyError, TypeError, ValueError) as error:
            raise PackError(f"Pack line {line_no} is invalid: {error}") from error
        if puzzle.rating < MIN_PUBLISHED_RATING:
            raise PackError(f"Puzzle {puzzle.puzzle_id} is below the rating minimum.")
        if puzzle.puzzle_id in seen:
            raise PackError(f"Duplicate puzzle id {puzzle.puzzle_id}.")
        seen.add(puzzle.puzzle_id)
        puzzles.append(puzzle)
    if len(puzzles) != manifest.count:
        raise PackError("Pack count does not match its manifest.")
    if min((puzzle.rating for puzzle in puzzles), default=MIN_PUBLISHED_RATING) != manifest.min_rating:
        raise PackError("Pack minimum rating does not match its manifest.")
    return PuzzlePack(manifest, tuple(puzzles))


def read_pack(directory: Path, *, revalidate: bool = True) -> PuzzlePack:
    try:
        manifest_text = (directory / "manifest.json").read_text(encoding="utf-8")
        body = (directory / "puzzles.jsonl").read_bytes()
    except (OSError, UnicodeDecodeError) as error:
        raise PackError(f"Cannot read pack in {directory}: {error}") from error
    return _parse_pack(manifest_text, body, revalidate)


def load_demo_pack() -> PuzzlePack:
    """The bundled demo pack: project-authored positions, not Lichess data."""
    data = resources.files(__package__).joinpath("data", "demo")
    return _parse_pack(
        data.joinpath("manifest.json").read_text(encoding="utf-8"),
        data.joinpath("puzzles.jsonl").read_bytes(),
        revalidate=True,
    )
