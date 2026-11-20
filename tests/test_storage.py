"""Storage tests. Every test writes only inside a temporary directory."""
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chess_and_chains.chess import ChessGame, DrawClaim, GameStatus, Move, parse_fen  # noqa: E402
from chess_and_chains.storage import (  # noqa: E402
    SCHEMA_VERSION,
    DataLayout,
    Database,
    Settings,
    SettingsError,
    StorageError,
    UnsafeDataPathError,
    default_data_dir,
    load_settings,
    save_settings,
    update_settings,
)
from chess_and_chains.storage.database import MIGRATIONS  # noqa: E402


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def open_db(self, name="db.sqlite3"):
        db = Database.open(self.tmp / name)
        self.addCleanup(db.close)
        return db


class PathTests(TempDirTestCase):
    def test_platform_defaults(self):
        home = Path("/home/u")
        self.assertEqual(default_data_dir("linux", {}, home), home / ".local/share/chess-and-chains")
        self.assertEqual(default_data_dir("linux", {"XDG_DATA_HOME": "/x"}, home), Path("/x/chess-and-chains"))
        self.assertEqual(default_data_dir("darwin", {}, home), home / "Library/Application Support/Chess and Chains")
        self.assertEqual(default_data_dir("win32", {"APPDATA": "C:/AppData"}, home), Path("C:/AppData/Chess and Chains"))
        self.assertEqual(default_data_dir("linux", {"CHESS_AND_CHAINS_DATA_DIR": "/d"}, home), Path("/d"))

    def test_refuses_package_and_checkout_locations(self):
        with self.assertRaises(UnsafeDataPathError):
            DataLayout(ROOT / "src" / "chess_and_chains" / "userdata")
        if (ROOT / ".git").exists():
            with self.assertRaises(UnsafeDataPathError):
                DataLayout(ROOT / "local-data")
        layout = DataLayout(self.tmp / "data")
        self.assertTrue(layout.root.is_dir())


