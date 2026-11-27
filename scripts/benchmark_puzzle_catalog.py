"""Benchmark a synthetic puzzle pack and its local index without downloading data.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

from chess_and_chains.puzzles import PuzzleSession, load_demo_pack, read_pack, write_pack
from chess_and_chains.puzzles.catalog import PuzzleCatalog


def measure(record, name, operation):
    started = perf_counter()
    value = operation()
    record[name] = round((perf_counter() - started) * 1000, 3)
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("size", type=int, choices=(20000, 50000))
    size = parser.parse_args().size
    timings = {}
    fixtures = load_demo_pack().puzzles
    query_theme = fixtures[0].themes[0]
    with TemporaryDirectory(prefix="chess-catalog-benchmark-") as directory:
        root = Path(directory).resolve()
        source, cache = root / "pack", root / "index"
        pack_id = "synthetic-benchmark"
        puzzles = (
            replace(fixtures[i % len(fixtures)], puzzle_id=f"benchmark-{i:06}",
                    rating=1000 + (i * 37) % 1801)
            for i in range(size)
        )
        measure(timings, "jsonl_build_ms", lambda: write_pack(
            source, puzzles, pack_id=pack_id, version="1", source="Project benchmark fixtures", license_note="MPL-2.0",
        ))
        validated = measure(timings, "complete_validation_ms", lambda: read_pack(source))
        measure(timings, "index_publication_ms", lambda: PuzzleCatalog.open(source, cache, pack_id, validated=validated))
        del validated
        indexed = measure(timings, "reopen_ms", lambda: PuzzleCatalog.open(source, cache, pack_id))
        selection = measure(timings, "combined_filter_ms",
                            lambda: indexed.catalog.select(theme=query_theme, minimum=1350, maximum=2050))
        measure(timings, "id_lookup_ms", lambda: indexed.catalog.get(f"benchmark-{size - 1:06}"))
        measure(timings, "seeded_sample_ms", lambda: selection.sample_ids(20, seed=42))
        measure(timings, "next_session_ms", lambda: PuzzleSession(selection[1]))
        try:
            import resource
        except ImportError:
            rss = None
        else:
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if sys.platform != "darwin":
                rss *= 1024
        print(json.dumps({"puzzles": size, "matches": len(selection), "peak_rss_bytes": rss, **timings}))


if __name__ == "__main__":
    main()
