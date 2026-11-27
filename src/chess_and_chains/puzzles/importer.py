"""Streaming, validating importer for the Lichess puzzle CSV export.

* Reads row by row; the multi-gigabyte export is never loaded into memory.
* Computes a SHA-256 of the CSV stream for provenance when read to completion.
* Rejects rows below ``min_rating`` (default 1000), duplicates, malformed
  fields, invalid FEN and any illegal setup/solution move.
* Never downloads anything. Callers pass a local file the owner obtained.
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import csv
import hashlib
import io
import re
import sqlite3
import tempfile
from collections import Counter
from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime, timezone
from heapq import nsmallest
from pathlib import Path
from typing import BinaryIO, Callable, Iterable, Iterator

from ..chess import ChessError, ChessRules, Move, parse_fen
from .model import MIN_PUBLISHED_RATING, Puzzle, ValidationStatus, validate_solution_line

LICHESS_COLUMNS = (
    "PuzzleId", "FEN", "Moves", "Rating", "RatingDeviation",
    "Popularity", "NbPlays", "Themes", "GameUrl", "OpeningTags",
)
_ID = re.compile(r"^[A-Za-z0-9]{3,16}$")
_THEME = re.compile(r"^[A-Za-z0-9]+$")
_INVALID_UTF8 = re.compile(r"[\udc80-\udcff]")
MAX_SOLUTION_PLIES = 40

RATING_BANDS = (
    (1199, "1000-1199"), (1399, "1200-1399"), (1599, "1400-1599"),
    (1799, "1600-1799"), (1999, "1800-1999"), (2399, "2000-2399"),
)


@dataclass
class PuzzleDistribution:
    ratings: Counter[str] = field(default_factory=Counter)
    themes: Counter[str] = field(default_factory=Counter)

    def include(self, puzzle: Puzzle) -> None:
        band = next((label for ceiling, label in RATING_BANDS if puzzle.rating <= ceiling), "2400+")
        self.ratings[band] += 1
        self.themes.update(set(puzzle.themes))

    def to_dict(self) -> dict[str, dict[str, int]]:
        return {"rating_bands": dict(sorted(self.ratings.items())), "themes": dict(sorted(self.themes.items()))}


class PuzzleImportError(ValueError):
    """The input cannot be imported at all (bad header, unsupported format)."""


class _RowError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class _HashingReader(io.RawIOBase):
    def __init__(self, raw: BinaryIO) -> None:
        self._raw = raw
        self.digest = hashlib.sha256()
        self.bytes_read = 0

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:  # type: ignore[override]
        data = self._raw.read(len(buffer))
        if not data:
            return 0
        self.digest.update(data)
        self.bytes_read += len(data)
        buffer[: len(data)] = data
        return len(data)


@dataclass
class ImportReport:
    source_name: str
    min_rating: int
    max_rating: int | None
    started_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    finished_utc: str | None = None
    rows_read: int = 0
    accepted: int = 0
    rejected: Counter = field(default_factory=Counter)
    examples: dict[str, str] = field(default_factory=dict)
    input_sha256: str | None = None
    input_bytes: int = 0
    complete: bool = False
    max_rating_deviation: int | None = field(default=None, kw_only=True)
    min_popularity: int | None = field(default=None, kw_only=True)
    min_plays: int | None = field(default=None, kw_only=True)
    selection_limit: int | None = field(default=None, init=False)
    selection_seed: int | None = field(default=None, init=False)
    accepted_distribution: PuzzleDistribution = field(default_factory=PuzzleDistribution, init=False)
    selected_distribution: PuzzleDistribution | None = field(default=None, init=False)

    def record_selection(self, puzzles: Iterable[Puzzle]) -> None:
        distribution = PuzzleDistribution()
        for puzzle in puzzles:
            distribution.include(puzzle)
        self.selected_distribution = distribution

    def reject(self, reason: str, puzzle_id: str) -> None:
        self.rejected[reason] += 1
        self.examples.setdefault(reason, puzzle_id)

    def to_dict(self) -> dict:
        selected = self.accepted if self.selection_limit is None else min(self.accepted, self.selection_limit)
        return {
            "source_name": self.source_name,
            "filters": {
                "min_rating": self.min_rating,
                "max_rating": self.max_rating,
                "max_rating_deviation": self.max_rating_deviation,
                "min_popularity": self.min_popularity,
                "min_plays": self.min_plays,
            },
            "started_utc": self.started_utc,
            "finished_utc": self.finished_utc,
            "rows_read": self.rows_read,
            "accepted": self.accepted,
            "selection": {
                "strategy": "input-order" if self.selection_seed is None else "sha256-top-k-v1",
                "seed": self.selection_seed,
                "limit": self.selection_limit,
                "selected": selected,
            },
            "distribution": {
                "accepted": self.accepted_distribution.to_dict(),
                "selected": (self.selected_distribution or self.accepted_distribution).to_dict(),
            },
            "rejected": dict(sorted(self.rejected.items())),
            "rejected_examples": dict(sorted(self.examples.items())),
            "input_sha256": self.input_sha256 if self.complete else None,
            "input_bytes": self.input_bytes,
            "complete": self.complete,
        }


def validate_row(row: dict[str, str], rules: ChessRules, source: str) -> Puzzle:
    """Convert and fully validate one CSV row; raises _RowError with a reason code."""
    puzzle_id = (row.get("PuzzleId") or "").strip()
    if not _ID.match(puzzle_id):
        raise _RowError("bad_id")
    try:
        rating = int(row.get("Rating", ""))
        deviation = int(row.get("RatingDeviation") or 0)
        popularity = int(row.get("Popularity") or 0)
        plays = int(row.get("NbPlays") or 0)
    except ValueError as error:
        raise _RowError("bad_number") from error
    if not -100 <= popularity <= 100 or deviation < 0 or plays < 0 or rating <= 0:
        raise _RowError("number_out_of_range")
    themes = tuple((row.get("Themes") or "").split())
    if any(not _THEME.match(theme) for theme in themes):
        raise _RowError("bad_theme")
    texts = (row.get("Moves") or "").split()
    if len(texts) < 2 or len(texts) > MAX_SOLUTION_PLIES:
        raise _RowError("bad_move_count")
    if len(texts) % 2:
        raise _RowError("solution_must_end_with_player_move")
    try:
        moves = [Move.from_uci(text) for text in texts]
    except ChessError as error:
        raise _RowError("bad_uci") from error
    fen = " ".join((row.get("FEN") or "").split())
    try:
        state = parse_fen(fen)
    except ChessError as error:
        raise _RowError("bad_fen") from error
    try:
        validate_solution_line(state, moves, rules)
    except ChessError as error:
        raise _RowError("illegal_move") from error
    return Puzzle(
        puzzle_id=puzzle_id,
        fen=fen,
        setup_move=moves[0],
        solution=tuple(moves[1:]),
        rating=rating,
        rating_deviation=deviation,
        popularity=popularity,
        plays=plays,
        themes=themes,
        source=source,
        game_url=(row.get("GameUrl") or "").strip(),
        opening_tags=tuple((row.get("OpeningTags") or "").split()),
        validation=ValidationStatus.VALID,
    )


def iter_lichess_csv(
    stream: BinaryIO,
    report: ImportReport,
    *,
    source: str = "lichess-puzzle-db",
    rules: ChessRules | None = None,
    limit: int | None = None,
) -> Iterator[Puzzle]:
    """Yield validated puzzles from a binary CSV stream, updating ``report``."""
    seen: set[str] = set()

    def register_id(puzzle_id: str) -> bool:
        if puzzle_id in seen:
            return False
        seen.add(puzzle_id)
        return True

    yield from _iter_lichess_csv(stream, report, register_id, source=source, rules=rules, limit=limit)


def _iter_lichess_csv(
    stream: BinaryIO,
    report: ImportReport,
    register_id: Callable[[str], bool],
    *,
    source: str,
    rules: ChessRules | None = None,
    limit: int | None = None,
) -> Iterator[Puzzle]:
    if report.min_rating < MIN_PUBLISHED_RATING:
        raise PuzzleImportError(f"Published packs require Rating >= {MIN_PUBLISHED_RATING}.")
    if report.max_rating is not None and report.max_rating < report.min_rating:
        raise PuzzleImportError("Maximum rating is below the minimum.")
    if report.max_rating_deviation is not None and report.max_rating_deviation < 0:
        raise PuzzleImportError("Maximum rating deviation must be non-negative.")
    if report.min_popularity is not None and not -100 <= report.min_popularity <= 100:
        raise PuzzleImportError("Minimum popularity must be between -100 and 100.")
    if report.min_plays is not None and report.min_plays < 0:
        raise PuzzleImportError("Minimum play count must be non-negative.")
    if limit is not None and limit < 1:
        raise PuzzleImportError("Puzzle limit must be positive.")
    report.selection_limit = limit
    required_quality_columns = tuple(column for column, threshold in (
        ("RatingDeviation", report.max_rating_deviation),
        ("Popularity", report.min_popularity),
        ("NbPlays", report.min_plays),
    ) if threshold is not None)
    chess_rules = rules or ChessRules()
    hashing = _HashingReader(stream)
    # Keep invalid bytes attached to their CSV record even when the text reader buffers ahead.
    text = io.TextIOWrapper(io.BufferedReader(hashing), encoding="utf-8", errors="surrogateescape", newline="")
    reader = csv.reader(text)
    try:
        header = next(reader)
    except StopIteration as error:
        raise PuzzleImportError("Empty puzzle file.") from error
    except csv.Error as error:
        raise PuzzleImportError("Cannot read the puzzle CSV header.") from error
    if any(_INVALID_UTF8.search(name) for name in header):
        raise PuzzleImportError("Puzzle CSV header is not UTF-8 text.")
    header = [name.strip().lstrip("﻿") for name in header]
    if (tuple(header[: len(LICHESS_COLUMNS)]) != LICHESS_COLUMNS
            or len(set(header)) != len(header)):
        raise PuzzleImportError(f"Unexpected CSV header: {header}")
    while True:
        if limit is not None and report.accepted >= limit:
            break
        try:
            values = next(reader)
        except StopIteration:
            # Drain remaining bytes so the checksum covers the whole file.
            while hashing.read(1 << 16):
                pass
            report.complete = True
            break
        except csv.Error:
            report.rows_read += 1
            report.reject("unreadable_row", f"row-{report.rows_read}")
            continue
        report.rows_read += 1
        if any(_INVALID_UTF8.search(value) for value in values):
            report.reject("unreadable_row", f"row-{report.rows_read}")
            continue
        if not values or values == [""]:
            report.reject("empty_row", f"row-{report.rows_read}")
            continue
        if len(values) != len(header):
            report.reject("column_count", values[0] if values else "?")
            continue
        row = dict(zip(header, values))
        puzzle_id = row["PuzzleId"].strip()
        if not _ID.fullmatch(puzzle_id):
            report.reject("bad_id", f"row-{report.rows_read}")
            continue
        # Register the id before filtering so its ownership is filter-independent.
        if not register_id(puzzle_id):
            report.reject("duplicate_id", puzzle_id)
            continue
        try:
            rating = int(row.get("Rating", ""))
        except ValueError:
            report.reject("bad_number", puzzle_id)
            continue
        if rating < report.min_rating:
            report.reject("below_min_rating", puzzle_id)
            continue
        if report.max_rating is not None and rating > report.max_rating:
            report.reject("above_max_rating", puzzle_id)
            continue
        try:
            puzzle = validate_row(row, chess_rules, source)
        except _RowError as error:
            report.reject(error.reason, puzzle_id)
            continue
        if any(not row[column] for column in required_quality_columns):
            report.reject("missing_quality_value", puzzle_id)
            continue
        if report.max_rating_deviation is not None and puzzle.rating_deviation > report.max_rating_deviation:
            report.reject("above_max_rating_deviation", puzzle_id)
            continue
        if report.min_popularity is not None and puzzle.popularity < report.min_popularity:
            report.reject("below_min_popularity", puzzle_id)
            continue
        if report.min_plays is not None and puzzle.plays < report.min_plays:
            report.reject("below_min_plays", puzzle_id)
            continue
        report.accepted += 1
        report.accepted_distribution.include(puzzle)
        yield puzzle
    report.input_bytes = hashing.bytes_read
    report.input_sha256 = hashing.digest.hexdigest()
    report.finished_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")


def open_puzzle_source(path: Path) -> BinaryIO:
    """Open ``.csv`` or (when the Python build supports it) ``.csv.zst`` files."""
    if path.suffix == ".zst":
        try:
            from compression import zstd  # Python 3.14+
        except ImportError as error:
            raise PuzzleImportError(
                "This Python build cannot read .zst; decompress the file first."
            ) from error
        return zstd.open(path, "rb")  # type: ignore[return-value]
    return path.open("rb")


def import_lichess_file(
    path: Path,
    *,
    min_rating: int = MIN_PUBLISHED_RATING,
    max_rating: int | None = None,
    max_rating_deviation: int | None = None,
    min_popularity: int | None = None,
    min_plays: int | None = None,
    limit: int | None = None,
    seed: int | None = None,
    source: str = "lichess-puzzle-db",
) -> tuple[list[Puzzle], ImportReport]:
    """Import in CSV order or select a reproducible subset from the whole source."""
    if seed is not None and (limit is None or limit < 1):
        raise PuzzleImportError("Seeded selection requires a positive puzzle limit.")
    report = ImportReport(
        path.name, min_rating, max_rating,
        max_rating_deviation=max_rating_deviation, min_popularity=min_popularity, min_plays=min_plays,
    )
    # A full export contains millions of distinct IDs. Store source IDs in a
    # disposable database so the input-order and seeded paths retain exact duplicate checks.
    with tempfile.TemporaryDirectory(prefix="chess-puzzle-import-") as directory:
        index_path = Path(directory) / "seen.sqlite3"
        with closing(sqlite3.connect(index_path)) as index, open_puzzle_source(path) as stream:
            index.execute("CREATE TABLE seen (id TEXT PRIMARY KEY) WITHOUT ROWID")

            def register_id(puzzle_id: str) -> bool:
                cursor = index.execute("INSERT OR IGNORE INTO seen (id) VALUES (?)", (puzzle_id,))
                return cursor.rowcount == 1

            if seed is None:
                return list(_iter_lichess_csv(stream, report, register_id, source=source, limit=limit)), report

            def rank(puzzle: Puzzle) -> tuple[bytes, str]:
                puzzle_id = puzzle.puzzle_id
                digest = hashlib.sha256(f"{seed}:{puzzle_id}".encode("ascii")).digest()
                return digest, puzzle_id

            # The selection heap is bounded by the pack limit while the reader checks all rows.
            puzzles = nsmallest(limit, _iter_lichess_csv(stream, report, register_id, source=source), key=rank)
    report.selection_seed = seed
    report.selection_limit = limit
    report.record_selection(puzzles)
    return puzzles, report
