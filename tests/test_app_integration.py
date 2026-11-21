"""Tk app integration: mock-bot vertical slice, non-blocking UI, puzzles, storage.

Runs a real Tk root (withdrawn). The bot is the project-owned mock UCI
engine in a subprocess; this is not a test against a real chess engine.
"""
import sys
import tempfile
import time
import tkinter as tk
import unittest
from contextlib import ExitStack
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from chess_and_chains import DISPLAY_VERSION  # noqa: E402
from chess_and_chains.chess import Color, DrawClaim, GameStatus, Move, Piece, PieceType, parse_square  # noqa: E402
from chess_and_chains.engines.bot import EngineConfig, UCIBot  # noqa: E402
from chess_and_chains.engines.mock_engine import ENGINE_NAME  # noqa: E402
from chess_and_chains.game import BotStatus, GameSetup  # noqa: E402
from chess_and_chains.storage import DataLayout, load_settings  # noqa: E402
from chess_and_chains.ui.app import ChessApp, EngineDialog  # noqa: E402
from chess_and_chains.ui.branding import brand_image  # noqa: E402
from chess_and_chains.ui.pieces import (  # noqa: E402
    PIECE_FALLBACK_SIZES,
    PIECE_FILE_NAMES,
    GeometricTestPieces,
    OwnerSvgPieces,
    validate_svg_piece_set,
)
from tests.tk_support import create_root  # noqa: E402


def mock_factory(delay_ms=0, mode="normal"):
    created = []

    def factory(preset, _settings):
        bot = UCIBot(EngineConfig.mock(mode, delay_ms=delay_ms), preset)
        created.append(bot)
        return bot

    factory.created = created
    return factory


class AppTestCase(unittest.TestCase):
    def make_app(self, **kwargs):
        self.root = create_root(self)
        kwargs.setdefault("locale", "en")
        self.app = ChessApp(self.root, **kwargs)
        self.addCleanup(self.app.close)
        return self.app

    def pump_until(self, predicate, timeout=10.0):
        reached = False
        check_job = None

        def check():
            nonlocal reached, check_job
            check_job = None
            reached = bool(predicate())
            if reached:
                self.root.quit()
            else:
                check_job = self.root.after(5, check)

        stop_job = self.root.after(int(timeout * 1000), self.root.quit)
        check_job = self.root.after(0, check)
        try:
            self.root.mainloop()
        finally:
            self.root.after_cancel(stop_job)
            if check_job is not None:
                self.root.after_cancel(check_job)
            # Break the recursive callback's cycle while still on the Tk thread.
            del check
        self.assertTrue(reached, "condition not reached while pumping Tk events")

    def pump_for(self, seconds):
        deadline = time.monotonic() + seconds
        self.pump_until(lambda: time.monotonic() >= deadline, timeout=seconds + 1)


class PromotionUiTests(AppTestCase):
    def test_keyboard_promotion_counts_one_target_and_accepts_return(self):
        app = self.make_app(locale="de")
        app.controller.new_game(GameSetup(initial_fen="4k3/P7/8/8/8/8/8/4K3 w - - 0 1"))
        self.root.deiconify()
        self.root.update()
        app.board.focus_force()
        self.root.update()

        keys = ("Left",) * 4 + ("Up",) * 5 + ("Return",)
        for key in keys:
            app.board.event_generate(f"<{key}>")
        self.assertEqual(app.interaction_text.get(), "a7 ausgewählt · 1 legales Zielfeld")
        app.board.event_generate("<Up>")

        deadline = time.monotonic() + 5
        focused_rook = False
        pending = None

        def choose_rook():
            nonlocal focused_rook, pending
            pending = None
            dialog = next(child for child in self.root.winfo_children() if isinstance(child, tk.Toplevel))
            rook = next(child for child in dialog.winfo_children()
                        if isinstance(child, tk.Button) and child.cget("text") == "Turm")
            if time.monotonic() >= deadline:
                dialog.destroy()
            elif not rook.winfo_viewable():
                pending = self.root.after(10, choose_rook)
            elif self.root.focus_get() is not rook:
                rook.focus_force()
                pending = self.root.after(10, choose_rook)
            else:
                focused_rook = True
                # Aqua can still be processing focus events from the new toplevel.
                rook.event_generate("<Return>", when="tail")
                pending = self.root.after(1000, dialog.destroy)

        pending = self.root.after(0, choose_rook)
        try:
            app.board.event_generate("<Return>")
        finally:
            if pending is not None:
                self.root.after_cancel(pending)
        self.assertTrue(focused_rook, "the mapped promotion button never received keyboard focus")
        self.assertEqual(app.game.moves, [Move.from_uci("a7a8r")])

    def test_promotion_dialog_applies_a_legal_underpromotion(self):
        app = self.make_app()
        app.controller.new_game(GameSetup(initial_fen="4k3/P7/8/8/8/8/8/4K3 w - - 0 1"))
        choices = tuple(move for move in app.board._legal_moves if move.from_square == parse_square("a7"))
        invoked = []

        def choose_rook():
            dialog = next(child for child in self.root.winfo_children() if isinstance(child, tk.Toplevel))
            try:
                rook = next(child for child in dialog.winfo_children()
                            if isinstance(child, tk.Button) and child.cget("text") == "Rook")
                rook.invoke()
                invoked.append(True)
            finally:
                if dialog.winfo_exists():
                    dialog.destroy()

        self.root.after(0, choose_rook)
        app._on_move_requested(choices)
        self.assertTrue(invoked)
        self.assertEqual(app.game.moves, [Move.from_uci("a7a8r")])
        self.assertEqual(app.controller.view().san_moves, ("a8=R+",))
        app._undo()
        self.assertEqual(app.game.moves, [])
        app._redo()
        self.assertEqual(app.game.moves, [Move.from_uci("a7a8r")])


