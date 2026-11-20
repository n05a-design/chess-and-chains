"""Focused geometry and legal-move tests for the board interaction layer."""
import sys
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from chess_and_chains.chess import (  # noqa: E402
    ChessRules,
    GameStatus,
    Move,
    PieceType,
    parse_fen,
    parse_square,
)
from chess_and_chains.ui.app import ChessApp  # noqa: E402
from tests.tk_support import create_root  # noqa: E402
from chess_and_chains.ui.board import (  # noqa: E402
    BoardCanvas,
    moves_between,
    screen_cell,
    square_at_point,
)


class BoardGeometryTests(unittest.TestCase):
    def test_orientation_maps_board_corners(self):
        self.assertEqual(square_at_point(0, 0, 0, 0, 10, "white"), parse_square("a8"))
        self.assertEqual(square_at_point(79, 79, 0, 0, 10, "white"), parse_square("h1"))
        self.assertEqual(square_at_point(0, 0, 0, 0, 10, "black"), parse_square("h1"))
        self.assertEqual(square_at_point(79, 79, 0, 0, 10, "black"), parse_square("a8"))

    def test_points_outside_the_board_do_not_map_to_squares(self):
        self.assertIsNone(square_at_point(-1, 0, 0, 0, 10))
        self.assertIsNone(square_at_point(80, 10, 0, 0, 10))
        self.assertIsNone(square_at_point(10, 10, 0, 0, 0))

    def test_domain_square_round_trips_through_each_orientation(self):
        for orientation in ("white", "black"):
            for square in range(64):
                column, row = screen_cell(square, orientation)
                self.assertEqual(
                    square_at_point(column * 10 + 5, row * 10 + 5, 0, 0, 10, orientation),
                    square,
                )


class BoardMoveTests(unittest.TestCase):
    def test_only_domain_legal_moves_are_available_to_the_board(self):
        rules = ChessRules()
        legal = rules.legal_moves(rules.initial_state())
        self.assertEqual(
            moves_between(legal, parse_square("e2"), parse_square("e4")),
            (Move(parse_square("e2"), parse_square("e4")),),
        )
        self.assertEqual(
            moves_between(legal, parse_square("e2"), parse_square("e5")),
            (),
        )

    def test_promotion_keeps_all_domain_candidates_for_dialog(self):
        rules = ChessRules()
        state = parse_fen("7k/P7/8/8/8/8/8/7K w - - 0 1")
        candidates = moves_between(
            rules.legal_moves(state), parse_square("a7"), parse_square("a8")
        )
        self.assertEqual(
            {move.promotion for move in candidates},
            {PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT},
        )


