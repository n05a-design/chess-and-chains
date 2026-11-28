"""Install and verify an IV-B real pack in a fresh isolated desktop profile.

Run with Python/Tk and disabled networking for the offline acceptance.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from time import perf_counter, sleep

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chess_and_chains.puzzles import PackLibrary, PuzzleSession
from chess_and_chains.storage import DataLayout, Database, Settings, save_settings
from chess_and_chains.storage.backup_bundle import restore_backup, write_backup
from chess_and_chains.ui.app import PUZZLE_RATING_RANGES, launch

PACK_ID = "lichess-core-20k"


def require(condition: bool, description: str) -> None:
    if not condition:
        raise RuntimeError(description)


def measure(metrics: dict, name: str, operation):
    started = perf_counter()
    result = operation()
    metrics[name] = round((perf_counter() - started) * 1000, 3)
    return result


def open_desktop(layout: DataLayout):
    app = launch(data_layout=layout, mainloop=False)
    deadline = perf_counter() + 20
    while app.pack.manifest.pack_id != PACK_ID and perf_counter() < deadline:
        app.root.update()
        sleep(0.01)
    if app.pack.manifest.pack_id != PACK_ID:
        feedback = app.puzzle_pack_feedback.get()
        app.close()
        raise RuntimeError(f"The configured pack did not load: {feedback}")
    app.tab_rail.set_active("puzzles")
    app.root.update()
    return app


def solve(app) -> None:
    while app.puzzle.expected_move is not None:
        app._puzzle_move(app.puzzle.expected_move)
    require(app.puzzle.solved, "The expected move sequence did not solve the puzzle.")


def verify_native(layout: DataLayout, metrics: dict) -> None:
    app = measure(metrics, "desktop_reopen_ms", lambda: open_desktop(layout))
    try:
        app.puzzle_rating_filter.current(PUZZLE_RATING_RANGES.index((3000, None)) + 1)
        app.puzzle_theme_filter.current(app._puzzle_themes.index("middlegame") + 1)
        app._apply_puzzle_filters()
        require(app.puzzle is not None and app.puzzle.puzzle.rating >= 3000, "Desktop combined filter is empty.")
        require("middlegame" in app.puzzle.puzzle.themes, "Desktop mixed the selected theme.")
        require(app.puzzle.state == app.puzzle.puzzle.start_state(), "Opponent setup was not applied.")
        multistep = next(index for index, puzzle in enumerate(app._puzzle_selection) if len(puzzle.solution) > 1)
        app._start_puzzle(multistep)
        require(app.puzzle.state == app.puzzle.puzzle.start_state(), "Opponent setup was not applied.")
        trained = app.puzzle.puzzle.puzzle_id
        app._puzzle_hint()
        app._puzzle_hint()
        alternative = next(move for move in app.puzzle.legal_moves() if move != app.puzzle.expected_move)
        app._puzzle_move(alternative)
        require(app.puzzle.mistakes == 1 and app.puzzle.hints_used == 2, "Wrong move or hints were not tracked.")
        solve(app)
        app._record_puzzle()
        require(app.db.puzzle_progress(PACK_ID, trained).attempts == 1, "Completion was recorded twice.")
        require(app.db.latest_puzzle_attempt(PACK_ID, trained).mistakes == 1, "The attempt lost the mistake.")
        require(app.db.latest_puzzle_attempt(PACK_ID, trained).hints_used == 2, "The attempt lost the hints.")
        app.puzzle_status_filter.current(1)
        app._apply_puzzle_filters()
        require(trained not in app._puzzle_selection.ids, "Unsolved filter includes the solved task.")
        app.puzzle_status_filter.current(2)
        app._apply_puzzle_filters()
        require(app._puzzle_selection.ids == (trained,), "Review filter did not preserve the assisted success.")
        app._retry_puzzle()
        require(app.puzzle.state == app.puzzle.puzzle.start_state(), "Retry did not restore the opening board.")
        solve(app)
        require(app.db.puzzle_progress(PACK_ID, trained).clean_solves == 1, "Clean solve did not persist.")
        app.puzzle_status_filter.current(0)
        app._apply_puzzle_filters()
        app._next_puzzle()
        revealed = app.puzzle.puzzle.puzzle_id
        require(revealed != trained, "Next puzzle did not advance the selection.")
        app._puzzle_reveal()
        require(app.puzzle.revealed and not app.db.latest_puzzle_attempt(PACK_ID, revealed).solved,
                "Revealed answer counted as a solve.")
        due = app.db.due_puzzle_ids(PACK_ID, now=datetime.now(timezone.utc) + timedelta(days=30))
        require({trained, revealed} <= due, "Training schedule omitted a completed attempt.")
        require(not app.db.solved_puzzle_ids("demo"), "Progress escaped its package namespace.")
    finally:
        app.close()

    backup = layout.backups / "iv-b-offline-qa.zip"
    measure(metrics, "backup_ms", lambda: write_backup(layout, backup))
    with Database.open(layout.database) as database:
        database.record_puzzle_attempt(PACK_ID, trained, solved=False, mistakes=1, hints_used=0, duration_ms=10)
        require(database.puzzle_progress(PACK_ID, trained).attempts == 3, "Restore test could not add a distinct attempt.")
    measure(metrics, "restore_ms", lambda: restore_backup(layout, backup))
    app = open_desktop(layout)
    try:
        progress = app.db.puzzle_progress(PACK_ID, trained)
        require(progress.attempts == 2 and progress.clean_solves == 1, "Restore did not preserve the intended attempts.")
        require(not app.db.latest_puzzle_attempt(PACK_ID, revealed).solved, "Reveal attempt did not survive startup.")
        require(trained in app._solved_puzzle_ids, "Desktop progress did not reload.")
    finally:
        app.close()
    with TemporaryDirectory(prefix=".qa-missing-pack-", dir=layout.root.parent) as temporary:
        other = DataLayout(Path(temporary))
        result = restore_backup(other, backup)
        require(result.missing_packs == (PACK_ID,), "Restore did not report the absent local pack.")
        with Database.open(other.database) as database:
            require(database.puzzle_progress(PACK_ID, trained).clean_solves == 1,
                    "Progress was lost when the separate catalog was unavailable.")
    metrics["desktop_checks"] = {
        "combined_rating_and_theme": True, "opponent_setup": True, "wrong_move_and_hints": True,
        "solve_once": True, "unsolved_and_review": True, "retry_clean_solve": True, "next_and_reveal": True,
        "due_schedule": True, "pack_namespacing": True, "backup_restore": True, "startup_progress": True,
        "missing_pack_restore": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path)
    parser.add_argument("profile", type=Path)
    args = parser.parse_args()
    if args.profile.exists():
        parser.error("Choose a new isolated profile directory.")
    metrics: dict = {}
    try:
        layout = DataLayout(args.profile)
        library = PackLibrary(layout.packs)
        validated = measure(metrics, "local_install_and_complete_validation_ms", lambda: library.install(args.pack))
        require(validated.manifest.pack_id == PACK_ID and len(validated.puzzles) == 20_000,
                "Incorrect product pack or puzzle count.")
        measure(metrics, "index_publication_ms", lambda: library._open_catalog(PACK_ID, validated=validated))
        del validated
        indexed = measure(metrics, "warm_index_open_ms", lambda: library.open_catalog(PACK_ID))
        catalog = indexed.catalog
        hard = catalog.select(minimum=3000)
        require(len(hard) == 700, "The 3000+ stratum is incomplete.")
        selected = measure(metrics, "combined_filter_ms",
                           lambda: catalog.select(theme="middlegame", minimum=1350, maximum=2050))
        require(bool(selected), "The benchmark filter is empty.")
        sample = measure(metrics, "seeded_sample_ms", lambda: selected.sample_ids(20, seed=42))
        require(sample == selected.sample_ids(20, seed=42), "The seed did not reproduce the selected IDs.")
        puzzle = measure(metrics, "id_lookup_ms", lambda: catalog.get(sample[-1]))
        require(puzzle is not None and 1350 <= puzzle.rating <= 2050 and "middlegame" in puzzle.themes,
                "ID lookup did not return a matching puzzle.")
        require(catalog.content_identity(puzzle.puzzle_id) is not None, "The index has no content identity.")
        measure(metrics, "next_session_ms", lambda: PuzzleSession(selected[1]))
        save_settings(layout.settings, Settings(last_pack_id=PACK_ID))
        verify_native(layout, metrics)
        receipt = layout.root / "puzzle_packs-catalogs" / PACK_ID / "validated.json"
        index_hash = json.loads(receipt.read_text(encoding="utf-8"))["index"]
        index_file = receipt.with_name(f"{index_hash}.sqlite3")
        with index_file.open("rb") as data:
            require(hashlib.file_digest(data, "sha256").hexdigest() == index_hash, "Index SHA-256 mismatch.")
        metrics.update(matches=len(selected), puzzles=indexed.manifest.count, index_sha256=index_hash,
                       index_bytes=index_file.stat().st_size, profile=str(layout.root))
        try:
            import resource
        except ImportError:
            pass
        else:
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            metrics["peak_rss_bytes"] = rss if sys.platform == "darwin" else rss * 1024
    except (OSError, RuntimeError, ValueError, StopIteration) as error:
        parser.error(str(error))
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