class DrawClaimTests(AppTestCase):
    def test_dead_position_ends_game_and_disables_move_entry(self):
        app = self.make_app(locale="de")
        app.controller.new_game(GameSetup(initial_fen="8/8/8/8/8/8/1rk5/K7 b - - 0 1"))
        app._play_move(Move.from_uci("b2a2"))
        self.assertEqual(app.panel_text.get(), "Remis durch tote Stellung")
        self.assertEqual(app.board._legal_moves, ())
        self.assertEqual(app.resign_button.cget("state"), tk.DISABLED)
        app._undo()
        self.assertEqual(app.panel_text.get(), "Schwarz am Zug")
        self.assertIn(Move.from_uci("b2a2"), app.board._legal_moves)

    def test_claim_by_declared_move_preserves_position_and_supports_undo(self):
        app = self.make_app()
        for uci in ("g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1"):
            app._play_move(Move.from_uci(uci))
        before = app.game.state
        self.assertFalse(app.game.outcome().claimable_draws)
        self.assertEqual(app.claim_button.cget("state"), tk.NORMAL)
        with patch.object(app, "_choose_item", return_value=0) as chooser:
            app.claim_button.invoke()
        self.assertEqual(chooser.call_args.args[1], ["Threefold repetition by declaring Ng8"])
        self.assertIs(app.game.state, before)
        self.assertEqual(len(app.game.moves), 7)
        self.assertEqual(app.game.outcome().status, GameStatus.DRAW_CLAIMED)
        app._undo()
        self.assertEqual(app.game.outcome().status, GameStatus.ACTIVE)
        app._redo()
        self.assertEqual(app.game.outcome().status, GameStatus.DRAW_CLAIMED)


