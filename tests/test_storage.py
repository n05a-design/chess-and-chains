"""Storage tests. Every test writes only inside a temporary directory."""
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chess_and_chains.chess import ChessGame, Color, DrawClaim, FenError, GameStatus, Move, PGNError, parse_fen, to_fen  # noqa: E402
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
from chess_and_chains.storage.database import MAX_PGN_FILE_BYTES, MIGRATIONS  # noqa: E402
from chess_and_chains.storage.exchange import (  # noqa: E402
    MAX_FEN_FILE_BYTES, parse_fen_text, read_fen_file, write_fen_file,
)


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

    def test_old_records_replay_and_keep_their_result_in_newly_dead_positions(self):
        db = self.open_db()
        for movetext, moves_uci, result, resigned, draw_claim, expected in (
            ("1. Kxa2 1/2-1/2", "a1a2", "1/2-1/2", None, None, GameStatus.DRAW_INSUFFICIENT_MATERIAL),
            ("0-1", "", "0-1", "w", None, GameStatus.RESIGNED),
            ("0-1", "", "0-1", None, None, GameStatus.RECORDED_RESULT),
            ("1/2-1/2", "", "1/2-1/2", None, "FIFTY_MOVE_RULE", GameStatus.DRAW_CLAIMED),
            ("*", "", "*", None, None, GameStatus.DRAW_DEAD_POSITION),
        ):
            with self.subTest(movetext=movetext, resigned=resigned, draw_claim=draw_claim):
                clock = 100 if draw_claim else 0
                fen = f"8/8/8/8/8/8/r1k5/K7 w - - {clock} 1"
                pgn = f'[SetUp "1"]\n[FEN "{fen}"]\n[Result "{result}"]\n\n{movetext}\n'
                inserted = db._conn.execute(
                    "INSERT INTO games (created_utc, initial_fen, moves_uci, pgn, result, mode, resigned_by, draw_claim)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    ("2026-11-20", fen, moves_uci, pgn, result, "human-vs-human", resigned, draw_claim),
                )
                saved = db.load_game(inserted.lastrowid)
                game = saved.to_game()
                self.assertEqual(saved.pgn, pgn)
                self.assertEqual(saved.result, result)
                self.assertEqual([move.to_uci() for move in game.moves], moves_uci.split())
                outcome = game.outcome()
                self.assertIs(outcome.status, expected)
                self.assertIs(outcome.winner, Color.BLACK if result == "0-1" else None)
                self.assertIs(outcome.resigned_by, Color.WHITE if resigned else None)
                self.assertIs(outcome.claimed_draw, DrawClaim.FIFTY_MOVE_RULE if draw_claim else None)

    def test_saving_a_new_dead_position_keeps_the_automatic_draw(self):
        db = self.open_db()
        game = ChessGame(parse_fen("8/8/8/8/8/8/1rk5/K7 b - - 0 1"))
        game.play_uci("b2a2")
        saved = db.load_game(db.save_game(game, mode="human-vs-human"))
        self.assertEqual(saved.result, "1/2-1/2")
        self.assertEqual(saved.moves, (Move.from_uci("b2a2"),))
        self.assertIs(saved.to_game().outcome().status, GameStatus.DRAW_DEAD_POSITION)

    def test_old_record_can_replay_two_forced_moves_through_a_dead_position(self):
        db = self.open_db()
        # ECU arbiter's numeric reference position after Nc2+.
        fen = "R7/7q/8/8/1p6/1P2p3/p1N1P3/k1K5 b - - 1 48"
        pgn = f'[SetUp "1"]\n[FEN "{fen}"]\n[Result "1/2-1/2"]\n\n48... Qxc2+ 49. Kxc2 1/2-1/2'
        saved = db.load_game(db.import_pgn(pgn))
        self.assertEqual(saved.moves, (Move.from_uci("h7c2"), Move.from_uci("c1c2")))
        self.assertEqual(saved.result, "1/2-1/2")
        game = saved.to_game()
        self.assertIs(game.outcome().status, GameStatus.STALEMATE)
        game.undo()
        game.undo()
        self.assertIs(game.outcome().status, GameStatus.DRAW_DEAD_POSITION)
        game.redo()
        game.redo()
        self.assertIs(game.outcome().status, GameStatus.STALEMATE)

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

    def test_v2_games_and_backup_keep_generic_results(self):
        path = self.tmp / "v2.sqlite3"
        conn = sqlite3.connect(path)
        for version, script in MIGRATIONS[:2]:
            conn.executescript(script)
            conn.execute(f"PRAGMA user_version = {version}")
        conn.execute(
            "INSERT INTO games (created_utc, initial_fen, moves_uci, pgn, result, mode)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            ("2026-01-01", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
             "e2e4", "1. e4 0-1", "0-1", "human-vs-human"),
        )
        conn.commit()
        conn.close()
        db = self.open_db(path.name)
        untouched = db.migration_backup
        with sqlite3.connect(untouched) as backup:
            self.assertEqual(backup.execute("PRAGMA user_version").fetchone()[0], 2)
        backup.close()
        self.assertEqual(db.schema_version, SCHEMA_VERSION)
        db.restore(untouched)
        self.assertEqual(db.schema_version, SCHEMA_VERSION)
        game = db.load_game(1).to_game()
        self.assertEqual(game.outcome().status, GameStatus.RECORDED_RESULT)
        self.assertEqual(game.outcome().winner, Color.BLACK)
        self.assertIsNone(game.outcome().resigned_by)

    def test_rechecking_schema_after_lock_skips_an_applied_migration(self):
        db = self.open_db()
        Database._migrate(db._conn, 2)
        self.assertEqual(db.schema_version, SCHEMA_VERSION)

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

    def test_termination_metadata_round_trips_without_adding_the_declared_move(self):
        db = self.open_db()
        repetition = ChessGame()
        for uci in ("g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1"):
            repetition.play_uci(uci)
        repetition.claim_draw(DrawClaim.THREEFOLD_REPETITION, Move.from_uci("f6g8"))
        fifty = ChessGame(parse_fen("4k3/8/8/8/8/8/8/R3K3 w - - 100 51"))
        fifty.claim_draw(DrawClaim.FIFTY_MOVE_RULE)
        resignation = ChessGame(parse_fen("4k3/8/8/8/8/8/4P3/4K3 b - - 0 1"))
        resignation.resign(Color.WHITE)
        for game in (repetition, fifty, resignation):
            with self.subTest(outcome=game.outcome()):
                game_id = db.save_game(game, mode="human-vs-human")
                reopened = db.load_game(game_id).to_game()
                self.assertEqual(reopened.outcome(), game.outcome())
                self.assertEqual(reopened.moves, game.moves)
                reopened.undo()
                self.assertIs(reopened.outcome().status, GameStatus.ACTIVE)
                reopened.redo()
                self.assertEqual(reopened.outcome(), game.outcome())

    def test_load_rejects_claim_or_resignation_that_conflicts_with_the_record(self):
        db = self.open_db()
        claimed = ChessGame(parse_fen("4k3/8/8/8/8/8/8/R3K3 w - - 100 51"))
        claimed.claim_draw(DrawClaim.FIFTY_MOVE_RULE)
        claimed_id = db.save_game(claimed, mode="human-vs-human")
        db._conn.execute("UPDATE games SET draw_claim = 'THREEFOLD_REPETITION' WHERE id = ?", (claimed_id,))
        with self.assertRaisesRegex(StorageError, "not claimable"):
            db.load_game(claimed_id)

        resigned = ChessGame()
        resigned.resign(Color.WHITE)
        with self.assertRaisesRegex(ValueError, "contradicts"):
            db.save_game(resigned, mode="human-vs-human", result="1-0")
        resigned_id = db.save_game(resigned, mode="human-vs-human")
        db._conn.execute("UPDATE games SET resigned_by = 'b' WHERE id = ?", (resigned_id,))
        with self.assertRaisesRegex(StorageError, "contradicts"):
            db.load_game(resigned_id)

    def test_pgn_file_round_trip_preserves_utf8_tags_fen_and_result(self):
        db = self.open_db()
        source, target = self.tmp / "Quelle.pgn", self.tmp / "kopie.pgn"
        source.write_text(
            '[Event "Frühling"]\n[SetUp "1"]\n[FEN "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"]\n\n1. e4 1/2-1/2',
            encoding="utf-8-sig",
        )
        game_id = db.import_pgn_file(source)
        db.export_pgn_file(game_id, target)
        copied = db.load_game(db.import_pgn_file(target))
        original = db.load_game(game_id)
        self.assertEqual(copied.pgn_tags, original.pgn_tags)
        self.assertEqual(copied.moves, original.moves)
        self.assertEqual(copied.result, "1/2-1/2")

    def test_pgn_file_rejects_bad_input_without_inserting(self):
        db = self.open_db()
        source = self.tmp / "invalid.pgn"
        for payload, error in (
            (b"", StorageError),
            (b"\xff", UnicodeDecodeError),
            (b"1. e5 *", PGNError),
            (b"1. e4 *\n\n1. d4 *", PGNError),
            (b" " * (MAX_PGN_FILE_BYTES + 1), StorageError),
        ):
            with self.subTest(error=error), self.assertRaises(error):
                source.write_bytes(payload)
                db.import_pgn_file(source)
        source.write_bytes(b"1. e4 e5 *")
        with patch("chess_and_chains.storage.database.MAX_PGN_FILE_PLIES", 1):
            with self.assertRaisesRegex(PGNError, "1 half-moves"):
                db.import_pgn_file(source)
        self.assertEqual(db.list_games(), [])

    def test_pgn_export_failure_keeps_existing_file(self):
        db = self.open_db()
        game_id = db.import_pgn("1. e4 *")
        target = self.tmp / "saved.pgn"
        target.write_text("Keep this", encoding="utf-8")
        with patch.object(Path, "replace", side_effect=PermissionError("test rename failure")):
            with self.assertRaises(PermissionError):
                db.export_pgn_file(game_id, target)
        self.assertEqual(target.read_text(encoding="utf-8"), "Keep this")
        self.assertEqual(list(self.tmp.glob(".pgn-*")), [])

    def test_backup_and_restore_round_trip(self):
        db = self.open_db()
        game_id = db.import_pgn("1. e4 e5 *")
        db.record_puzzle_attempt("demo", "a", solved=False, mistakes=1, hints_used=0, duration_ms=500)
        backup = db.backup(self.tmp / "backups" / "b1.sqlite3")
        backup_before = backup.read_bytes()
        newer_id = db.import_pgn("1. d4 d5 *")
        db.record_puzzle_attempt("demo", "a", solved=True, mistakes=0, hints_used=0, duration_ms=300)
        self.assertEqual(db.puzzle_progress("demo", "a").attempts, 2)
        safety = db.restore(backup)
        self.assertTrue(safety.exists())
        self.assertEqual(backup.read_bytes(), backup_before)
        self.assertEqual([row[0] for row in db.list_games()], [game_id])
        self.assertEqual(db.load_game(game_id).moves, (Move.from_uci("e2e4"), Move.from_uci("e7e5")))
        with Database.open(safety) as previous:
            self.assertEqual([row[0] for row in previous.list_games()], [newer_id, game_id])
            self.assertTrue(previous.puzzle_progress("demo", "a").solved)
        self.assertEqual(db.puzzle_progress("demo", "a").attempts, 1)
        self.assertFalse(db.puzzle_progress("demo", "a").solved)
        (self.tmp / "junk.sqlite3").write_bytes(b"junk" * 200)
        with self.assertRaises(StorageError):
            db.restore(self.tmp / "junk.sqlite3")
        self.assertEqual(db.puzzle_progress("demo", "a").attempts, 1, "failed restore must not lose data")

    def test_restore_rejects_missing_foreign_or_malformed_backup_without_touching_live_data(self):
        db = self.open_db()
        game_id = db.import_pgn("1. e4 *")
        missing = self.tmp / "missing.sqlite3"
        foreign = self.tmp / "foreign.sqlite3"
        malformed = self.tmp / "malformed.sqlite3"
        for path, sql in ((foreign, "CREATE TABLE notes (text)"), (malformed, f"PRAGMA user_version={SCHEMA_VERSION}")):
            with sqlite3.connect(path) as connection:
                connection.execute(sql)
            connection.close()
        for path in (missing, foreign, malformed):
            with self.subTest(path=path), self.assertRaises(StorageError):
                db.restore(path)
        self.assertFalse(missing.exists())
        self.assertEqual(db.load_game(game_id).moves, (Move.from_uci("e2e4"),))
        with self.assertRaises(StorageError):
            db.backup(db.path)
        self.assertEqual(db.statistics().games_saved, 1)

    def test_restore_rejects_inconsistent_game_records_before_replacing_the_active_database(self):
        for name, change in (
            ("moves", "UPDATE games SET moves_uci = 'g1f3'"),
            ("termination", "UPDATE games SET result = '1-0', pgn = '1. d4 1-0', resigned_by = 'w'"),
        ):
            with self.subTest(name=name):
                db = self.open_db(f"live-{name}.sqlite3")
                game_id = db.import_pgn("1. e4 *")
                db.record_puzzle_attempt("demo", "a", solved=True, mistakes=0, hints_used=0, duration_ms=400)
                source = self.tmp / f"candidate-{name}.sqlite3"
                with Database.open(source) as candidate:
                    damaged_id = candidate.import_pgn("1. d4 *")
                    candidate._conn.execute(change)
                source_before = source.read_bytes()
                live_before = db.path.read_bytes()

                with self.assertRaisesRegex(StorageError, f"Cannot restore backup .*Saved game {damaged_id}"):
                    db.restore(source)

                self.assertEqual(source.read_bytes(), source_before)
                self.assertEqual(db.path.read_bytes(), live_before)
                self.assertEqual(db.load_game(game_id).moves, (Move.from_uci("e2e4"),))
                self.assertEqual(db.solved_puzzle_ids("demo"), {"a"})
                self.assertEqual(list(self.tmp.glob(f"{db.path.name}.pre-restore-*.bak")), [])
                self.assertEqual(list(self.tmp.glob(".restore-*")), [])

    def test_restore_preserves_live_data_when_the_safety_copy_cannot_be_written(self):
        db = self.open_db()
        game_id = db.import_pgn("1. e4 *")
        source = db.backup(self.tmp / "previous.sqlite3")
        db.import_pgn("1. d4 *")
        before = db.path.read_bytes()
        with patch.object(Path, "replace", side_effect=PermissionError("test write protection")):
            with self.assertRaisesRegex(StorageError, "test write protection"):
                db.restore(source)
        self.assertEqual(db.path.read_bytes(), before)
        self.assertEqual(db.load_game(game_id).moves, (Move.from_uci("e2e4"),))
        self.assertEqual(db.statistics().games_saved, 2)
        self.assertEqual(list(self.tmp.glob(f".{db.path.name}.pre-restore-*")), [])
        self.assertEqual(list(self.tmp.glob(".restore-*")), [])

    def test_interrupted_restore_rolls_back_the_live_copy_and_keeps_the_safety_backup(self):
        db = self.open_db()
        original_id = db.import_pgn("1. e4 *")
        source = db.backup(self.tmp / "previous.sqlite3")
        newer_id = db.import_pgn("1. d4 *")
        connect = sqlite3.connect

        class InterruptedCopy(sqlite3.Connection):
            def backup(self, target):
                def interrupt(_status, remaining, _total):
                    if remaining:
                        raise sqlite3.OperationalError("test interruption during live copy")

                super().backup(target, pages=1, progress=interrupt)

        def connect_with_interruption(path, **kwargs):
            if Path(path).name == "staged.sqlite3":
                kwargs["factory"] = InterruptedCopy
            return connect(path, **kwargs)

        before = db.path.read_bytes()
        with patch("chess_and_chains.storage.database.sqlite3.connect", side_effect=connect_with_interruption):
            with self.assertRaisesRegex(StorageError, "test interruption during live copy"):
                db.restore(source)
        self.assertEqual(db.path.read_bytes(), before)
        self.assertEqual(db.load_game(original_id).moves, (Move.from_uci("e2e4"),))
        self.assertEqual(db.load_game(newer_id).moves, (Move.from_uci("d2d4"),))
        safety_path, = self.tmp.glob(f"{db.path.name}.pre-restore-*.bak")
        with Database.open(safety_path) as safety:
            self.assertEqual(safety.list_games(), db.list_games())
        self.assertEqual(list(self.tmp.glob(".restore-*")), [])

    def test_open_does_not_quarantine_on_transient_database_error(self):
        path = self.tmp / "untouched.sqlite3"
        with Database.open(path):
            pass
        before = path.read_bytes()
        with patch.object(Database, "_connect_checked", side_effect=sqlite3.OperationalError("database is locked")):
            with self.assertRaisesRegex(StorageError, "database is locked"):
                Database.open(path)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(list(path.parent.glob("*.corrupt-*")), [])

    def test_training_candidate_is_validated_deduplicated_and_restored(self):
        from chess_and_chains.puzzles.training import TrainingCandidate

        db = self.open_db()
        game = ChessGame()
        game.play_uci("e2e4")
        game_id = db.save_game(game, mode="human-vs-human")
        original = db.load_game(game_id)
        candidate = TrainingCandidate(game_id, 0, to_fen(game.initial_state))
        db.save_training_candidate(candidate)
        db.save_training_candidate(candidate)
        with self.assertRaises(StorageError):
            db.save_training_candidate(TrainingCandidate(game_id, 1, candidate.fen))
        self.assertEqual(db.training_candidates(), (candidate,))
        backup = self.tmp / "training-backup.sqlite3"
        db.backup(backup)
        db.delete_game(game_id)
        self.assertEqual(db.training_candidates(), ())
        db.restore(backup)
        self.assertEqual(db.training_candidates(), (candidate,))
        self.assertEqual(db.load_game(game_id), original)

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


