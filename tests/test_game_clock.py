"""Deterministic Fischer clock tests.

SPDX-License-Identifier: MPL-2.0
"""
import unittest

from chess_and_chains.chess import ChessError, Color, GameStatus, IllegalMoveError, Move
from chess_and_chains.game import GameController, GameSetup
from chess_and_chains.game.clock import GameClock, TimeControl


class GameClockTests(unittest.TestCase):
    def setUp(self):
        self.time = 0
        self.clock = GameClock(TimeControl(1000, 200), Color.WHITE, now=lambda: self.time)

    def test_switch_and_fischer_increment_at_accepted_move(self):
        self.clock.resume()
        self.time = 250_000_000
        self.assertTrue(self.clock.complete_move(self.clock.sample_time()))
        self.time += 400_000_000
        reading = self.clock.reading()
        self.assertEqual(reading.turn, Color.BLACK)
        self.assertEqual(reading.remaining_ms(Color.WHITE), 950)
        self.assertEqual(reading.remaining_ms(Color.BLACK), 600)

    def test_exact_deadline_flags_and_last_nanosecond_can_play(self):
        self.clock.resume()
        self.assertEqual(self.clock.reading(999_999_999).remaining_ms(Color.WHITE), 1)
        self.assertTrue(self.clock.complete_move(999_999_999))
        self.assertFalse(self.clock.complete_move(1_999_999_999))
        self.assertEqual(self.clock.reading().remaining_ms(Color.BLACK), 0)
        self.clock.resume()
        self.assertFalse(self.clock.running)

    def test_resume_holds_saved_times_until_explicit_start(self):
        self.clock.resume()
        self.time = 300_000_000
        saved = self.clock.pause()
        self.time += 20_000_000_000
        clock = GameClock(self.clock.control, Color.WHITE, now=lambda: self.time)
        clock.restore_paused(saved)
        self.assertEqual(clock.reading(), saved)
        clock.resume()
        self.time += 200_000_000
        self.assertEqual(clock.pause().remaining_ms(Color.WHITE), 500)



class TimedGameControllerTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.controller = GameController(now=lambda: self.now)
        self.addCleanup(self.controller.shutdown)
        self.control = TimeControl(1000, 200)

    def start(self, fen=None):
        self.controller.new_game(GameSetup(initial_fen=fen, time_control=self.control))

    def test_illegal_move_does_not_switch_clock_and_deadline_beats_move(self):
        self.start()
        self.now = 250_000_000
        with self.assertRaises(IllegalMoveError):
            self.controller.play_human(Move.from_uci("e2e5"))
        self.assertEqual(self.controller.clock_reading().remaining_ms(Color.WHITE), 750)
        self.now = 1_000_000_000
        with self.assertRaises(ChessError):
            self.controller.play_human(Move.from_uci("e2e4"))
        self.assertEqual(self.controller.game.moves, [])
        self.assertEqual(self.controller.view().flagged, Color.WHITE)
        self.assertIs(self.controller.game.outcome().status, GameStatus.ACTIVE)
        self.assertFalse(self.controller.view().human_to_move)
        self.controller.adjudicate_timeout(draw=False)
        self.assertEqual(self.controller.game.outcome().winner, Color.BLACK)

    def test_flag_draw_is_automatic_for_opposing_lone_king(self):
        self.start("4k3/8/8/8/8/8/8/4K2R w - - 0 1")
        self.now = 1_000_000_000
        self.assertTrue(self.controller.poll())
        self.assertEqual(self.controller.view().flagged, Color.WHITE)
        self.assertIs(self.controller.game.outcome().status, GameStatus.RECORDED_RESULT)
        self.assertIsNone(self.controller.game.outcome().winner)

    def test_undo_redo_restore_position_times_and_pause_clock(self):
        self.start()
        self.now = 999_999_999
        self.controller.play_human(Move.from_uci("e2e4"))
        accepted = self.controller.clock_reading()
        self.now = 1_100_000_000
        self.controller.undo()
        self.assertFalse(self.controller.view().clock_running)
        self.assertEqual(self.controller.clock_reading().remaining_ms(Color.WHITE), 1000)
        self.controller.redo()
        self.assertEqual(self.controller.clock_reading(), accepted)
        self.now += 60_000_000_000
        self.assertEqual(self.controller.clock_reading(), accepted)
        self.controller.toggle_clock()
        self.assertTrue(self.controller.view().clock_running)