class BotVerticalSliceTests(AppTestCase):
    def test_closing_engine_dialog_cancels_pending_tk_poll(self):
        app = self.make_app()
        dialog = EngineDialog(app)
        with patch.object(EngineConfig, "from_path", return_value=EngineConfig.mock()):
            with patch("chess_and_chains.ui.app.threading.Thread"):
                dialog.test()
        pending = dialog._probe_job
        self.assertIsNotNone(pending)
        dialog.window.destroy()
        self.assertIsNone(dialog._probe_job)
        with self.assertRaises(tk.TclError):
            self.root.tk.call("after", "info", pending)

    def test_engine_dialog_reports_readiness_and_handles_exit_after_uciok(self):
        app = self.make_app()
        for mode, expected in (("normal", ENGINE_NAME), ("crash-on-ready", "Engine test failed")):
            with self.subTest(mode=mode):
                dialog = EngineDialog(app)
                with patch.object(EngineConfig, "from_path", return_value=EngineConfig.mock(mode)):
                    dialog.test()
                self.assertEqual(dialog.test_button.cget("state"), tk.DISABLED)
                self.pump_until(lambda: dialog.test_button.cget("state") == tk.NORMAL)
                self.assertIn(expected, dialog.status_var.get())
                dialog.window.destroy()
        self.assertIsNone(app.settings.engine_path)

    def test_user_move_bot_reply_and_ui_update(self):
        factory = mock_factory()
        app = self.make_app(provider_factory=factory)
        app.start_game("human-vs-bot-white")
        self.assertIn("YOU PLAY WHITE", app.header_mode_text.get())
        self.assertIn("MOCK", app.header_mode_text.get())
        app._play_move(Move.from_uci("e2e4"))
        self.pump_until(lambda: len(app.game.moves) == 2)
        view = app.controller.view()
        self.assertTrue(view.human_to_move)
        self.assertEqual(app.move_list.size(), 1)
        self.assertIn("e4", app.move_list.get(0))
        self.assertIn("not a real chess AI", app.bot_text.get())
        # Board shows the bot's move and only domain-legal moves for the human.
        self.assertEqual(app.board._state, app.game.state)
        self.assertTrue(all(m in app.game.rules.legal_moves(app.game.state) for m in app.board._legal_moves))

    def test_tk_event_loop_keeps_running_while_bot_thinks(self):
        app = self.make_app(provider_factory=mock_factory(delay_ms=600))
        app.start_game("human-vs-bot-white")
        start = time.monotonic()
        app._play_move(Move.from_uci("d2d4"))
        self.assertLess(time.monotonic() - start, 0.3, "human move must return before the bot answers")
        self.assertEqual(app.controller.view().bot_status, BotStatus.THINKING)
        self.assertIn("thinking", app.bot_text.get())
        self.assertEqual(app.board._legal_moves, (), "board is locked while the bot thinks")
        gaps, last = [], time.monotonic()

        def bot_replied():
            nonlocal last
            now = time.monotonic()
            gaps.append(now - last)
            last = now
            return len(app.game.moves) == 2

        self.pump_until(bot_replied)
        self.assertLess(max(gaps), 0.25, "Tk loop stalled while engine computed")

    def test_bot_plays_white_and_board_orients_for_black(self):
        app = self.make_app(provider_factory=mock_factory())
        app.start_game("human-vs-bot-black")
        self.assertEqual(app.orientation, "black")
        self.pump_until(lambda: len(app.game.moves) == 1)
        self.assertEqual(app.game.state.turn, Color.BLACK)

    def test_undo_during_thinking_and_new_game_discards_stale_move(self):
        app = self.make_app(provider_factory=mock_factory(delay_ms=400))
        app.start_game("human-vs-bot-white")
        app._play_move(Move.from_uci("e2e4"))
        app._undo()
        self.assertEqual(app.game.moves, [])
        app.start_game("human-vs-human")
        self.pump_for(0.8)
        self.assertEqual(app.game.moves, [])
        self.assertIn("TWO PLAYERS", app.header_mode_text.get())

    def test_engine_crash_shows_error_and_retry_button(self):
        app = self.make_app(provider_factory=mock_factory(mode="crash"))
        app.start_game("human-vs-bot-white")
        app._play_move(Move.from_uci("e2e4"))
        self.pump_until(lambda: app.controller.view().bot_status is BotStatus.ERROR)
        self.assertIn("Bot problem", app.bot_text.get())
        self.assertEqual(app.retry_bot_button.cget("state"), tk.NORMAL)
        self.assertEqual(len(app.game.moves), 1)

    def test_close_terminates_engine_process(self):
        factory = mock_factory(delay_ms=3000)
        app = self.make_app(provider_factory=factory)
        app.start_game("human-vs-bot-black")
        self.pump_until(lambda: factory.created and factory.created[0]._engine is not None
                        and factory.created[0]._engine.running)
        engine = factory.created[0]._engine
        start = time.monotonic()
        app.close()
        self.assertLess(time.monotonic() - start, 3.0)
        self.assertFalse(engine.running)

    def test_resign_ends_game(self):
        app = self.make_app()
        app._play_move(Move.from_uci("e2e4"))
        app._resign()
        self.assertIs(app.game.outcome().status, GameStatus.RESIGNED)
        self.assertIn("wins by resignation", app.panel_text.get())

    def test_resigning_to_lone_king_displays_draw(self):
        app = self.make_app()
        app.controller.new_game(GameSetup(initial_fen="4k3/8/8/8/8/8/4P3/4K3 b - - 0 1"))
        app._play_move(Move.from_uci("e8d7"))
        app.resign_button.invoke()
        self.assertIn("Draw after resignation", app.panel_text.get())
        self.assertTrue(app._current_pgn().endswith("1/2-1/2"))