class PositionFileTests(TempDirTestCase):
    FEN = "r3k2r/8/8/8/3pP3/8/8/R3K2R b KQkq e3 0 17"

    def test_fen_file_round_trip_keeps_turn_castling_en_passant_and_counters(self):
        source, target = self.tmp / "source.fen", self.tmp / "target.FEN"
        source.write_bytes(f"  {self.FEN}\r\n".encode("utf-8-sig"))
        position = read_fen_file(source)
        self.assertEqual(position, parse_fen(self.FEN))
        write_fen_file(position, target)
        self.assertEqual(target.read_bytes(), f"{self.FEN}\n".encode("ascii"))
        self.assertEqual(read_fen_file(target), position)

    def test_fen_files_reject_large_invalid_and_multi_position_inputs(self):
        source = self.tmp / "source.fen"
        for data, error in (
            (b" " * (MAX_FEN_FILE_BYTES + 1), FenError),
            (b"\xff", UnicodeDecodeError),
            (b"\0" + self.FEN.encode(), FenError),
            (f"{self.FEN}\n{self.FEN}".encode(), FenError),
            (b"8/8/8/8/8/8/8/8 w - - 0 1", FenError),
        ):
            with self.subTest(size=len(data), prefix=data[:8]):
                source.write_bytes(data)
                with self.assertRaises(error):
                    read_fen_file(source)
        with self.assertRaises(FenError):
            read_fen_file(self.tmp)
        with self.assertRaises(FenError):
            parse_fen_text(" " * MAX_FEN_FILE_BYTES + self.FEN)

    def test_failed_fen_export_preserves_existing_file_and_removes_staging_file(self):
        position = parse_fen(self.FEN)
        target = self.tmp / "old.fen"
        target.write_bytes(b"existing file")
        with patch.object(Path, "replace", side_effect=PermissionError("test rename failure")):
            with self.assertRaises(PermissionError):
                write_fen_file(position, target)
        with self.assertRaises(FenError):
            write_fen_file(position, self.tmp / "old.pgn")
        self.assertEqual(target.read_bytes(), b"existing file")
        self.assertEqual(list(self.tmp.iterdir()), [target])


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
