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
from chess_and_chains.ui.board_artwork import (  # noqa: E402
    BoardArtwork,
    BoardArtworkError,
    Marble2DArtwork,
    load_board_design,
)
from chess_and_chains.ui.marble_board import MarbleBoardCanvas  # noqa: E402
from chess_and_chains.ui.theme import ACCENT_CHOICES, resolve_theme  # noqa: E402
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
            if color == "#00aa00":
                photo.put("#0000ff", to=(0, 0, 3, 4))
                photo.transparency_set(size - 1, 0, True)
            return photo

        with patch.object(artwork, "_photo", side_effect=render_square) as render:
            board = BoardCanvas(root, lambda _moves: None, artwork=artwork)
            board._square_size = 24
            board._last_move = Move.from_uci("e2e4")
            with patch.object(board, "_draw_last_move", wraps=board._draw_last_move) as mark:
                board._draw_board()
                self.assertEqual(mark.call_count, 2)
            background, = board.find_withtag("board-artwork")
            self.assertEqual(board.find_all()[64], background)
            forward = artwork.image(board, 24, flipped=False)
            self.assertEqual(forward.get(12, 12), (0, 170, 0))
            board.set_orientation("black")
            reversed_image = artwork.image(board, 24, flipped=True)
            self.assertEqual(reversed_image.get(180, 180), (0, 170, 0))
            self.assertEqual(reversed_image.get(168, 168), (0, 0, 255))
            self.assertTrue(reversed_image.transparency_get(191, 168))
            self.assertIs(artwork.image(board, 24, flipped=True), reversed_image)
            self.assertIs(artwork.image(board, 24, flipped=False), forward)
            self.assertEqual(render.call_count, 3)

            larger = artwork.image(board, 32, flipped=True)
            self.assertEqual(larger.width(), 256)
            self.assertEqual(larger.get(224, 224), (0, 0, 255))
            self.assertIsNot(artwork.image(board, 24, flipped=False), forward)
            self.assertEqual(render.call_count, 9)

    def test_full_board_caches_each_orientation_for_the_current_size(self):
        root = create_root(self)
        artwork = BoardArtwork(load_board_design(ROOT / "assets" / "boards" / "source" / "board-template.svg"))

        def render_board(master, _content, size, *, flipped):
            return tk.PhotoImage(master=master, width=size, height=size)

        with patch.object(artwork, "_photo", side_effect=render_board) as render:
            forward = artwork.image(root, 24, flipped=False)
            flipped = artwork.image(root, 24, flipped=True)
            self.assertIs(artwork.image(root, 24, flipped=False), forward)
            self.assertIs(artwork.image(root, 24, flipped=True), flipped)
            self.assertEqual([call.kwargs["flipped"] for call in render.call_args_list], [False, True])
            self.assertEqual(artwork.image(root, 32, flipped=False).width(), 256)
            self.assertIsNot(artwork.image(root, 24, flipped=True), flipped)


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
        self.app = ChessApp(self.root)
        self.addCleanup(self.app.close)

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