class PuzzleUiTests(AppTestCase):
    def test_puzzle_tab_uses_same_board_and_records_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = self.make_app(data_layout=DataLayout(Path(tmp) / "data"))
            app.tab_rail.set_active("puzzles")
            self.assertEqual(app.active_panel, "puzzles")
            self.assertIn("PUZZLE LAB", app.header_mode_text.get())
            self.assertEqual(app.puzzle_atlas._stations[0], (1, "open", True))
            session = app.puzzle
            self.assertIs(app.board._state, session.state)
            app._play_move(Move.from_uci("a1a2"))  # not legal: board would never offer it
            app._play_move(session.expected_move)
            self.assertEqual(app.puzzle_feedback_text.get(), "Solved!")
            self.assertEqual(app.db.solved_puzzle_ids("demo"), {session.puzzle.puzzle_id})
            self.assertEqual(app.puzzle_atlas._stations[0], (1, "solved", True))
            app._next_puzzle()
            app._puzzle_hint()
            self.assertEqual(app.board._hint_square, app.puzzle.expected_move.from_square)
            app._puzzle_reveal()
            self.assertIn("Solution:", app.puzzle_feedback_text.get())
            self.assertEqual(app.puzzle_atlas._stations[:2], ((1, "solved", False), (2, "revealed", True)))
            self.assertEqual(app.db.statistics().puzzles_attempted, 2)
            app.tab_rail.set_active("play")
            self.assertIs(app.board._state, app.game.state)
            app.close()

    def test_puzzle_filters_show_stored_progress_and_handle_empty_matches(self):
        with ExitStack() as stack:
            tmp = stack.enter_context(tempfile.TemporaryDirectory())
            app = self.make_app(data_layout=DataLayout(Path(tmp) / "data"))
            stack.callback(app.close)
            self.root.deiconify()
            app.db.record_puzzle_attempt("demo", "ccSC01", solved=True, mistakes=0, hints_used=0, duration_ms=500)
            app.tab_rail.set_active("puzzles")
            self.root.update()
            self.assertEqual(app.puzzle_progress_text.get(), "Solved 1 of 5 in this selection.")

            app.puzzle_theme_filter.current(app.puzzle_theme_filter.cget("values").index("Opening"))
            app.puzzle_theme_filter.event_generate("<<ComboboxSelected>>", when="tail")
            self.root.update()
            self.assertEqual(app.puzzle.puzzle.puzzle_id, "ccSC01")
            self.assertIn("Mate, Mate in 1, Opening", app.puzzle_meta_text.get())
            self.assertEqual(app.puzzle_progress_text.get(), "Solved 1 of 2 in this selection.")
            app._next_puzzle()
            app._play_move(app.puzzle.expected_move)
            self.assertEqual(app.puzzle_progress_text.get(), "Solved 2 of 2 in this selection.")
            self.assertEqual(app.board.orientation, "black")

            app.puzzle_rating_filter.current(2)
            app.puzzle_rating_filter.event_generate("<<ComboboxSelected>>", when="tail")
            self.root.update()
            self.assertIsNone(app.puzzle)
            self.assertIsNone(app.board._state)
            self.assertEqual(app.panel_text.get(), "No puzzles match the filters.")
            self.assertEqual(app.next_puzzle_button.cget("state"), tk.DISABLED)
            self.assertEqual(app.puzzle_atlas._stations, ())
            self.assertEqual(app.atlas_section.winfo_manager(), "")

            app.tab_rail.set_active("play")
            self.assertIs(app.board._state, app.game.state)
            self.assertEqual(app.board.orientation, "white")
            app.tab_rail.set_active("puzzles")
            self.root.update()
            app.puzzle_theme_filter.current(0)
            app.puzzle_theme_filter.event_generate("<<ComboboxSelected>>", when="tail")
            self.root.update()
            self.assertEqual(app.puzzle.puzzle.puzzle_id, "ccSM02")
            self.assertEqual(app.puzzle_progress_text.get(), "Solved 0 of 1 in this selection.")

    def test_german_puzzle_themes_show_localized_labels_and_filter_by_id(self):
        app = self.make_app(locale="de")
        self.root.deiconify()
        app.tab_rail.set_active("puzzles")
        self.root.update()
        self.assertIn("Matt, Matt in 1, Grundreihenmatt", app.puzzle_meta_text.get())

        choices = app.puzzle_theme_filter.cget("values")
        app.puzzle_theme_filter.current(choices.index("Ersticktes Matt"))
        app.puzzle_theme_filter.event_generate("<<ComboboxSelected>>", when="tail")
        self.root.update()

        self.assertEqual(app.puzzle.puzzle.puzzle_id, "ccSM02")
        self.assertIn("smotheredMate", app.puzzle.puzzle.themes)
        self.assertIn("Matt, Matt in 2, Ersticktes Matt", app.puzzle_meta_text.get())
        self.assertEqual(app.panel_text.get(), "Rätsel 1 von 1")

    def test_game_undo_is_ignored_in_puzzle_mode(self):
        app = self.make_app()
        app._play_move(Move.from_uci("e2e4"))
        app.tab_rail.set_active("puzzles")
        app._undo()
        self.assertEqual(len(app.game.moves), 1)


