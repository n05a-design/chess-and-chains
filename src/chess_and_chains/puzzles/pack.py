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
import sqlite3
import tempfile
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, Iterable

from ..chess import ChessRules, to_fen
from .importer import MAX_SOLUTION_PLIES, ImportReport
from .model import MIN_PUBLISHED_RATING, Puzzle, ValidationStatus, validate_solution_line

if TYPE_CHECKING:
    from .catalog import IndexedPuzzlePack

PACK_SCHEMA = 1
DEMO_PACK_ID = "demo"
_MANIFEST_LIMIT = 64 * 1024
_PACK_LIMIT = 64 * 1024 * 1024
_RECORD_LIMIT = 64 * 1024
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


    def incompatible_puzzle_ids(self, newer: PuzzlePack) -> tuple[str, ...]:
        """Identify puzzle IDs whose saved progress cannot be carried forward."""
        if newer.manifest.pack_id != self.manifest.pack_id:
            raise PackError("Pack revisions must share the same pack id.")
        next_by_id = {puzzle.puzzle_id: puzzle for puzzle in newer.puzzles}
        incompatible = []
        for previous in self.puzzles:
            replacement = next_by_id.get(previous.puzzle_id)
            if replacement is None:
                # A removed ID could later be reused while its attempts still exist.
                incompatible.append(previous.puzzle_id)
            elif (
                previous.setup_move != replacement.setup_move
                or previous.solution != replacement.solution
                or (previous.fen != replacement.fen
                    and to_fen(previous.initial_state()) != to_fen(replacement.initial_state()))
            ):
                incompatible.append(previous.puzzle_id)
        return tuple(sorted(incompatible))


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
    if not all(map(_valid_text, (version, source, license_note))):
        raise PackError("Invalid text metadata in the pack manifest.")
    directory.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    count = size = 0
    min_rating = None
    ids: set[str] = set()
    with tempfile.TemporaryDirectory(prefix=".build-", dir=directory) as staging:
        payload = Path(staging) / "puzzles.jsonl"
        with payload.open("wb") as handle:
            for puzzle in puzzles:
                if puzzle.rating < MIN_PUBLISHED_RATING:
                    raise PackError(f"Packs may only contain puzzles with Rating >= {MIN_PUBLISHED_RATING}.")
                if puzzle.validation is not ValidationStatus.VALID:
                    raise PackError("Packs may only contain validated puzzles.")
                if puzzle.puzzle_id in ids:
                    raise PackError("Duplicate puzzle ids in pack.")
                ids.add(puzzle.puzzle_id)
                record = (json.dumps(puzzle.to_record(), sort_keys=True, ensure_ascii=False) + "\n").encode()
                size += len(record)
                if len(record) > _RECORD_LIMIT or size > _PACK_LIMIT:
                    raise PackError("Puzzle pack exceeds the file size limit.")
                handle.write(record)
                digest.update(record)
                count += 1
                min_rating = puzzle.rating if min_rating is None else min(min_rating, puzzle.rating)
            handle.flush()
            os.fsync(handle.fileno())
        manifest = PackManifest(
            pack_id=pack_id,
            version=version,
            count=count,
            sha256=digest.hexdigest(),
            min_rating=min_rating if min_rating is not None else MIN_PUBLISHED_RATING,
            source=source,
            license_note=license_note,
            created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            demo=demo,
        )
        manifest_data = json.dumps(manifest.to_dict(), indent=2).encode()
        report_data = json.dumps(report.to_dict(), indent=2).encode() if report is not None else None
        if len(manifest_data) > _MANIFEST_LIMIT:
            raise PackError("Puzzle pack exceeds the manifest size limit.")
        payload.replace(directory / payload.name)
        if report_data is not None:
            _atomic_write(directory / "import_report.json", report_data)
        _atomic_write(directory / "manifest.json", manifest_data)
    return manifest


