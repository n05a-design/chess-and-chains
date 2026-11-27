"""Session recovery tests using only temporary SQLite databases.

SPDX-License-Identifier: MPL-2.0
"""
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from chess_and_chains.chess import ChessGame, Color, GameStatus, parse_fen, to_fen
from chess_and_chains.game import GameSetup
from chess_and_chains.game.session import GameSessionSnapshot, SessionLifecycle
from chess_and_chains.storage import Database, SessionConflict, StorageError


def snapshot_of(game, setup=GameSetup.two_players(), **overrides):
    now = "2026-11-27T12:00:00+00:00"
    return replace(
        GameSessionSnapshot(
            str(uuid4()), now, now, setup, to_fen(game.initial_state), game.timeline(),
            SessionLifecycle.ACTIVE if game.outcome().status is GameStatus.ACTIVE else SessionLifecycle.FINISHED,
        ),
        **overrides,
    )


class GameSessionTests(unittest.TestCase):
    def setUp(self):
        self.directory = self.enterContext(TemporaryDirectory())
        self.path = Path(self.directory) / "games.db"

    def test_session_survives_reopen_and_retains_redo_after_promotion(self):
        game = ChessGame(parse_fen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1"))
        game.play_uci("a7a8r")
        promoted = game.state
        game.undo()
        snapshot = snapshot_of(game, GameSetup.against_bot(Color.WHITE), engine_ref="mock", bot_preset="level-3")
        with Database.open(self.path) as db:
            db.save_session(snapshot)
            self.assertEqual(db.list_games(), [])
        with Database.open(self.path) as db:
            loaded, restored = db.load_session()
        self.assertEqual(loaded, snapshot)
        self.assertEqual(restored.state, game.initial_state)
        self.assertTrue(restored.can_redo)
        self.assertEqual(restored.redo(), promoted)

    def test_redo_restores_explicit_termination(self):
        game = ChessGame()
        game.play_uci("e2e4")
        game.resign(Color.WHITE)
        finished = snapshot_of(game)
        self.assertIs(finished.restore_game().outcome().status, GameStatus.RESIGNED)
        game.undo()
        restored = snapshot_of(game).restore_game()
        self.assertIs(restored.outcome().status, GameStatus.ACTIVE)
        restored.redo()
        self.assertIs(restored.outcome().status, GameStatus.RESIGNED)
        self.assertEqual(restored.outcome().resigned_by, Color.WHITE)

    def test_failed_overwrite_keeps_previous_snapshot(self):
        game = ChessGame()
        snapshot = snapshot_of(game)
        with Database.open(self.path) as db:
            db.save_session(snapshot)
            with self.assertRaises(sqlite3.IntegrityError):
                db.save_session(replace(snapshot, headers=(("Event", "x" * 262144),)))
            self.assertEqual(db.load_session()[0], snapshot)

    def test_other_instance_cannot_overwrite_a_newer_active_checkpoint(self):
        game = ChessGame()
        original = snapshot_of(game)
        with Database.open(self.path) as first, Database.open(self.path) as second:
            original_payload = first.compare_and_save_session(original, None)
            stale_payload = second.session_payload()
            game.play_uci("e2e4")
            newer = replace(original, timeline=game.timeline())
            first.compare_and_save_session(newer, original_payload)
            with self.assertRaises(SessionConflict):
                second.compare_and_save_session(original, stale_payload)
            with self.assertRaises(SessionConflict):
                second.compare_and_save_session(original, None)
            self.assertEqual(second.load_session()[0], newer)

    def test_restore_rejects_archived_snapshot_for_another_game(self):
        live = ChessGame()
        live.play_uci("d2d4")
        source = self.path.with_name("backup.db")
        archived = ChessGame()
        archived.play_uci("e2e4")
        with Database.open(source) as candidate:
            row = candidate.save_game(archived, mode="human-vs-human", session_snapshot=snapshot_of(archived))
            candidate._conn.execute("UPDATE games SET session_snapshot = ? WHERE id = ?",
                                    (snapshot_of(live).encode(), row))
        with Database.open(self.path) as db:
            saved_id = db.save_game(live, mode="human-vs-human")
            with self.assertRaisesRegex(StorageError, "Archive session differs"):
                db.restore(source)
            self.assertEqual(db.load_game(saved_id).moves, tuple(live.moves))

    def test_abrupt_process_exit_leaves_previous_committed_snapshot(self):
        game = ChessGame()
        game.play_uci("e2e4")
        original = snapshot_of(game)
        with Database.open(self.path) as db:
            db.save_session(original)

        code = """
import os
from pathlib import Path
import sys
from chess_and_chains.storage import Database
db = Database.open(Path(sys.argv[1]))
db._conn.execute('BEGIN IMMEDIATE')
db._conn.execute('UPDATE active_session SET snapshot = ?', ('incomplete',))
os._exit(17)
"""
        child = subprocess.run((sys.executable, "-c", code, str(self.path)), check=False, timeout=10)
        self.assertEqual(child.returncode, 17)
        with Database.open(self.path) as db:
            self.assertEqual(db.load_session()[0], original)

    def test_backup_rejects_bad_snapshot_and_keeps_the_live_session(self):
        snapshot = snapshot_of(ChessGame())
        for field, value in (("schema", 99), ("cursor", 4), ("moves", ["e2e5"]), ("fen", None)):
            with self.subTest(field=field):
                backup = Path(self.directory) / f"{field}.db"
                with Database.open(self.path) as db:
                    db.save_session(snapshot)
                    db.backup(backup)
                    payload = json.loads(snapshot.encode())
                    payload[field] = value
                    with sqlite3.connect(backup) as corrupt:
                        corrupt.execute("UPDATE active_session SET snapshot = ?", (json.dumps(payload),))
                    corrupt.close()
                    with self.assertRaises(StorageError):
                        db.restore(backup)
                    self.assertEqual(db.load_session()[0], snapshot)


if __name__ == "__main__":
    unittest.main()
