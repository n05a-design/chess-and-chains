"""Focused geometry and legal-move tests for the board interaction layer."""
import sys
import tempfile
import tkinter as tk
import unittest
import xml.etree.ElementTree as ET
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
from chess_and_chains.ui.board_artwork import BoardArtwork, BoardArtworkError, load_board_design  # noqa: E402
from tests.tk_support import create_root  # noqa: E402
from chess_and_chains.ui.board import (  # noqa: E402
    BoardCanvas,
    moves_between,
    screen_cell,
    square_at_point,
)


def _write_square(path: Path, color: str) -> None:
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">'
        f'<rect width="256" height="256" fill="{color}"/></svg>',
        encoding="utf-8",
    )


class BoardArtworkInputTests(unittest.TestCase):
    def test_full_board_accepts_the_editable_template(self):
        design = load_board_design(ROOT / "assets" / "boards" / "source" / "board-template.svg")
        self.assertIsNotNone(design.full)
        self.assertEqual(design.tiles, ())

    def test_light_dark_pair_with_an_algebraic_override(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for filename, color in (("light.svg", "#ffeecc"), ("dark.svg", "#504136"), ("e4.svg", "#00aa00")):
                _write_square(folder / filename, color)
            tiles = load_board_design(folder).tiles
            self.assertEqual(len(tiles), 64)
            self.assertIn(b"#ffeecc", tiles[0])  # a8
            self.assertIn(b"#504136", tiles[1])  # b8
            self.assertIn(b"#00aa00", tiles[36])  # e4
            self.assertEqual(sum(b"#00aa00" in tile for tile in tiles), 1)

    def test_all_64_labeled_svgs_work_without_the_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for rank in range(1, 9):
                for column, file in enumerate("abcdefgh"):
                    _write_square(folder / f"{file}{rank}.svg", f"#{column}{rank}0000")
            tiles = load_board_design(folder).tiles
            self.assertIn(b"#080000", tiles[0])
            self.assertIn(b"#710000", tiles[63])
            self.assertEqual(len(set(tiles)), 64)
            (folder / "a1.svg").unlink()
            with self.assertRaisesRegex(BoardArtworkError, "all 64"):
                load_board_design(folder)

    def test_invalid_viewbox_and_external_svg_references_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "board.svg"
            for viewbox, child, message in (
                ("0 0 200 256", "<rect width='10' height='10'/>", "square viewBox"),
                ("0 0 256 256", "<foreignObject/>", "unsupported SVG element"),
                ("0 0 256 256", "<rect style='fill:url(https://example.invalid/a.svg)'/>", "same document"),
            ):
                with self.subTest(message=message):
                    file.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}">{child}</svg>',
                                    encoding="utf-8")
                    with self.assertRaisesRegex(BoardArtworkError, message):
                        load_board_design(file)


class BoardArtworkUiTests(unittest.TestCase):
    def test_tile_background_tracks_the_named_square_and_keeps_marks_in_front(self):
        root = create_root(self)
        self.addCleanup(root.destroy)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for filename, color in (("light.svg", "#ffeecc"), ("dark.svg", "#504136"), ("a8.svg", "#00aa00")):
                _write_square(folder / filename, color)
            artwork = BoardArtwork(load_board_design(folder))

        def render_square(master, content, size, *, flipped=False):
            root_element = ET.fromstring(content)
            color = root_element[0].get("fill")
            photo = tk.PhotoImage(master=master, width=size, height=size)
            photo.put(color, to=(0, 0, size, size))
            return photo

        with patch.object(artwork, "_photo", side_effect=render_square):
            board = BoardCanvas(root, lambda _moves: None, artwork=artwork)
            board._square_size = 24
            board._last_move = Move.from_uci("e2e4")
            with patch.object(board, "_draw_last_move", wraps=board._draw_last_move) as mark:
                board._draw_board()
                self.assertEqual(mark.call_count, 2)
            background, = board.find_withtag("board-artwork")
            self.assertEqual(board.find_all()[64], background)
            self.assertEqual(artwork.image(board, 24, flipped=False).get(12, 12), (0, 170, 0))
            board.set_orientation("black")
            reversed_image = artwork.image(board, 24, flipped=True)
            self.assertEqual(reversed_image.get(180, 180), (0, 170, 0))
            self.assertIs(artwork.image(board, 24, flipped=True), reversed_image)


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