class BoardInputTests(unittest.TestCase):
    def setUp(self):
        self.root = create_root(self)
        self.root.withdraw()
        self.requested = []
        self.board = BoardCanvas(self.root, self.requested.append)
        self.rules = ChessRules()
        self.state = self.rules.initial_state()
        with patch.object(self.board, "redraw"):
            self.board.set_position(
                self.state, self.rules.legal_moves(self.state), None, False
            )
        self.board._board_x = 0
        self.board._board_y = 0
        self.board._square_size = 10

    def tearDown(self):
        if hasattr(self, "root"):
            self.root.destroy()

    def _center(self, square):
        column, row = screen_cell(square)
        return (
            round((column + 0.5) * 10),
            round((row + 0.5) * 10),
        )

    def _press(self, square):
        x, y = self._center(square)
        event = SimpleNamespace(x=x, y=y)
        self.board._on_button_press(event)
        self.board._on_button_release(event)

    def test_click_click_requests_only_a_domain_legal_move(self):
        source, destination = parse_square("e2"), parse_square("e4")
        with patch.object(self.board, "focus_set"), patch.object(self.board, "redraw"):
            self._press(source)
            self.assertEqual(self.board.selected_square, source)
            self._press(destination)
        self.assertEqual(self.requested, [(Move(source, destination),)])

    def test_drag_and_drop_requests_a_domain_legal_move(self):
        source, destination = parse_square("e2"), parse_square("e4")
        start_x, start_y = self._center(source)
        end_x, end_y = self._center(destination)
        with patch.object(self.board, "focus_set"), patch.object(self.board, "redraw"):
            self.board._on_button_press(SimpleNamespace(x=start_x, y=start_y))
            self.board._on_drag(SimpleNamespace(x=end_x, y=end_y))
            self.board._on_button_release(SimpleNamespace(x=end_x, y=end_y))
        self.assertEqual(self.requested, [(Move(source, destination),)])

    def test_keyboard_focus_selects_and_requests_a_legal_move(self):
        with patch.object(self.board, "redraw"):
            self.board._on_key(SimpleNamespace(keysym="Right"))
            self.assertEqual(self.board._focused_square, parse_square("e2"))
            self.board._on_key(SimpleNamespace(keysym="Return"))
            self.assertEqual(self.board.selected_square, parse_square("e2"))

            self.board._on_key(SimpleNamespace(keysym="Up"))
            self.board._on_key(SimpleNamespace(keysym="Up"))
            self.assertEqual(self.board._focused_square, parse_square("e4"))
            self.board._on_key(SimpleNamespace(keysym="Return"))

        self.assertEqual(
            self.requested,
            [(Move(parse_square("e2"), parse_square("e4")),)],
        )

    def test_keyboard_activation_does_not_dispatch_an_illegal_move(self):
        with patch.object(self.board, "redraw"):
            self.board._on_key(SimpleNamespace(keysym="Right"))
            self.board._on_key(SimpleNamespace(keysym="Return"))
            for _ in range(3):
                self.board._on_key(SimpleNamespace(keysym="Up"))
            self.assertEqual(self.board._focused_square, parse_square("e5"))
            self.board._on_key(SimpleNamespace(keysym="Return"))

        self.assertEqual(self.requested, [])
        self.assertIsNone(self.board.selected_square)


class ChessAppActionTests(unittest.TestCase):
    def setUp(self):
        self.root = create_root(self)
        self.root.withdraw()
        self.app = ChessApp(self.root)

    def tearDown(self):
        if hasattr(self, "app"):
            self.app.close()

    def test_undo_and_redo_controls_follow_the_game_timeline(self):
        move = Move(parse_square("e2"), parse_square("e4"))
        self.assertEqual(self.app.undo_button.cget("state"), tk.DISABLED)
        self.assertEqual(self.app.redo_button.cget("state"), tk.DISABLED)

        self.app._play_move(move)
        self.assertEqual(self.app.game.state.board[parse_square("e4")].kind, PieceType.PAWN)
        self.assertEqual(self.app.undo_button.cget("state"), tk.NORMAL)

        self.app._undo()
        self.assertEqual(self.app.game.outcome().status, GameStatus.ACTIVE)
        self.assertIsNone(self.app.game.state.board[parse_square("e4")])
        self.assertEqual(self.app.undo_button.cget("state"), tk.DISABLED)
        self.assertEqual(self.app.redo_button.cget("state"), tk.NORMAL)

        self.app._redo()
        self.assertEqual(self.app.game.state.board[parse_square("e4")].kind, PieceType.PAWN)
        self.assertEqual(self.app.undo_button.cget("state"), tk.NORMAL)
        self.assertEqual(self.app.redo_button.cget("state"), tk.DISABLED)

    def test_flip_action_updates_app_and_board_orientation(self):
        self.assertEqual(self.app.orientation, "white")
        self.app._flip_board()
        self.assertEqual(self.app.orientation, "black")
        self.assertEqual(self.app.board._orientation, "black")
        self.app._flip_board()
        self.assertEqual(self.app.orientation, "white")
        self.assertEqual(self.app.board._orientation, "white")


if __name__ == "__main__":
    unittest.main()