class BrandingUiTests(AppTestCase):
    def test_packaged_brand_marks_load_when_tk_cannot_read_svg(self):
        root = create_root(self)
        photo_image = tk.PhotoImage

        def without_svg(*args, **kwargs):
            if kwargs.get("format", ())[0] == "svg":
                raise tk.TclError("image format svg is not supported")
            return photo_image(*args, **kwargs)

        with patch("chess_and_chains.ui.branding.tk.PhotoImage", side_effect=without_svg):
            for name, scale, expected_size in (
                ("signet", 40 / 64, (40, 40)), ("app-icon", 1, (64, 64)), ("wordmark", 1, (254, 40)),
            ):
                image = brand_image(root, name, scale=scale)
                self.assertEqual((image.width(), image.height()), expected_size)
                self.assertTrue(image.transparency_get(0, 0))

    def test_test_piece_letter_fits_its_disc_at_double_text_scale(self):
        root = create_root(self)
        scale = root.tk.call("tk", "scaling")
        self.addCleanup(root.tk.call, "tk", "scaling", scale)
        root.tk.call("tk", "scaling", 8 / 3)
        canvas = tk.Canvas(root)
        queen = Piece(Color.WHITE, PieceType.QUEEN)
        GeometricTestPieces().draw(canvas, 40, 40, 46, queen)
        disc, glyph = (canvas.bbox(item) for item in canvas.find_withtag("piece"))
        self.assertLessEqual(disc[0], glyph[0])
        self.assertLessEqual(glyph[2], disc[2])


class OwnerPieceUiTests(AppTestCase):
    def test_owner_pieces_render_and_are_reused_in_play_and_puzzles(self):
        app = self.make_app()
        self.root.geometry("860x700")
        self.root.deiconify()
        self.pump_until(lambda: len(app.board.find_withtag("piece")) == 32)
        self.root.update()
        board = app.board
        self.assertIsInstance(board.renderer, OwnerSvgPieces)

        def images():
            return {board.itemcget(item, "image") for item in board.find_withtag("piece")}

        initial_images = images()
        self.assertEqual(len(initial_images), 12)
        app._play_move(Move.from_uci("e2e4"))
        board.set_orientation("black")
        self.assertEqual(len(board.find_withtag("piece")), 32)
        self.assertEqual(images(), initial_images)

        app.tab_rail.set_active("puzzles")
        self.assertIsNotNone(app.puzzle)
        self.assertEqual(len(board.find_withtag("piece")), sum(piece is not None for piece in app.puzzle.state.board))
        self.assertTrue(images())
        self.assertTrue(images() <= initial_images)

    def test_png_atlas_preserves_piece_color_and_shadows_and_reuses_the_same_size_band(self):
        root = create_root(self)
        canvas = tk.Canvas(root)
        renderer = OwnerSvgPieces()
        photo_image = tk.PhotoImage

        def without_svg(*args, **kwargs):
            if kwargs.get("format", ())[:1] == ("svg",):
                raise tk.TclError("image format svg is not supported")
            return photo_image(*args, **kwargs)

        with patch("chess_and_chains.ui.pieces.tk.PhotoImage", side_effect=without_svg):
            renderer.draw(canvas, 30, 30, 53, Piece(Color.WHITE, PieceType.KING))
            renderer.draw(canvas, 90, 30, 54, Piece(Color.WHITE, PieceType.KING))
            renderer.draw(canvas, 150, 30, 54, Piece(Color.BLACK, PieceType.KING))
        white, another_white, black = (canvas.itemcget(item, "image") for item in canvas.find_withtag("piece"))
        self.assertIsNotNone(renderer._atlas)
        self.assertEqual(white, another_white)
        self.assertEqual(root.tk.call("image", "width", white), 48)
        self.assertTrue(root.tk.getboolean(root.tk.call(white, "transparency", "get", 0, 0)))
        self.assertGreater(root.tk.call(white, "get", 24, 35)[0], 220)
        self.assertLess(root.tk.call(black, "get", 24, 35)[0], 80)
        for image, minimum_drop in ((white, 1), (black, 35)):
            lit_side = root.tk.call(image, "get", 18, 35)[0]
            shaded_side = root.tk.call(image, "get", 35, 35)[0]
            self.assertGreaterEqual(lit_side - shaded_side, minimum_drop)

    def test_top_view_uses_its_own_artwork_in_play_and_puzzles(self):
        renderer = OwnerSvgPieces(top_view=True)
        app = self.make_app(piece_renderer=renderer)
        self.root.geometry("860x700")
        self.root.deiconify()
        self.pump_until(lambda: len(app.board.find_withtag("piece")) == 32)
        self.assertIs(app.board.renderer, renderer)

        def images():
            return {app.board.itemcget(item, "image") for item in app.board.find_withtag("piece")}

        self.assertEqual(len(images()), 12)
        app.tab_rail.set_active("puzzles")
        self.assertIsNotNone(app.puzzle)
        self.assertTrue(images())
        self.assertEqual(len(app.board.find_withtag("piece")), sum(piece is not None for piece in app.puzzle.state.board))

        # The bottom corner of the front-view foot lies outside the top-view disc.
        front = OwnerSvgPieces()
        band = PIECE_FALLBACK_SIZES.index(64)
        self.assertFalse(front._copy_png_piece(app.board, "wK.svg", band).transparency_get(15, 54))
        self.assertTrue(renderer._copy_png_piece(app.board, "wK.svg", band).transparency_get(15, 54))

    def test_piece_images_share_the_visible_dimensions_within_each_view(self):
        root = create_root(self)
        canvas = tk.Canvas(root)
        # Render at 2× so that the half-unit edges land on whole pixels.
        size = 128
        band = PIECE_FALLBACK_SIZES.index(size)
        expected_bounds = {False: (25, 10, 102, 117), True: (12, 12, 115, 115)}
        for top_view, bounds in expected_bounds.items():
            renderer = OwnerSvgPieces(top_view=top_view)
            for name in PIECE_FILE_NAMES:
                with self.subTest(top_view=top_view, piece=name):
                    tile = renderer._copy_png_piece(canvas, name, band)
                    visible = [(x, y) for y in range(size) for x in range(size)
                               if not tile.transparency_get(x, y)]
                    xs, ys = zip(*visible)
                    self.assertEqual((min(xs), min(ys), max(xs), max(ys)), bounds)