class DatabaseTests(TempDirTestCase):
    def test_fresh_database_has_latest_schema(self):
        db = self.open_db()
        self.assertEqual(db.schema_version, SCHEMA_VERSION)
        self.assertIsNone(db.recovered_from)
        self.assertIsNone(db.migration_backup)

    def test_migration_from_v1_creates_backup_and_keeps_data(self):
        path = self.tmp / "old.sqlite3"
        conn = sqlite3.connect(path)
        conn.executescript(MIGRATIONS[0][1])
        conn.execute("PRAGMA user_version = 1")
        conn.execute("INSERT INTO puzzle_attempts (pack_id, puzzle_id, attempted_utc, solved, mistakes, hints_used)"
                     " VALUES ('demo', 'p1', '2026-01-01', 1, 0, 0)")
        conn.commit()
        conn.close()
        db = self.open_db("old.sqlite3")
        self.assertEqual(db.schema_version, SCHEMA_VERSION)
        self.assertIsNotNone(db.migration_backup)
        self.assertTrue(db.migration_backup.exists())
        self.assertEqual(db.puzzle_progress("demo", "p1").attempts, 1)
        backup = sqlite3.connect(db.migration_backup)
        self.assertEqual(backup.execute("PRAGMA user_version").fetchone()[0], 1)
        backup.close()

    def test_newer_schema_is_refused_without_modification(self):
        path = self.tmp / "future.sqlite3"
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA user_version = 99")
        conn.close()
        before = path.read_bytes()
        with self.assertRaises(StorageError):
            Database.open(path)
        self.assertEqual(path.read_bytes(), before)

    def test_corrupt_file_is_quarantined_not_deleted(self):
        path = self.tmp / "broken.sqlite3"
        garbage = b"this is not a database" * 100
        path.write_bytes(garbage)
        db = self.open_db("broken.sqlite3")
        self.assertIsNotNone(db.recovered_from)
        self.assertEqual(db.recovered_from.read_bytes(), garbage)
        self.assertEqual(db.schema_version, SCHEMA_VERSION)

    def test_save_load_validates_and_preserves_setup_position(self):
        db = self.open_db()
        game = ChessGame(parse_fen("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"))
        game.play(Move.from_uci("e2e4"))
        game.play(Move.from_uci("e8d7"))
        game_id = db.save_game(game, mode="human-vs-bot", bot_color="b", bot_name="Mock", bot_preset="level-1")
        saved = db.load_game(game_id)
        self.assertEqual(saved.moves, tuple(game.moves))
        self.assertEqual(saved.to_game().state, game.state)
        self.assertIn('[FEN "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"]', saved.pgn)
        self.assertEqual(saved.bot_preset, "level-1")

    def test_tampered_game_row_fails_validation(self):
        db = self.open_db()
        game = ChessGame()
        game.play(Move.from_uci("e2e4"))
        game_id = db.save_game(game, mode="human-vs-human")
        db._conn.execute("UPDATE games SET moves_uci = 'e2e5' WHERE id = ?", (game_id,))
        with self.assertRaises(StorageError):
            db.load_game(game_id)

    def test_load_rejects_mismatched_fen_result_and_invalid_uci(self):
        db = self.open_db()
        for column, value in (
            ("initial_fen", "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"),
            ("result", "1/2-1/2"),
            ("moves_uci", "e2"),
        ):
            with self.subTest(column=column):
                game_id = db.import_pgn("1. e4 *")
                db._conn.execute(f"UPDATE games SET {column} = ? WHERE id = ?", (value, game_id))
                with self.assertRaises(StorageError):
                    db.load_game(game_id)

    def test_pgn_import_export_keeps_result(self):
        db = self.open_db()
        game_id = db.import_pgn('[White "A"]\n[Result "1-0"]\n\n1. e4 e5 2. Qh5 Nc6 1-0')
        saved = db.load_game(game_id)
        self.assertEqual(saved.result, "1-0")
        self.assertIn('[White "A"]', saved.pgn)
        self.assertEqual(saved.to_game().outcome().status, GameStatus.RECORDED_RESULT)
        self.assertIn(("White", "A"), saved.pgn_tags)
        self.assertEqual(db.export_pgn([]), "")
        claimed = ChessGame()
        for uci in ("g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8"):
            claimed.play(Move.from_uci(uci))
        claimed.claim_draw(DrawClaim.THREEFOLD_REPETITION)
        db.save_game(claimed, mode="human-vs-human")
        exported = db.export_pgn()
        self.assertIn("1-0", exported)
        self.assertIn("1/2-1/2", exported)
        with self.assertRaises(Exception):
            db.import_pgn("1. e5 *")

    def test_backup_and_restore_round_trip(self):
        db = self.open_db()
        db.record_puzzle_attempt("demo", "a", solved=False, mistakes=1, hints_used=0, duration_ms=500)
        backup = db.backup(self.tmp / "backups" / "b1.sqlite3")
        db.record_puzzle_attempt("demo", "a", solved=True, mistakes=0, hints_used=0, duration_ms=300)
        self.assertEqual(db.puzzle_progress("demo", "a").attempts, 2)
        safety = db.restore(backup)
        self.assertTrue(safety.exists())
        self.assertEqual(db.puzzle_progress("demo", "a").attempts, 1)
        self.assertFalse(db.puzzle_progress("demo", "a").solved)
        (self.tmp / "junk.sqlite3").write_bytes(b"junk" * 200)
        with self.assertRaises(StorageError):
            db.restore(self.tmp / "junk.sqlite3")
        self.assertEqual(db.puzzle_progress("demo", "a").attempts, 1, "failed restore must not lose data")

    def test_puzzle_progress_and_statistics(self):
        db = self.open_db()
        db.record_puzzle_attempt("demo", "a", solved=False, mistakes=2, hints_used=0, duration_ms=900)
        db.record_puzzle_attempt("demo", "a", solved=True, mistakes=0, hints_used=1, duration_ms=700)
        db.record_puzzle_attempt("demo", "b", solved=True, mistakes=0, hints_used=0, duration_ms=400)
        progress = db.puzzle_progress("demo", "a")
        self.assertEqual((progress.attempts, progress.solved, progress.clean_solves, progress.best_duration_ms),
                         (2, True, 0, 700))
        self.assertEqual(db.solved_puzzle_ids("demo"), {"a", "b"})
        stats = db.statistics()
        self.assertEqual((stats.puzzles_attempted, stats.puzzles_solved, stats.puzzles_clean), (2, 2, 1))
        with self.assertRaises(sqlite3.IntegrityError):
            db.record_puzzle_attempt("demo", "c", solved=True, mistakes=-1, hints_used=0, duration_ms=1)


class SettingsTests(TempDirTestCase):
    def test_defaults_round_trip_and_atomic_write(self):
        path = self.tmp / "settings.json"
        settings, warning = load_settings(path)
        self.assertEqual(settings, Settings())
        self.assertIsNone(warning)
        update_settings(path, locale="de", bot_preset_id="level-5", engine_path="/opt/engine")
        loaded, warning = load_settings(path)
        self.assertEqual((loaded.locale, loaded.bot_preset_id, loaded.engine_path), ("de", "level-5", "/opt/engine"))
        self.assertEqual([p.name for p in self.tmp.iterdir()], ["settings.json"])

    def test_invalid_file_is_quarantined_and_defaults_used(self):
        path = self.tmp / "settings.json"
        path.write_text("{ not json")
        settings, warning = load_settings(path)
        self.assertEqual(settings, Settings())
        self.assertIn("defaults loaded", warning)
        quarantined = list(self.tmp.glob("settings.json.invalid-*"))
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(quarantined[0].read_text(), "{ not json")

    def test_invalid_values_are_rejected_and_unknown_keys_ignored(self):
        path = self.tmp / "settings.json"
        with self.assertRaises(SettingsError):
            save_settings(path, Settings(locale="fr"))
        with self.assertRaises(SettingsError):
            update_settings(path, play_mode="online")
        path.write_text(json.dumps({"schema_version": 1, "locale": "en", "future_key": 1}))
        settings, warning = load_settings(path)
        self.assertEqual(settings.locale, "en")
        self.assertIsNone(warning)


if __name__ == "__main__":
    unittest.main()
