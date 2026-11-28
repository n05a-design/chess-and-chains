"""Profile a local official export and build the stratified IV-B puzzle pack.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
from contextlib import closing
import csv
from datetime import datetime, timezone
import hashlib
import heapq
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chess_and_chains.chess import ChessRules
from chess_and_chains.puzzles import Puzzle, PuzzleImportError, write_pack
from chess_and_chains.puzzles.importer import (
    LICHESS_COLUMNS, _HashingReader, _ID, _INVALID_UTF8, _RowError, open_puzzle_source, validate_row,
)
from chess_and_chains.storage.paths import ensure_safe_data_dir

SOURCE_URL = "https://database.lichess.org/lichess_db_puzzle.csv.zst"
LICENSE = "CC0 1.0 Universal (Lichess Open Database)"
PACK_ID = "lichess-core-20k"
STARTS = (1000, 1300, 1600, 1900, 2200, 2500, 3000)
LABELS = ("1000–1299", "1300–1599", "1600–1899", "1900–2199", "2200–2499", "2500–2999", "3000+")
QUOTAS = (2500, 4000, 4500, 3800, 2700, 1800, 700)
MIN_POPULARITY = 60
MAX_DEVIATION = 125
MIN_PLAYS = 10
SEED = 20261128


def source_profile(path: Path, scratch: Path, seed: int, reserve: int) -> tuple[dict, list]:
    """Stream the entire CSV, using a bounded heap and a disk-backed ID set."""
    source_ratings, eligible_ratings, quality = Counter(), Counter(), Counter()
    themes, eligible_themes, deviation_hist, popularity_hist, plays_hist = (
        Counter(), Counter(), Counter(), Counter(), Counter()
    )
    populations = [0] * len(QUOTAS)
    heaps: list[list[tuple[int, str, int, tuple[str, ...]]]] = [[] for _ in QUOTAS]
    seed_bytes = f"{seed}:".encode("ascii")
    started = perf_counter()
    rows_read = 0
    with closing(sqlite3.connect(scratch / "source-ids.sqlite3")) as seen, open_puzzle_source(path) as raw:
        seen.execute("CREATE TABLE seen (id TEXT PRIMARY KEY) WITHOUT ROWID")
        stream = _HashingReader(raw)
        with io.TextIOWrapper(io.BufferedReader(stream), encoding="utf-8-sig", errors="surrogateescape", newline="") as text:
            reader = csv.reader(text, strict=True)
            header = next(reader, ())
            if tuple(header[:len(LICHESS_COLUMNS)]) != LICHESS_COLUMNS or len(header) != len(set(header)):
                raise PuzzleImportError(f"Unexpected CSV header: {header}")
            with seen:
                for row in reader:
                    rows_read += 1
                    if len(row) != len(header) or any(_INVALID_UTF8.search(value) for value in row):
                        quality["malformed_record"] += 1
                        continue
                    puzzle_id, fen, moves, rt, rd, pop, count, tags, game_url, opening = row[:10]
                    if not _ID.fullmatch(puzzle_id):
                        quality["invalid_id"] += 1
                        continue
                    if not seen.execute("INSERT OR IGNORE INTO seen VALUES (?)", (puzzle_id,)).rowcount:
                        quality["duplicate_source_id"] += 1
                        continue
                    try:
                        rating, deviation, popularity, plays = map(int, (rt, rd, pop, count))
                    except ValueError:
                        quality["missing_or_invalid_number"] += 1
                        continue
                    if rating <= 0 or deviation < 0 or not -100 <= popularity <= 100 or plays < 0:
                        quality["out_of_range_number"] += 1
                        continue
                    source_ratings[rating] += 1
                    deviation_hist[deviation] += 1
                    popularity_hist[popularity] += 1
                    plays_hist[bisect_right((10, 50, 100, 1000, 10000), plays)] += 1
                    source_tags = set(tags.split())
                    themes.update(source_tags)
                    quality["missing_themes"] += not source_tags
                    quality["missing_openings"] += not opening
                    quality["missing_fen"] += not fen
                    quality["missing_moves"] += not moves
                    quality["unexpected_game_url"] += not game_url.startswith("https://lichess.org/")
                    quality["rating_below_1000"] += rating < 1000
                    quality["popularity_below_minimum"] += popularity < MIN_POPULARITY
                    quality["deviation_above_maximum"] += deviation > MAX_DEVIATION
                    quality["plays_below_minimum"] += plays < MIN_PLAYS
                    if (rating < 1000 or popularity < MIN_POPULARITY or deviation > MAX_DEVIATION or plays < MIN_PLAYS
                            or not (fen and moves and source_tags and game_url.startswith("https://lichess.org/"))):
                        continue
                    band = bisect_right(STARTS, rating) - 1
                    populations[band] += 1
                    eligible_themes.update(source_tags)
                    eligible_ratings[rating] += 1
                    priority = -int.from_bytes(hashlib.sha256(seed_bytes + puzzle_id.encode("ascii")).digest(), "big")
                    heap = heaps[band]
                    if len(heap) < QUOTAS[band] * reserve:
                        heapq.heappush(heap, (priority, puzzle_id, rows_read, tuple(row[:10])))
                    elif priority > heap[0][0]:
                        heapq.heapreplace(heap, (priority, puzzle_id, rows_read, tuple(row[:10])))
    profile = dict(
        rows=rows_read, csv_headers=header, input_bytes=stream.bytes_read, input_sha256=stream.digest.hexdigest(),
        indicators=dict(quality), ratings=dict(sorted(source_ratings.items())),
        eligible_ratings=dict(sorted(eligible_ratings.items())), source_themes=dict(themes.most_common()),
        eligible_themes=dict(eligible_themes.most_common()), rating_deviation=dict(sorted(deviation_hist.items())),
        popularity=dict(sorted(popularity_hist.items())),
        plays=dict(zip(("0–9", "10–49", "50–99", "100–999", "1000–9999", "10000+"),
                       (plays_hist[i] for i in range(6)))),
        eligible_by_band=dict(zip(LABELS, populations)), retained_by_band=dict(zip(LABELS, map(len, heaps))),
        profile_seconds=round(perf_counter() - started, 3),
    )
    return profile, heaps


def select(heaps: list, source: str, quotas: tuple[int, ...] = QUOTAS) -> tuple[list[Puzzle], dict]:
    """Fill all quotas using full rule validation and shared semantic identity."""
    started = perf_counter()
    rules = ChessRules()
    accepted: list[Puzzle] = []
    content: set[tuple] = set()
    counts: dict[str, dict] = {}
    for band, heap, quota in zip(LABELS, heaps, quotas, strict=True):
        rejected: Counter[str] = Counter()
        stats = {"quota": quota, "examined": 0, "accepted": 0, "rejected": rejected}
        for _, _, _, values in sorted(heap, reverse=True):
            if stats["accepted"] == quota:
                break
            stats["examined"] += 1
            try:
                puzzle = validate_row(dict(zip(LICHESS_COLUMNS, values, strict=True)), rules, source)
            except _RowError as error:
                rejected[error.reason] += 1
                continue
            playable = puzzle.start_state(rules)
            identity = (rules.position_key(playable), puzzle.solution)
            if identity in content:
                rejected["duplicate_playable_position_and_solution"] += 1
                continue
            content.add(identity)
            accepted.append(puzzle)
            stats["accepted"] += 1
        counts[band] = stats
        if stats["accepted"] != quota:
            raise PuzzleImportError(f"Incomplete band {band}: {stats}. Increase --reserve or revise the documented quotas.")
    return accepted, {"bands": counts, "validation_seconds": round(perf_counter() - started, 3)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-sha256", required=True, help="SHA-256 of the original compressed download")
    parser.add_argument("--snapshot", required=True, help="ISO date assigned to this verified snapshot")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--reserve", type=int, choices=range(1, 9), default=2)
    args = parser.parse_args()
    try:
        date = datetime.strptime(args.snapshot, "%Y-%m-%d").date().isoformat()
        if not args.source.is_file() or not args.source.name.endswith(".csv.zst"):
            raise PuzzleImportError("Use the original local .csv.zst download.")
        if args.output.exists():
            raise PuzzleImportError("Choose a fresh output directory.")
        parent = ensure_safe_data_dir(args.output.parent)
        with args.source.open("rb") as handle:
            source_sha = hashlib.file_digest(handle, "sha256").hexdigest()
        if source_sha != args.expected_sha256.lower():
            raise PuzzleImportError("Compressed download has an unexpected SHA-256.")
        source = f"Lichess Open Database · {date} · SHA-256 {source_sha} · {SOURCE_URL}"
        with tempfile.TemporaryDirectory(prefix=".lichess-core-", dir=parent) as temporary:
            scratch = Path(temporary)
            profile, heaps = source_profile(args.source, scratch, args.seed, args.reserve)
            print(json.dumps({"profile": {key: profile[key] for key in (
                "rows", "eligible_by_band", "indicators", "profile_seconds",
            )}}, ensure_ascii=False), flush=True)
            puzzles, selection = select(heaps, source)
            staging = scratch / PACK_ID
            started = perf_counter()
            manifest = write_pack(
                staging, puzzles, pack_id=PACK_ID, version=f"{date}-{source_sha[:12]}",
                source=source, license_note=LICENSE,
            )
            selected_themes = Counter(theme for puzzle in puzzles for theme in set(puzzle.themes))
            provenance = {
                "schema": 1, "origin": SOURCE_URL, "source_filename": args.source.name, "license": LICENSE,
                "compressed_sha256": source_sha, "compressed_bytes": args.source.stat().st_size, "snapshot": date,
                "processed_utc": datetime.now(timezone.utc).isoformat(), "profile": profile,
                "selection": {"algorithm": "sha256-stratified-v1", "seed": args.seed, "reserve": args.reserve,
                              "quality_filters": {"min_rating": 1000, "min_popularity": MIN_POPULARITY,
                                                  "max_rating_deviation": MAX_DEVIATION, "min_plays": MIN_PLAYS},
                              "themes": dict(selected_themes.most_common()), **selection},
                "manifest": manifest.to_dict(), "pack_publication_seconds": round(perf_counter() - started, 3),
            }
            (staging / "import_report.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n",
                                                        encoding="utf-8")
            staging.rename(parent / args.output.name)
    except (OSError, ValueError, csv.Error, sqlite3.Error) as error:
        parser.error(str(error))
    print(json.dumps({"manifest": manifest.to_dict(), "selection": selection}, ensure_ascii=False))


if __name__ == "__main__":
    main()