class StorageAndLocaleUiTests(AppTestCase):
    def test_startup_reports_database_recovery_alongside_settings_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            layout = DataLayout(Path(tmp) / "data")
            damaged = b"not a SQLite database" * 20
            layout.database.write_bytes(damaged)
            layout.settings.write_text("{", encoding="utf-8")
            app = self.make_app(data_layout=layout, locale="de")
            try:
                recovered = app.db.recovered_from
                self.assertEqual(recovered.read_bytes(), damaged)
                self.assertIn(
                    f"Beschädigte Bibliothek gesichert als {recovered.name}",
                    app.interaction_text.get(),
                )
                self.assertIn("settings.json.invalid-", app.interaction_text.get())
                self.assertEqual(app.db.list_games(), [])
            finally:
                app.close()

    def test_app_variables_belong_to_its_root_with_another_window_open(self):
        other_root = create_root(self)
        app = self.make_app()
        self.assertIsNot(self.root.tk, other_root.tk)
        self.assertIs(app.interaction_text._tk, self.root.tk)
        self.assertIs(app.mode_var._tk, self.root.tk)

    def test_save_game_and_settings_persist_in_temp_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            layout = DataLayout(Path(tmp) / "data")
            app = self.make_app(data_layout=layout)
            self.assertEqual(app.save_button.cget("state"), tk.DISABLED)
            app._play_move(Move.from_uci("e2e4"))
            game_id = app._save_game()
            self.assertEqual(app.db.load_game(game_id).moves, (Move.from_uci("e2e4"),))
            app.preset_var.set(app._preset_label("level-5"))
            app._on_preset_changed()
            settings, _ = load_settings(layout.settings)
            self.assertEqual(settings.bot_preset_id, "level-5")
            app.close()

    def test_open_saved_game_to_continue_and_keep_recorded_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = self.make_app(data_layout=DataLayout(Path(tmp) / "data"))
            ongoing = app.db.import_pgn('[Event "Club game"]\n\n1. e4 *')
            ended = app.db.import_pgn("1. d4 d5 1/2-1/2")
            with patch.object(app, "_choose_item", return_value=1):
                app.library_button.invoke()
            self.assertIn(f"#{ongoing}", app.interaction_text.get())
            self.assertIn('[Event "Club game"]', app._current_pgn())
            app._play_move(Move.from_uci("e7e5"))
            self.assertEqual(len(app.game.moves), 2)
            with patch.object(app, "_choose_item", return_value=0), patch(
                "chess_and_chains.ui.app.messagebox.askyesno", side_effect=[False, True],
            ):
                app.library_button.invoke()
                self.assertEqual(app.game.moves[0], Move.from_uci("e2e4"))
                app.library_button.invoke()
            self.assertIn(f"#{ended}", app.interaction_text.get())
            self.assertEqual(app.game.outcome().status, GameStatus.RECORDED_RESULT)
            self.assertEqual(app.board._legal_moves, ())
            self.assertEqual(app.panel_text.get(), "Recorded result: draw")
            self.assertTrue(app._current_pgn().endswith("1/2-1/2"))
            app.close()

    def test_library_reopens_claim_with_reason_and_declared_move(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = self.make_app(data_layout=DataLayout(Path(tmp) / "data"))
            app.controller.new_game(GameSetup(initial_fen="4k3/8/8/8/8/8/8/R3K3 w - - 99 51"))
            app.controller.claim_draw(DrawClaim.FIFTY_MOVE_RULE, Move.from_uci("a1a2"))
            self.assertIsNotNone(app._save_game())
            app.start_game("human-vs-human")
            with patch.object(app, "_choose_item", return_value=0):
                app.library_button.invoke()
            self.assertEqual(app.panel_text.get(), "Draw claimed: 50-move rule by declaring Ra2")
            self.assertEqual(app.game.moves, [])
            self.assertTrue(app._current_pgn().endswith("1/2-1/2"))
            app.close()

    def test_library_keyboard_import_and_export_restore_focus(self):
        with ExitStack() as stack:
            directory = Path(stack.enter_context(tempfile.TemporaryDirectory()))
            app = self.make_app(data_layout=DataLayout(directory / "data"))
            stack.callback(app.close)
            source, target = directory / "game.pgn", directory / "saved.pgn"
            source.write_text("1. e4 e5 *", encoding="utf-8")
            self.root.deiconify()
            self.root.update()
            app.library_button.focus_force()
            self.root.update()

            def press_action(label, key):
                deadline = time.monotonic() + 5
                pending = None
                sent = False
                keypad_bound = False

                def press_when_focused():
                    nonlocal pending, sent, keypad_bound
                    pending = None
                    dialog = self.root.grab_current()
                    content = dialog.winfo_children()[0]
                    button = next(child for child in content.winfo_children()
                                  if isinstance(child, ttk.Button) and child.cget("text") == label)
                    if time.monotonic() >= deadline:
                        dialog.destroy()
                    elif not button.winfo_viewable():
                        pending = self.root.after(10, press_when_focused)
                    elif self.root.focus_get() is not button:
                        button.focus_force()
                        pending = self.root.after(10, press_when_focused)
                    else:
                        sent = True
                        keypad_bound = bool(button.bind("<KP_Enter>"))
                        button.event_generate(f"<{key}>", when="tail")
                        pending = self.root.after(1000, dialog.destroy)

                pending = self.root.after(0, press_when_focused)
                try:
                    app.library_button.invoke()
                finally:
                    if pending is not None:
                        self.root.after_cancel(pending)
                self.assertTrue(sent, f"{label} did not receive focus")
                self.assertTrue(keypad_bound, f"{label} has no keypad Enter binding")
                self.pump_until(lambda: self.root.focus_get() is app.library_button)

            with patch("chess_and_chains.ui.app.filedialog.askopenfilename", return_value=str(source)):
                press_action("Import PGN…", "Return")
            self.assertEqual(app.game.moves, [])
            self.assertIn("Imported game #1", app.interaction_text.get())

            with patch("chess_and_chains.ui.app.filedialog.asksaveasfilename", return_value=str(target)):
                # Win32 Tk cannot synthesize this keysym (it produces keycode 0).
                press_action("Export PGN…", "Return")
            self.assertIn("1. e4 e5 *", target.read_text(encoding="utf-8"))
            press_action("Cancel", "Escape")

    def test_without_data_layout_nothing_is_written(self):
        app = self.make_app()
        app._play_move(Move.from_uci("e2e4"))
        self.assertIsNone(app._save_game())
        self.assertIn("unavailable", app.interaction_text.get())

    def test_copy_pgn_uses_clipboard(self):
        app = self.make_app()
        app._play_move(Move.from_uci("e2e4"))
        app._copy_pgn()
        self.assertIn("1. e4 *", self.root.clipboard_get())

    def test_german_ui(self):
        app = self.make_app(locale="de")
        self.assertEqual(app.panel_text.get(), "Weiß am Zug")
        self.assertIn("ZWEI PERSONEN", app.header_mode_text.get())
        self.assertEqual(app.new_game_button.cget("text"), "Neue Partie")
        self.assertEqual(self.root.title(), f'{app.t("app.window_title")} · {DISPLAY_VERSION}')

    def test_keyboard_shortcut_undo(self):
        app = self.make_app()
        app._play_move(Move.from_uci("e2e4"))
        self.root.deiconify()
        self.root.update()
        app.board.focus_force()
        self.root.update()
        app.board.event_generate("<Control-z>", when="tail")
        self.root.update()
        self.root.withdraw()
        self.assertEqual(app.game.moves, [])

    def test_board_shows_localized_focus_until_tab_moves_on(self):
        app = self.make_app(locale="de")
        self.root.deiconify()
        self.root.update()
        app.board.focus_force()
        self.root.update()
        self.assertEqual(app.interaction_text.get(), "Fokus e2 · Weiß, Bauer")
        self.assertEqual(len(app.board.find_withtag("square-focus")), 2)

        app.board.event_generate("<Return>")
        self.assertEqual(app.interaction_text.get(), "e2 ausgewählt · 2 legale Zielfelder")
        app.board.event_generate("<Up>")
        app.board.event_generate("<Up>")
        self.assertEqual(app.interaction_text.get(), "Fokus e4 · frei")
        app.board.event_generate("<Return>")
        self.assertEqual(app.game.moves, [Move.from_uci("e2e4")])
        self.assertEqual(app.interaction_text.get(), "Fokus e4 · Weiß, Bauer")

        app.board.event_generate("<Tab>")
        self.root.update()
        self.assertEqual(self.root.focus_get(), app.tab_rail.children["play"])
        self.assertEqual(app.board.find_withtag("square-focus"), ())
        self.assertEqual(app.interaction_text.get(), "")

        app.tab_rail.children["play"].event_generate("<Shift-Tab>")
        self.root.update()
        self.assertEqual(self.root.focus_get(), app.board)
        self.assertEqual(app.interaction_text.get(), "Fokus e4 · Weiß, Bauer")
        app.interaction_text.set("Partie #1 in die Bibliothek importiert.")
        app.board.event_generate("<Tab>")
        self.root.update()
        self.assertEqual(app.interaction_text.get(), "Partie #1 in die Bibliothek importiert.")

    def test_play_panel_scrolls_to_focused_engine_settings_in_small_window(self):
        app = self.make_app(locale="de")
        self.root.deiconify()
        self.root.geometry("860x700")
        canvas = app.play_canvas
        # Force a tall status area independently of the platform font.
        app.play_panel.grid_rowconfigure(app.bot_label.grid_info()["row"], minsize=720)
        self.pump_until(lambda: canvas.winfo_height() > 100 and app.play_panel.winfo_height() > canvas.winfo_height())
        self.root.update()
        self.assertEqual(int(canvas.cget("scrollregion").split()[-1]), app.play_panel.winfo_height())
        self.assertEqual(canvas.yview()[0], 0)
        self.assertLess(canvas.yview()[1], 1)
        app.engine_button.event_generate("<FocusIn>")
        self.root.update()
        bottom = app.engine_button.winfo_rooty() + app.engine_button.winfo_height()
        self.assertLessEqual(bottom, canvas.winfo_rooty() + canvas.winfo_height() + 1)
        self.assertGreater(canvas.yview()[0], 0)
        app.new_game_button.event_generate("<FocusIn>")
        self.root.update()
        self.assertGreaterEqual(app.new_game_button.winfo_rooty(), canvas.winfo_rooty() - 1)
        self.assertGreater(app.board._square_size, 20)

    def test_small_window_keeps_board_usable(self):
        app = self.make_app()
        self.root.deiconify()
        self.root.geometry("860x700")
        self.root.update()
        self.assertGreater(app.board._square_size, 20)
        self.root.withdraw()


class PieceRendererContractTests(unittest.TestCase):
    def test_bundled_owner_svg_set_meets_the_contract(self):
        directory = ROOT / "src" / "chess_and_chains" / "ui" / "piece_assets"
        for assets in (directory, directory / "top"):
            with self.subTest(assets=assets):
                report = validate_svg_piece_set(assets)
                self.assertTrue(report.ok, report.problems)

    def test_cli_selects_top_view_for_the_session(self):
        from chess_and_chains.__main__ import main

        with patch("chess_and_chains.ui.launch") as launch:
            self.assertEqual(main(["--piece-view", "top"]), 0)
            launch.assert_called_once_with(board_design=None, top_pieces=True)

    def test_svg_contract_accepts_clean_set_and_rejects_unsafe_files(self):
        clean = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45"><circle cx="22" cy="22" r="10"/></svg>'
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.assertFalse(validate_svg_piece_set(folder).ok)
            for name in PIECE_FILE_NAMES:
                (folder / name).write_text(clean)
            (folder / "PROVENANCE.md").write_text("author: owner")
            self.assertTrue(validate_svg_piece_set(folder).ok)
            (folder / "wK.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><script>x</script></svg>')
            (folder / "wQ.svg").write_text('<!DOCTYPE svg [<!ENTITY a "b">]><svg viewBox="0 0 1 1"/>')
            (folder / "wR.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1 1"><image xlink:href="https://x.invalid/a.png"/></svg>')
            (folder / "wB.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect onload="x()"/></svg>')
            problems = "\n".join(validate_svg_piece_set(folder).problems)
            for expected in ("forbidden element <script>", "DTD/entities", "external reference", "event handler", "viewBox"):
                self.assertIn(expected, problems)


if __name__ == "__main__":
    unittest.main()
