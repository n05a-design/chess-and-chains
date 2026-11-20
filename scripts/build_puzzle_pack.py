"""Build a validated, versioned puzzle pack from a local Lichess-format CSV.

Never downloads data. Example (demo pack, project-authored positions):

    PYTHONPATH=src python scripts/build_puzzle_pack.py data/source/demo_puzzles.csv \
        src/chess_and_chains/puzzles/data/demo --pack-id demo --version 1 --demo \
        --source "Chess & Chains project-authored demo positions" \
        --license "MPL-2.0 (project-authored); ratings are fixture values, not measured"

For a real Lichess export (CC0, owner-downloaded) write packs OUTSIDE the
Git checkout, e.g. into the user data directory.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chess_and_chains.puzzles import import_lichess_file, write_pack  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--pack-id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--source", dest="source_label", required=True)
    parser.add_argument("--license", required=True)
    parser.add_argument("--min-rating", type=int, default=1000)
    parser.add_argument("--max-rating", type=int)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args(argv)
    puzzles, report = import_lichess_file(
        args.source, min_rating=args.min_rating, max_rating=args.max_rating, limit=args.limit
    )
    manifest = write_pack(
        args.output, puzzles, pack_id=args.pack_id, version=args.version,
        source=args.source_label, license_note=args.license, report=report, demo=args.demo,
    )
    print(json.dumps({"manifest": manifest.to_dict(), "report": report.to_dict()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
