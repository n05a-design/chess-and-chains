"""Deterministic Fischer clock tests.

SPDX-License-Identifier: MPL-2.0
"""
import unittest

from chess_and_chains.chess import ChessError, ChessGame, Color, GameStatus, IllegalMoveError, MatePossibility, Move, parse_fen
from chess_and_chains.chess.mating import prove_mate_possibility
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

    def test_flag_draw_when_only_reply_captures_the_other_sides_rook(self):
        self.start("8/8/8/8/4R3/8/r1k5/K7 w - - 0 1")
        self.assertEqual(self.controller.game.rules.legal_moves(self.controller.game.state),
                         (Move.from_uci("a1a2"),))
        self.now = 1_000_000_000
        self.assertTrue(self.controller.poll())
        self.assertIs(self.controller.game.outcome().status, GameStatus.RECORDED_RESULT)
        self.assertIsNone(self.controller.game.outcome().winner)
        self.assertEqual(self.controller.game.moves, [])

    def test_flag_win_when_a_legal_mating_line_exists(self):
        self.start("7k/8/5K2/6Q1/8/8/8/8 b - - 148 1")
        self.now = 1_000_000_000
        self.assertTrue(self.controller.poll())
        self.assertEqual(self.controller.view().flagged, Color.BLACK)
        self.assertEqual(self.controller.game.outcome().winner, Color.WHITE)
        self.assertEqual(self.controller.game.moves, [])

    def test_cooperative_mate_does_not_continue_past_an_automatic_draw(self):
        game = ChessGame(parse_fen("7k/8/5K2/6Q1/8/8/8/8 b - - 149 1"))
        self.assertIs(game.mate_possibility(Color.WHITE), MatePossibility.UNKNOWN)
        game = ChessGame(parse_fen("7k/8/5K2/6Q1/8/8/8/8 b - - 0 1"))
        child = game.rules.apply(game.state, Move.from_uci("h8h7"))
        seen = {game.rules.position_key(child): 4}
        self.assertIs(prove_mate_possibility(game.state, Color.WHITE, game.rules, seen), MatePossibility.UNKNOWN)
        self.assertEqual(seen[game.rules.position_key(child)], 4)

    def test_proof_leaves_history_intact_and_recognizes_two_knights(self):
        game = ChessGame(parse_fen("k7/2K5/2N5/3N4/8/8/8/8 w - - 0 1"))
        game.play_uci("d5b6")
        game.undo()
        timeline = game.timeline()
        self.assertIs(game.mate_possibility(Color.WHITE), MatePossibility.POSSIBLE)
        self.assertEqual(game.timeline(), timeline)
        game.redo()
        self.assertIs(game.outcome().status, GameStatus.CHECKMATE)

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
