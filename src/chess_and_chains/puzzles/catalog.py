"""SQLite read index built locally from validated JSONL puzzle packs.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

from collections.abc import Sequence, Set
from contextlib import closing
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import re
import sqlite3
import tempfile

from ..chess import to_fen
from .model import Puzzle, ValidationStatus
from .pack import PACK_SCHEMA, PackError, PackManifest, PuzzlePack, _MANIFEST_LIMIT, _PACK_LIMIT, _atomic_write, read_pack

CATALOG_SCHEMA = 1
_PAGE_SIZE = 48
_DIGEST = re.compile(r"[0-9a-f]{64}")
_INDEX_LIMIT = 4 * _PACK_LIMIT

_SCHEMA = """
PRAGMA user_version = 1;
CREATE TABLE puzzles (
    ordinal INTEGER PRIMARY KEY,
    id TEXT NOT NULL UNIQUE,
    rating INTEGER NOT NULL,
    content_id TEXT NOT NULL,
    record TEXT NOT NULL
);
CREATE INDEX puzzles_rating ON puzzles(rating, ordinal);
CREATE TABLE themes (
    theme TEXT NOT NULL,
    puzzle INTEGER NOT NULL REFERENCES puzzles(ordinal),
    PRIMARY KEY(theme, puzzle)
) WITHOUT ROWID;
"""


def _digest(path: Path, limit: int) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as handle:
        total = 0
        while block := handle.read(256 * 1024):
            total += len(block)
            if total > limit:
                raise PackError("Puzzle catalogue exceeds the file size limit.")
            checksum.update(block)
    return checksum.hexdigest()


def _source_manifest(path: Path) -> tuple[PackManifest, str]:
    with path.open("rb") as handle:
        data = handle.read(_MANIFEST_LIMIT + 1)
    if len(data) > _MANIFEST_LIMIT:
        raise PackError("Puzzle catalogue manifest exceeds its size limit.")
    raw = json.loads(data)
    if type(raw["schema"]) is not int or raw["schema"] != PACK_SCHEMA:
        raise PackError("Unsupported puzzle pack schema.")
    manifest = PackManifest(**{key: raw[key] for key in PackManifest.__slots__ if key in raw})
    return manifest, hashlib.sha256(data).hexdigest()


@dataclass(frozen=True, slots=True)
class IndexedPuzzlePack:
    manifest: PackManifest
    catalog: PuzzleCatalog

    @property
    def puzzles(self) -> PuzzleSelection:
        return self.catalog.select()


class PuzzleCatalog:
    """An immutable index opened only through the local validation receipt."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @classmethod
    def open(
        cls, source: Path, cache: Path, pack_id: str, *, validated: PuzzlePack | None = None,
    ) -> IndexedPuzzlePack:
        try:
            if any((source / name).is_symlink() for name in ("manifest.json", "puzzles.jsonl")):
                raise PackError("Installed puzzle sources must not be redirected.")
            manifest, manifest_hash = _source_manifest(source / "manifest.json")
            if manifest.pack_id != pack_id or type(manifest.count) is not int or manifest.count < 1:
                raise PackError("Invalid installed puzzle pack identity or count.")
            payload_hash = _digest(source / "puzzles.jsonl", _PACK_LIMIT)
            if payload_hash != manifest.sha256:
                raise PackError("Pack checksum mismatch; the pack is corrupt or modified.")
            if cache.resolve() != cache:
                raise PackError("Local puzzle catalogue paths must not be redirected.")
            receipt_path = cache / "validated.json"
            if receipt_path.is_symlink():
                raise PackError("Local puzzle catalogue receipts must not be redirected.")
            try:
                with receipt_path.open("rb") as handle:
                    receipt = json.loads(handle.read(_MANIFEST_LIMIT + 1))
            except FileNotFoundError:
                receipt = None
            if receipt is not None:
                if (receipt["manifest"], receipt["payload"]) != (manifest_hash, payload_hash):
                    raise PackError("Installed puzzle pack has changed since validation.")
                if type(receipt["schema"]) is not int or receipt["schema"] > CATALOG_SCHEMA:
                    raise PackError("Unsupported local puzzle catalogue receipt schema.")
                if receipt["schema"] == CATALOG_SCHEMA:
                    index_hash = receipt["index"]
                    if not isinstance(index_hash, str) or not _DIGEST.fullmatch(index_hash):
                        raise PackError("Invalid local puzzle catalogue receipt.")
                    index = cache / f"{index_hash}.sqlite3"
                    if index.is_symlink() or _digest(index, _INDEX_LIMIT) != index_hash:
                        raise PackError("Local puzzle catalogue failed its integrity check.")
                    catalog = cls(index)
                    with closing(catalog._connect()) as conn:
                        if conn.execute("PRAGMA user_version").fetchone()[0] != CATALOG_SCHEMA:
                            raise PackError("Unsupported puzzle catalogue schema.")
                    return IndexedPuzzlePack(manifest, catalog)

            pack = read_pack(source) if validated is None else validated
            if pack.manifest != manifest or _source_manifest(source / "manifest.json")[1] != manifest_hash:
                raise PackError("Installed puzzle pack changed during validation.")
            return cls._build(cache, pack.manifest, pack.puzzles, manifest_hash)
        except (OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError, sqlite3.Error) as error:
            if isinstance(error, PackError):
                raise
            raise PackError(f"Cannot open puzzle catalogue '{pack_id}': {error}") from error

    @classmethod
    def _build(
        cls, cache: Path, manifest: PackManifest, puzzles: Sequence[Puzzle], manifest_hash: str,
    ) -> IndexedPuzzlePack:
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".index-", dir=cache) as temporary:
            staged = Path(temporary) / "catalog.sqlite3"
            with closing(sqlite3.connect(staged)) as conn:
                conn.executescript(_SCHEMA)
                with conn:
                    for ordinal, puzzle in enumerate(puzzles):
                        record = puzzle.to_record()
                        content = (to_fen(puzzle.initial_state()), record["moves"])
                        content_id = hashlib.sha256(json.dumps(content, separators=(",", ":")).encode()).hexdigest()
                        conn.execute("INSERT INTO puzzles VALUES (?, ?, ?, ?, ?)",
                                     (ordinal, puzzle.puzzle_id, puzzle.rating, content_id,
                                      json.dumps(record, ensure_ascii=False, separators=(",", ":"))))
                        conn.executemany("INSERT INTO themes VALUES (?, ?)",
                                         ((theme, ordinal) for theme in sorted(set(puzzle.themes))))
            index_hash = _digest(staged, _INDEX_LIMIT)
            index = cache / f"{index_hash}.sqlite3"
            if not index.exists():
                staged.replace(index)
            elif index.is_symlink() or _digest(index, _INDEX_LIMIT) != index_hash:
                raise PackError("Local puzzle catalogue failed its integrity check.")
            receipt = {"schema": CATALOG_SCHEMA, "manifest": manifest_hash,
                       "payload": manifest.sha256, "index": index_hash}
            _atomic_write(cache / "validated.json", json.dumps(receipt).encode("utf-8"))
        return IndexedPuzzlePack(manifest, cls(index))

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path.as_uri() + "?mode=ro&immutable=1", uri=True)
        try:
            conn.execute("PRAGMA trusted_schema = OFF")
        except sqlite3.Error:
            conn.close()
            raise
        return conn

    @property
    def themes(self) -> tuple[str, ...]:
        with closing(self._connect()) as conn:
            return tuple(theme for (theme,) in conn.execute("SELECT DISTINCT theme FROM themes ORDER BY theme"))

    def get(self, puzzle_id: str) -> Puzzle | None:
        return self._get_rows((puzzle_id,)).get(puzzle_id)

    def content_identity(self, puzzle_id: str) -> str | None:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT content_id FROM puzzles WHERE id = ?", (puzzle_id,)).fetchone()
        return row[0] if row else None

    def incompatible_ids(self, replacement: PuzzleCatalog) -> tuple[str, ...]:
        """Find changed or removed puzzles whose progress must keep its identity."""
        with closing(replacement._connect()) as conn:
            current_ids = dict(conn.execute("SELECT id, content_id FROM puzzles"))
        with closing(self._connect()) as conn:
            return tuple(puzzle_id for puzzle_id, content_id in
                         conn.execute("SELECT id, content_id FROM puzzles ORDER BY id")
                         if current_ids.get(puzzle_id) != content_id)

    def _get_rows(self, ids: Sequence[str]) -> dict[str, Puzzle]:
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        with closing(self._connect()) as conn:
            rows = conn.execute(f"SELECT id, record FROM puzzles WHERE id IN ({placeholders})", tuple(ids))
            return {puzzle_id: Puzzle.from_record(json.loads(record), ValidationStatus.VALID)
                    for puzzle_id, record in rows}

    def select(
        self, *, minimum: int = 0, maximum: int | None = None, theme: str | None = None,
        included: Set[str] | None = None, excluded: Set[str] = frozenset(),
    ) -> PuzzleSelection:
        statement = "SELECT p.id FROM puzzles p"
        parameters: list[int | str] = []
        if theme is not None:
            statement += " JOIN themes t ON t.puzzle = p.ordinal AND t.theme = ?"
            parameters.append(theme)
        statement += " WHERE p.rating >= ?"
        parameters.append(minimum)
        if maximum is not None:
            statement += " AND p.rating <= ?"
            parameters.append(maximum)
        statement += " ORDER BY p.ordinal"
        with closing(self._connect()) as conn:
            ids = tuple(puzzle_id for (puzzle_id,) in conn.execute(statement, parameters)
                        if puzzle_id not in excluded and (included is None or puzzle_id in included))
        return PuzzleSelection(self, ids)


class PuzzleSelection(Sequence[Puzzle]):
    """A lightweight ordered ID selection with one lazily read page of boards."""

    def __init__(self, catalog: PuzzleCatalog, ids: tuple[str, ...]) -> None:
        self.catalog = catalog
        self.ids = ids
        self._page: dict[str, Puzzle] = {}

    def __len__(self) -> int:
        return len(self.ids)

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, end, step = index.indices(len(self))
            return tuple(self[position] for position in range(start, end, step))
        puzzle_id = self.ids[index]
        if puzzle_id not in self._page:
            start = (index % len(self) // _PAGE_SIZE) * _PAGE_SIZE
            self._page = self.catalog._get_rows(self.ids[start:start + _PAGE_SIZE])
        return self._page[puzzle_id]

    def sample_ids(self, count: int, *, seed: int) -> tuple[str, ...]:
        return tuple(random.Random(seed).sample(self.ids, count))
