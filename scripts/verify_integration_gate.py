"""Verify the III/IV-B workflow offline using an existing validated catalog.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
from shutil import copytree
import sqlite3
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from chess_and_chains.chess import Move, to_fen
from chess_and_chains.engines.analysis import AnalysisMode, AnalysisRequest, AnalysisService, JobStatus
from chess_and_chains.engines.registry import EngineRegistry
from chess_and_chains.puzzles import PackLibrary
from chess_and_chains.storage import DataLayout, Database, Settings, save_settings
from scripts.verify_lichess_core_pack import PACK_ID, measure, open_desktop, require, verify_native
from tests.test_engine_analysis import FIXTURE

RAW_SHA = "7b0d235fa40cfd7fdb7df1fec56a96b3b6ee1496b32ed2eb05be90d0ebf94253"
PAYLOAD_SHA = "2ebc99d811d159e42a39ae33acb280c2e6a410826d9c67f24386924343b338a6"
INDEX_SHA = "eacede1d861a23ab06035fbcc58c7ad60e7ce34b485329d93dc38a395379d0e2"


def sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def check_existing_assets(directory: Path) -> dict:
    pack = directory / PACK_ID
    profile = directory / "test-profile"
    report = json.loads((pack / "import_report.json").read_text(encoding="utf-8"))
    require(sha(directory / "lichess_db_puzzle.csv.zst") == report["compressed_sha256"] == RAW_SHA,
            "Raw download or source provenance differs.")
    require(sha(pack / "puzzles.jsonl") == report["manifest"]["sha256"] == PAYLOAD_SHA,
            "Pack payload or build report differs.")
    receipt = profile / "puzzle_packs-catalogs" / PACK_ID / "validated.json"
    validated = json.loads(receipt.read_text(encoding="utf-8"))
    require(sha(receipt.with_name(f"{INDEX_SHA}.sqlite3")) == validated["index"] == INDEX_SHA,
            "Existing index checksum differs.")
    require(sha(pack / "manifest.json") == validated["manifest"]
            and sha(profile / "puzzle_packs" / PACK_ID / "manifest.json") == validated["manifest"]
            and sha(profile / "puzzle_packs" / PACK_ID / "puzzles.jsonl") == validated["payload"] == PAYLOAD_SHA,
            "Installed source differs from the validated original.")
    proof = (directory / "reproduction.log").read_text(encoding="utf-8").splitlines()
    require(f"reproduced JSONL SHA-256 {PAYLOAD_SHA}" in proof, "Independent reproduction record is missing.")
    database = profile / "chess_and_chains.sqlite3"
    with closing(sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)) as reader:
        schema = reader.execute("PRAGMA user_version").fetchone()[0]
        progress = reader.execute(
            "SELECT COUNT(*), COALESCE(SUM(attempts), 0), COALESCE(SUM(clean_solves), 0) "
            "FROM puzzle_progress WHERE pack_id = ?", (PACK_ID,),
        ).fetchone()
    require(schema == 8 and progress == (2, 3, 1), "Existing offline test progress differs.")
    return {"raw_sha256": RAW_SHA, "jsonl_sha256": PAYLOAD_SHA, "index_sha256": INDEX_SHA,
            "existing_progress": list(progress), "schema": schema,
            "source_database_sha256": sha(database)}


def prepare_analysis_candidate(layout: DataLayout) -> str:
    fixture = layout.root / "fixture.py"
    log = layout.root / "uci.log"
    fixture.write_text(FIXTURE, encoding="utf-8")
    registry = EngineRegistry(layout.engine_registry)
    stored = registry.register(sys.executable, arguments=("-u", str(fixture), str(log), "restricted"),
                               resources=(fixture,), origin="fixture")
    registry.probe(stored.engine_id)
    registry = EngineRegistry(layout.engine_registry)
    config = registry.launch_configuration(stored.engine_id)
    with Database.open(layout.database) as database:
        game_id = database.import_pgn("1. e4 d5 *")
        game = database.load_game(game_id).to_game()
        for attempt in (1, 2):
            service = AnalysisService(config, engine_id=config.session_reference(), cache_path=layout.analysis_cache)
            request = AnalysisRequest(f"gate-{attempt}", moves=tuple(game.moves), mode=AnalysisMode.GAME)
            job = service.start(request)
            require(job.wait(15), "Analysis fixture did not finish.")
            report = job.progress()
            require(report.status is JobStatus.COMPLETED and len(report.results) == 3,
                    f"Analysis fixture failed: {report.error}")
            require(all(result.cached == (attempt == 2) for result in report.results),
                    "Analysis cache did not survive service recreation.")
        commands = log.read_text(encoding="utf-8").splitlines()
        require(commands.count("go movetime 100") == 3
                and sum(command.startswith("go movetime 100 searchmoves") for command in commands) == 4,
                "The second service unexpectedly searched again.")
        database.save_analysis_report(game_id, report)
        candidate = database.save_analysis_training_candidate(report.job_id, 0)
        require(candidate.played_move == Move.from_uci("e2e4"), "Wrong played move in candidate.")
        database.delete_game(game_id)
        require(not database.analysis_reports(), "Deleted source report is still attached.")
    return candidate.candidate_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_directory", type=Path)
    args = parser.parse_args()
    directory = args.data_directory.resolve(strict=True)
    metrics = check_existing_assets(directory)
    source_profile = directory / "test-profile"
    with TemporaryDirectory(prefix=".integration-gate-", dir=directory) as temporary:
        layout = DataLayout(Path(temporary))
        for name in ("puzzle_packs", "puzzle_packs-catalogs"):
            copytree(source_profile / name, layout.root / name)
        library = PackLibrary(layout.packs)
        pack = measure(metrics, "verified_index_open_ms", lambda: library.open_catalog(PACK_ID))
        puzzles = pack.puzzles
        wanted = (len(puzzles), len(set(puzzles.ids)), min(p.rating for p in puzzles),
                  max(p.rating for p in puzzles), len(pack.catalog.select(minimum=3000)))
        require(wanted == (20_000, 20_000, 1000, 3330, 700), f"Unexpected verified ratings: {wanted}")
        metrics["puzzle_counts"] = list(wanted)
        save_settings(layout.settings, Settings(last_pack_id=PACK_ID))
        candidate_id = prepare_analysis_candidate(layout)
        verify_native(layout, metrics)
        app = open_desktop(layout)
        try:
            candidate, = app.db.analysis_training_candidates()
            require(candidate.candidate_id == candidate_id, "Candidate lost during puzzle backup/restore.")
            with patch.object(app, "_choose_item", return_value=0):
                app._open_training_positions()
            require(to_fen(app.game.state) == candidate.fen, "Candidate did not open for free practice.")
        finally:
            app.close()
        metrics["analysis_to_candidate_to_catalog_and_restore"] = True
    require(sha(source_profile / "chess_and_chains.sqlite3") == metrics["source_database_sha256"],
            "The original QA profile was unexpectedly modified.")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