def _parse_pack(manifest_text: str, body: BinaryIO, revalidate: bool) -> PuzzlePack:
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
    if (
        type(manifest.count) is not int or manifest.count < 0
        or type(manifest.min_rating) is not int or manifest.min_rating < MIN_PUBLISHED_RATING
        or type(manifest.demo) is not bool
    ):
        raise PackError("Invalid count, minimum rating or demo flag in the pack manifest.")
    digest = hashlib.sha256()
    size = 0
    rules = ChessRules()
    puzzles = []
    seen: set[str] = set()
    validation = ValidationStatus.VALID if revalidate else ValidationStatus.UNVALIDATED
    for line_no, line in enumerate(iter(lambda: body.readline(_RECORD_LIMIT + 1), b""), 1):
        size += len(line)
        if size > _PACK_LIMIT or len(line) > _RECORD_LIMIT:
            raise PackError("Puzzle pack exceeds the file size limit.")
        digest.update(line)
        try:
            record = json.loads(line.decode("utf-8"))
            if not isinstance(record, dict) or not _valid_text(record.get("id")) or not record["id"].strip():
                raise PackError("Expected a puzzle with a non-empty text id.")
            moves, themes = record.get("moves"), record.get("themes", [])
            if not isinstance(moves, list) or not 2 <= len(moves) <= MAX_SOLUTION_PLIES:
                raise PackError("Unexpected number of moves in the solution.")
            if not all(map(_valid_text, moves)):
                raise PackError("Expected a list of UCI moves.")
            if not isinstance(themes, list) or not all(map(_valid_text, themes)):
                raise PackError("Expected a list of theme identifiers.")
            opening_tags = record.get("opening_tags", [])
            if not isinstance(opening_tags, list) or not all(map(_valid_text, opening_tags)):
                raise PackError("Expected a list of opening tags.")
            for name in ("fen", "source", "game_url"):
                if not _valid_text(record.get(name, "")) or (name == "fen" and not record.get(name)):
                    raise PackError(f"Expected text for {name}.")
            if type(record.get("rating")) is not int:
                raise PackError("Expected an integer puzzle rating.")
            for name, minimum, maximum in (
                ("rating_deviation", 0, None), ("plays", 0, None), ("popularity", -100, 100),
            ):
                value = record.get(name, 0)
                if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
                    raise PackError(f"Invalid value for {name}.")
            puzzle = Puzzle.from_record(record, validation)
            if not puzzle.solution or len(puzzle.solution) % 2 == 0:
                raise PackError("The solution must end with a player move.")
            if revalidate:
                validate_solution_line(puzzle.initial_state(), (puzzle.setup_move, *puzzle.solution), rules)
        except (IndexError, KeyError, TypeError, ValueError, RecursionError) as error:
            raise PackError(f"Pack line {line_no} is invalid: {error}") from error
        if puzzle.rating < MIN_PUBLISHED_RATING:
            raise PackError(f"Puzzle {puzzle.puzzle_id} is below the rating minimum.")
        if puzzle.puzzle_id in seen:
            raise PackError(f"Duplicate puzzle id {puzzle.puzzle_id}.")
        seen.add(puzzle.puzzle_id)
        puzzles.append(puzzle)
    if digest.hexdigest() != manifest.sha256:
        raise PackError("Pack checksum mismatch; the pack is corrupt or modified.")
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
    try:
        with (directory / "manifest.json").open("rb") as file:
            manifest = file.read(_MANIFEST_LIMIT + 1)
        if len(manifest) > _MANIFEST_LIMIT:
            raise PackError("Puzzle pack exceeds the manifest size limit.")
        with (directory / "puzzles.jsonl").open("rb") as body:
            return _parse_pack(_decode_manifest(manifest), body, revalidate)
    except OSError as error:
        raise PackError(f"Cannot read pack in {directory}: {error}") from error


def load_demo_pack() -> PuzzlePack:
    """The bundled demo pack: project-authored positions, not Lichess data."""
    data = resources.files(__package__).joinpath("data", DEMO_PACK_ID)
    return _parse_pack(
        data.joinpath("manifest.json").read_text(encoding="utf-8"),
        io.BytesIO(data.joinpath("puzzles.jsonl").read_bytes()),
        revalidate=True,
    )