class BoardMarkerCenteringTests(unittest.TestCase):
    @staticmethod
    def _coords_center(coords: list[float]) -> tuple[float, float]:
        if len(coords) == 4:
            return (coords[0] + coords[2]) / 2.0, (coords[1] + coords[3]) / 2.0
        xs = coords[0::2]
        ys = coords[1::2]
        return (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0

    def test_2d_markers_and_concentric_rings_share_exact_square_center_all_squares(self):
        root = create_root(self)
        root.deiconify()
        board = MarbleBoardCanvas(root, lambda _moves: None)
        board.pack(fill="both", expand=True)
        root.geometry("640x640")
        root.update()
        # Valid position with legal quiet moves and capture Qxd5
        state = parse_fen("7k/8/8/3p4/4Q3/8/8/4K3 w - - 0 1")
        rules = ChessRules()
        legal = rules.legal_moves(state)

        for design in ("standard", "marble"):
            board.set_board_design(design)
            for size in ((420, 420), (640, 640), (790, 710)):
                root.geometry(f"{size[0]}x{size[1]}")
                root.update()
                for orientation in ("white", "black"):
                    board.set_orientation(orientation)
                    # Check all 64 squares across focus, hint, selection, and last move
                    board.set_position(state, legal, Move.from_uci("d1e4"), in_check=True)
                    for sq in range(64):
                        board._selected = sq
                        board._focused_square = sq
                        board._has_focus = True
                        board._hint_square = sq
                        board.redraw()
                        exp_x, exp_y = board.square_center(sq)
                        for tag in ("selected-square", "square-focus", "hint"):
                            items = board.find_withtag(tag)
                            self.assertTrue(items, f"missing {tag} on sq {sq}")
                            for item in items:
                                cx, cy = self._coords_center(board.coords(item))
                                self.assertAlmostEqual(cx, exp_x, delta=0.01)
                                self.assertAlmostEqual(cy, exp_y, delta=0.01)

                    # Verify all quiet + capture legal move concentric rings share exact square centers
                    e4 = parse_square("e4")
                    board._selected = e4
                    board._hint_square = None
                    board.redraw()
                    quiet_items = board.find_withtag("legal-move")
                    capture_items = board.find_withtag("legal-capture")
                    self.assertTrue(len(quiet_items) >= 2 and len(quiet_items) % 2 == 0)
                    self.assertTrue(len(capture_items) >= 2 and len(capture_items) % 2 == 0)

                    legal_dests = {m.to_square for m in legal if m.from_square == e4}
                    dest_centers = [board.square_center(sq) for sq in legal_dests]
                    for idx in range(0, len(quiet_items), 2):
                        c1 = self._coords_center(board.coords(quiet_items[idx]))
                        c2 = self._coords_center(board.coords(quiet_items[idx + 1]))
                        self.assertAlmostEqual(c1[0], c2[0], delta=0.01)
                        self.assertAlmostEqual(c1[1], c2[1], delta=0.01)
                        self.assertTrue(any(abs(c1[0] - dx) < 0.01 and abs(c1[1] - dy) < 0.01 for dx, dy in dest_centers))
                    for idx in range(0, len(capture_items), 2):
                        c1 = self._coords_center(board.coords(capture_items[idx]))
                        c2 = self._coords_center(board.coords(capture_items[idx + 1]))
                        self.assertAlmostEqual(c1[0], c2[0], delta=0.01)
                        self.assertAlmostEqual(c1[1], c2[1], delta=0.01)
                        d5x, d5y = board.square_center(parse_square("d5"))
                        self.assertAlmostEqual(c1[0], d5x, delta=0.01)
                        self.assertAlmostEqual(c1[1], d5y, delta=0.01)

    def test_3d_projected_markers_and_concentric_rings_use_projected_square_center(self):
        root = create_root(self)
        root.deiconify()
        board = MarbleBoardCanvas(root, lambda _moves: None)
        board.pack(fill="both", expand=True)
        root.geometry("640x640")
        root.update()
        root.geometry("760x700")
        root.update()
        state = parse_fen("7k/8/8/3p4/4Q3/8/8/4K3 w - - 0 1")
        rules = ChessRules()
        legal = rules.legal_moves(state)
        board.set_board_design("marble")
        board.set_perspective("3d")
        board.set_position(state, legal, Move.from_uci("d1e4"), in_check=True)
        e4 = parse_square("e4")
        d5 = parse_square("d5")
        board._selected = e4
        board._focused_square = e4
        board._has_focus = True
        board.redraw()

        self.assertTrue(board.find_withtag("marble-board"))
        quiet = board.find_withtag("legal-move")
        capture = board.find_withtag("legal-capture")
        self.assertTrue(len(quiet) >= 2)
        self.assertTrue(len(capture) >= 2)
        d5x, d5y = board.projected_square_center(d5)
        for idx in range(0, len(capture), 2):
            c1 = self._coords_center(board.coords(capture[idx]))
            c2 = self._coords_center(board.coords(capture[idx + 1]))
            self.assertAlmostEqual(c1[0], c2[0], delta=0.5)
            self.assertAlmostEqual(c1[1], c2[1], delta=0.5)
            self.assertAlmostEqual(c1[0], d5x, delta=0.5)
            self.assertAlmostEqual(c1[1], d5y, delta=0.5)

    def test_marble_2d_tinting_and_custom_svg_isolation(self):
        root = create_root(self)
        marble_art = Marble2DArtwork()
        gray = marble_art.image(root, 32, flipped=False, tint_color=resolve_theme("light", accent="muted").brand_blue)
        cobalt = marble_art.image(root, 32, flipped=False, tint_color=resolve_theme("light", accent="accent").brand_blue)
        emerald = marble_art.image(root, 32, flipped=False, tint_color=resolve_theme("light", accent="export").brand_blue)
        self.assertEqual((gray.width(), gray.height()), (256, 256))
        self.assertEqual((cobalt.width(), cobalt.height()), (256, 256))
        self.assertNotEqual(cobalt.get(16, 16), emerald.get(16, 16))
        # Custom SVG artwork receives no tint_color parameter and keeps its exact design
        custom = BoardArtwork(load_board_design(ROOT / "assets" / "boards" / "source" / "board-template.svg"))
        board = MarbleBoardCanvas(root, lambda _moves: None, artwork=custom)
        self.assertEqual(board.board_design, "custom")
        for acc, _lbl in ACCENT_CHOICES:
            board.set_theme(resolve_theme("light", accent=acc))
            self.assertIs(board._artwork, custom)


if __name__ == "__main__":
    unittest.main()
