"""Versioned offline puzzle packs: ``puzzles.jsonl`` + ``manifest.json``.

Packs are read-only catalogue data and are kept separate from user progress
(SQLite, see ``storage``), raw source files and import reports.
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Iterable

from ..chess import ChessGame, ChessRules
from .importer import ImportReport
from .model import MIN_PUBLISHED_RATING, Puzzle, ValidationStatus

PACK_SCHEMA = 1
DEMO_PACK_ID = "demo"
_MANIFEST_LIMIT = 64 * 1024
_PACK_LIMIT = 64 * 1024 * 1024
_PACK_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
_SURROGATE = re.compile(r"[\ud800-\udfff]")


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


def _valid_text(value: object) -> bool:
    return isinstance(value, str) and _SURROGATE.search(value) is None


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
    if not _PACK_ID.fullmatch(pack_id):
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
    except (json.JSONDecodeError, RecursionError) as error:
        raise PackError(f"Pack manifest is not JSON: {error}") from error
    if not isinstance(raw, dict) or type(raw.get("schema")) is not int or raw["schema"] != PACK_SCHEMA:
        raise PackError("Unsupported pack schema.")
    try:
        manifest = PackManifest(**{k: raw[k] for k in PackManifest.__slots__ if k in raw})
    except TypeError as error:
        raise PackError(f"Incomplete pack manifest: {error}") from error
    if not isinstance(manifest.pack_id, str) or not _PACK_ID.fullmatch(manifest.pack_id):
        raise PackError("Invalid pack id in the manifest.")
    if not all(map(_valid_text, (manifest.version, manifest.source, manifest.license_note, manifest.created_utc))):
        raise PackError("Invalid text metadata in the pack manifest.")
    if type(manifest.count) is not int or type(manifest.min_rating) is not int or type(manifest.demo) is not bool:
        raise PackError("Invalid count, minimum rating or demo flag in the pack manifest.")
    if hashlib.sha256(body).hexdigest() != manifest.sha256:
        raise PackError("Pack checksum mismatch; the pack is corrupt or modified.")
    rules = ChessRules()
    puzzles = []
    seen: set[str] = set()
    validation = ValidationStatus.VALID if revalidate else ValidationStatus.UNVALIDATED
    for line_no, line in enumerate(io.BytesIO(body), 1):
        try:
            record = json.loads(line.decode("utf-8"))
            if not isinstance(record, dict) or not _valid_text(record.get("id")) or not record["id"].strip():
                raise PackError("Expected a puzzle with a non-empty text id.")
            moves, themes = record.get("moves"), record.get("themes", [])
            if not isinstance(moves, list) or any(not isinstance(move, str) for move in moves):
                raise PackError("Expected a list of UCI moves.")
            if not isinstance(themes, list) or not all(map(_valid_text, themes)):
                raise PackError("Expected a list of theme identifiers.")
            if type(record.get("rating")) is not int:
                raise PackError("Expected an integer puzzle rating.")
            puzzle = Puzzle.from_record(record, validation)
            if not puzzle.solution or len(puzzle.solution) % 2 == 0:
                raise PackError("The solution must end with a player move.")
            if revalidate:
                game = ChessGame(puzzle.initial_state(), rules=rules, adjudicate_forced_capture_draws=False)
                for move in (puzzle.setup_move, *puzzle.solution):
                    game.play(move)
        except (IndexError, KeyError, TypeError, ValueError, RecursionError) as error:
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


def _read_pack_data(directory: Path) -> tuple[bytes, bytes]:
    try:
        with (directory / "manifest.json").open("rb") as file:
            manifest = file.read(_MANIFEST_LIMIT + 1)
        with (directory / "puzzles.jsonl").open("rb") as file:
            body = file.read(_PACK_LIMIT + 1)
    except OSError as error:
        raise PackError(f"Cannot read pack in {directory}: {error}") from error
    if len(manifest) > _MANIFEST_LIMIT or len(body) > _PACK_LIMIT:
        raise PackError("Puzzle pack exceeds the file size limit.")
    return manifest, body


def _decode_manifest(manifest: bytes) -> str:
    try:
        return manifest.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PackError("Pack manifest must be UTF-8.") from error


def read_pack(directory: Path, *, revalidate: bool = True) -> PuzzlePack:
    manifest, body = _read_pack_data(directory)
    return _parse_pack(_decode_manifest(manifest), body, revalidate)


def load_demo_pack() -> PuzzlePack:
    """The bundled demo pack: project-authored positions, not Lichess data."""
    data = resources.files(__package__).joinpath("data", DEMO_PACK_ID)
    return _parse_pack(
        data.joinpath("manifest.json").read_text(encoding="utf-8"),
        data.joinpath("puzzles.jsonl").read_bytes(),
        revalidate=True,
    )


class PackLibrary:
    """Read-only puzzle contents installed under their manifest id in user data."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory.absolute()

    def _location(self, pack_id: str) -> Path:
        if not isinstance(pack_id, str) or pack_id == DEMO_PACK_ID or not _PACK_ID.fullmatch(pack_id):
            raise PackError(f"Invalid or reserved local pack id: {pack_id!r}.")
        path = self.directory / pack_id
        try:
            resolved = path.resolve()
        except (OSError, RuntimeError) as error:
            raise PackError(f"Cannot resolve the local puzzle pack folder: {error}") from error
        if resolved != path:
            raise PackError("Local puzzle pack paths must not be redirected.")
        return path

    def ids(self) -> tuple[str, ...]:
        try:
            return tuple(sorted(path.name for path in self.directory.iterdir()
                                if path.name != DEMO_PACK_ID and _PACK_ID.fullmatch(path.name)
                                and path.is_dir() and not path.is_symlink()))
        except FileNotFoundError:
            return ()
        except OSError as error:
            raise PackError(f"Cannot list local puzzle packs: {error}") from error

    def load(self, pack_id: str) -> PuzzlePack:
        pack = read_pack(self._location(pack_id))
        if pack.manifest.pack_id != pack_id:
            raise PackError("Pack id does not match its local folder.")
        if not pack.puzzles:
            raise PackError("A local puzzle pack must contain at least one puzzle.")
        return pack

    def install(self, source: Path) -> PuzzlePack:
        manifest, body = _read_pack_data(source)
        pack = _parse_pack(_decode_manifest(manifest), body, revalidate=True)
        target = self._location(pack.manifest.pack_id)
        if not pack.puzzles:
            raise PackError("A local puzzle pack must contain at least one puzzle.")
        if target.exists():
            raise PackError(f"Puzzle pack '{pack.manifest.pack_id}' is already installed.")
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=".incoming-", dir=self.directory) as staging:
                payload = Path(staging) / "pack"
                _atomic_write(payload / "puzzles.jsonl", body)
                _atomic_write(payload / "manifest.json", manifest)
                payload.rename(target)
        except OSError as error:
            raise PackError(f"Cannot install puzzle pack '{pack.manifest.pack_id}': {error}") from error
        return pack