class PackLibrary:
    """Read-only puzzle contents installed under their manifest id in user data."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory.absolute()

    def _location(self, pack_id: str) -> Path:
        if not isinstance(pack_id, str) or pack_id == DEMO_PACK_ID or not _PACK_ID.fullmatch(pack_id):
            raise PackError(f"Invalid or reserved local pack id: {pack_id!r}.")
        try:
            # The data root can have an OS-provided alias (e.g. macOS temporary paths).
            path = self.directory.parent.resolve() / self.directory.name / pack_id
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
        pack = read_pack(self._catalog_paths(pack_id)[0])
        if pack.manifest.pack_id != pack_id:
            raise PackError("Pack id does not match its local folder.")
        if not pack.puzzles:
            raise PackError("A local puzzle pack must contain at least one puzzle.")
        return pack

    def open_catalog(self, pack_id: str) -> IndexedPuzzlePack:
        return self._open_catalog(pack_id)

    def install_catalog(self, source: Path) -> IndexedPuzzlePack:
        pack = self.install(source)
        return self._open_catalog(pack.manifest.pack_id, validated=pack)

    def _open_catalog(self, pack_id: str, *, validated: PuzzlePack | None = None) -> IndexedPuzzlePack:
        from .catalog import PuzzleCatalog

        source, cache = self._catalog_paths(pack_id)
        return PuzzleCatalog.open(source, cache, pack_id, validated=validated)

    def _catalog_root(self, pack_id: str) -> Path:
        source = self._location(pack_id)
        cache = source.parent.with_name(f"{source.parent.name}-catalogs") / pack_id
        try:
            resolved = cache.resolve()
        except (OSError, RuntimeError) as error:
            raise PackError(f"Cannot resolve the puzzle catalogue: {error}") from error
        if resolved != cache:
            raise PackError("Local puzzle catalogue paths must not be redirected.")
        return cache

    def _catalog_paths(self, pack_id: str) -> tuple[Path, Path]:
        source = self._location(pack_id)
        cache = self._catalog_root(pack_id)
        active = cache / "active.json"
        try:
            if active.is_symlink():
                raise PackError("Active puzzle revision must not be redirected.")
            with active.open("rb") as handle:
                generation = json.loads(handle.read(256))["generation"]
            if not isinstance(generation, str) or not re.fullmatch(r"[0-9a-f]{64}", generation):
                raise PackError("Invalid active puzzle revision.")
            directory = cache / "versions" / generation
            if directory.resolve() != directory or (directory / "source").resolve() != directory / "source":
                raise PackError("Puzzle revision paths must not be redirected.")
            return directory / "source", directory / "index"
        except FileNotFoundError:
            return source, cache
        except (OSError, TypeError, ValueError, KeyError, RuntimeError) as error:
            if isinstance(error, PackError):
                raise
            raise PackError(f"Cannot read active puzzle revision: {error}") from error

    def install_revision(self, pack_id: str, source: Path) -> IndexedPuzzlePack:
        """Publish a compatible replacement while keeping earlier generations intact."""
        from .catalog import PuzzleCatalog

        original = self._location(pack_id)
        if not original.is_dir():
            raise PackError(f"Puzzle pack '{pack_id}' is not installed.")
        manifest_data, body = _read_pack_data(source)
        proposed = _parse_pack(_decode_manifest(manifest_data), io.BytesIO(body), revalidate=True)
        if proposed.manifest.pack_id != pack_id or not proposed.puzzles:
            raise PackError("The revision must belong to the selected non-empty pack.")
        cache = self._catalog_root(pack_id)
        versions = cache / "versions"
        try:
            resolved = versions.resolve()
        except (OSError, RuntimeError) as error:
            raise PackError(f"Cannot resolve puzzle revisions: {error}") from error
        if resolved != versions:
            raise PackError("Puzzle revision paths must not be redirected.")
        generation = hashlib.sha256(manifest_data).hexdigest()
        destination = versions / generation
        try:
            versions.mkdir(parents=True, exist_ok=True)
            lock = cache / "updates.sqlite3"
            if lock.is_symlink():
                raise PackError("Puzzle catalogue update lock must not be redirected.")
            with closing(sqlite3.connect(lock, timeout=30)) as conn:
                conn.execute("BEGIN IMMEDIATE")
                current = self.open_catalog(pack_id)
                if current.manifest.version == proposed.manifest.version:
                    raise PackError("The new puzzle pack revision must have a different version.")
                with tempfile.TemporaryDirectory(prefix=".revision-", dir=versions) as temporary:
                    staged = Path(temporary)
                    _atomic_write(staged / "source" / "manifest.json", manifest_data)
                    _atomic_write(staged / "source" / "puzzles.jsonl", body)
                    indexed = PuzzleCatalog.open(staged / "source", staged / "index", pack_id, validated=proposed)
                    incompatible = current.catalog.incompatible_ids(indexed.catalog)
                    if incompatible:
                        raise PackError(f"Use a new pack id because {len(incompatible)} puzzle IDs changed or disappeared.")
                    if destination.exists():
                        existing = PuzzleCatalog.open(destination / "source", destination / "index", pack_id)
                        if existing.manifest != proposed.manifest:
                            raise PackError("Installed revision differs from the validated replacement.")
                    else:
                        staged.rename(destination)
                    _atomic_write(cache / "active.json", json.dumps({"generation": generation}).encode())
                conn.commit()
            return self.open_catalog(pack_id)
        except (OSError, sqlite3.Error) as error:
            raise PackError(f"Cannot publish puzzle revision '{pack_id}': {error}") from error

    def install(self, source: Path) -> PuzzlePack:
        manifest, body = _read_pack_data(source)
        pack = _parse_pack(_decode_manifest(manifest), io.BytesIO(body), revalidate=True)
        target = self._location(pack.manifest.pack_id)
        if not pack.puzzles:
            raise PackError("A local puzzle pack must contain at least one puzzle.")
        if target.exists():
            current = self.load(pack.manifest.pack_id)
            incompatible = current.incompatible_puzzle_ids(pack)
            if incompatible:
                sample = ", ".join(incompatible[:3])
                raise PackError(
                    f"Puzzle pack '{pack.manifest.pack_id}' is already installed. "
                    f"Use a new pack id because {len(incompatible)} puzzle IDs changed or disappeared ({sample})."
                )
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
