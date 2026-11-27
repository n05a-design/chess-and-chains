"""Tk app integration: mock-bot vertical slice, non-blocking UI, puzzles, storage.

Runs a real Tk root (withdrawn). The bot is the project-owned mock UCI
engine in a subprocess; this is not a test against a real chess engine.
"""
import sys
import tempfile
import threading
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
from chess_and_chains.chess import Color, DrawClaim, GameStatus, Move, Piece, PieceType, parse_square, to_fen  # noqa: E402
from chess_and_chains.engines.bot import EngineConfig, UCIBot  # noqa: E402
from chess_and_chains.engines.mock_engine import ENGINE_NAME  # noqa: E402
from chess_and_chains.game.clock import TimeControl  # noqa: E402
from chess_and_chains.game import BotStatus, GameSetup  # noqa: E402
from chess_and_chains.puzzles import load_demo_pack, write_pack  # noqa: E402
from chess_and_chains.storage import DataLayout, load_settings, update_settings  # noqa: E402
from chess_and_chains.ui.app import ChessApp, EngineDialog  # noqa: E402
from chess_and_chains.ui.branding import brand_image  # noqa: E402
from chess_and_chains.ui.board import screen_cell  # noqa: E402
from chess_and_chains.ui.dialogs import PositionDialog  # noqa: E402
from chess_and_chains.ui.replay import ReplayDialog  # noqa: E402
from chess_and_chains.ui.text_board import TextBoardDialog  # noqa: E402
from chess_and_chains.ui.theme import RoundedButton  # noqa: E402
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


def _png_size(name: str) -> tuple[int, int]:
    """Width/height of a generated brand PNG (aspect follows the current Logo 01 master)."""
    from chess_and_chains.ui.branding import asset_bytes

    header = asset_bytes(name)[16:24]
    return int.from_bytes(header[:4], "big"), int.from_bytes(header[4:], "big")


def _hex_rgb(value: str) -> tuple[int, int, int]:
    return (int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16))


class AppTestCase(unittest.TestCase):
    def make_app(self, *, tk_dpi=None, **kwargs):
        self.root = create_root(self)
        if tk_dpi is not None:
            original_scaling = self.root.tk.call("tk", "scaling")
            self.root.tk.call("tk", "scaling", tk_dpi / 72)
        kwargs.setdefault("locale", "en")
        self.app = ChessApp(self.root, **kwargs)
        self.addCleanup(self.app.close)
        if tk_dpi is not None:
            self.addCleanup(self.root.tk.call, "tk", "scaling", original_scaling)
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
                        if isinstance(child, (tk.Button, RoundedButton)) and child.cget("text") == "Turm")
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
                            if isinstance(child, (tk.Button, RoundedButton)) and child.cget("text") == "Rook")
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


class CapturedMaterialUiTests(AppTestCase):
    def setUp(self) -> None:
        self.make_app(locale="de")

    def test_14_app_material_bars_initial_state(self) -> None:
        """Beide Materialanzeigen sind im Brettbereich initial vorhanden und leer."""
        self.assertTrue(hasattr(self.app, "top_material_bar"))
        self.assertTrue(hasattr(self.app, "bottom_material_bar"))
        self.assertEqual(self.app.top_material_bar.player_color, Color.BLACK)
        self.assertEqual(self.app.bottom_material_bar.player_color, Color.WHITE)
        top_mat = self.app.top_material_bar.material
        bot_mat = self.app.bottom_material_bar.material
        self.assertIsNotNone(top_mat)
        self.assertIsNotNone(bot_mat)
        assert top_mat is not None and bot_mat is not None
        self.assertEqual(top_mat.captures, ())
        self.assertEqual(bot_mat.captures, ())
        self.assertIsNone(top_mat.advantage)
        self.assertIsNone(bot_mat.advantage)

    def test_15_app_material_bars_capture_and_orientation_flip(self) -> None:
        """Schlagzug und Brettdrehung: Anzeigen tauschen ihre Positionen exakt."""
        # 1. e4 d5 2. exd5
        self.app.controller.play_human(Move.from_uci("e2e4"))
        self.app.controller.play_human(Move.from_uci("d7d5"))
        self.app.controller.play_human(Move.from_uci("e4d5"))
        self.root.update_idletasks()

        # Normal orientation ("white"):
        # top = Black (0 captures, no advantage)
        # bottom = White (captured black pawn, +1 advantage)
        self.assertEqual(self.app.top_material_bar.player_color, Color.BLACK)
        self.assertEqual(self.app.bottom_material_bar.player_color, Color.WHITE)
        self.assertIsNone(self.app.top_material_bar.material.advantage)
        self.assertEqual(self.app.bottom_material_bar.material.advantage, 1)
        self.assertEqual(len(self.app.bottom_material_bar.material.captures), 1)

        # Flip board
        self.app._flip_board()
        self.root.update_idletasks()
        self.assertEqual(self.app.orientation, "black")
        # In black orientation:
        # top = White (captured black pawn, +1 advantage)
        # bottom = Black (0 captures, no advantage)
        self.assertEqual(self.app.top_material_bar.player_color, Color.WHITE)
        self.assertEqual(self.app.bottom_material_bar.player_color, Color.BLACK)
        self.assertEqual(self.app.top_material_bar.material.advantage, 1)
        self.assertIsNone(self.app.bottom_material_bar.material.advantage)

        # Flip back
        self.app._flip_board()
        self.root.update_idletasks()
        self.assertEqual(self.app.top_material_bar.player_color, Color.BLACK)
        self.assertEqual(self.app.bottom_material_bar.player_color, Color.WHITE)

    def test_16_app_material_undo_and_redo(self) -> None:
        """Undo und Redo im GUI aktualisieren die Materialanzeigen."""
        self.app.controller.play_human(Move.from_uci("e2e4"))
        self.app.controller.play_human(Move.from_uci("d7d5"))
        self.app.controller.play_human(Move.from_uci("e4d5"))
        self.root.update_idletasks()

        self.assertEqual(self.app.bottom_material_bar.material.advantage, 1)

        # Undo
        self.app.controller.undo()
        self.root.update_idletasks()
        self.assertIsNone(self.app.bottom_material_bar.material.advantage)
        self.assertEqual(self.app.bottom_material_bar.material.captures, ())

        # Redo
        self.app.controller.redo()
        self.root.update_idletasks()
        self.assertEqual(self.app.bottom_material_bar.material.advantage, 1)
        self.assertEqual(len(self.app.bottom_material_bar.material.captures), 1)

    def test_17_replay_dialog_material_tracking(self) -> None:
        """ReplayDialog zeigt den Materialstand an jedem Zugschritt."""
        self.app.controller.play_human(Move.from_uci("e2e4"))
        self.app.controller.play_human(Move.from_uci("d7d5"))
        self.app.controller.play_human(Move.from_uci("e4d5"))

        dialog = ReplayDialog(
            self.app.root,
            self.app.game,
            self.app.t,
            self.app._board_artwork,
            self.app.board.renderer,
            self.app.orientation,
            theme=self.app.theme,
        )
        try:
            # At start (index 0)
            dialog.show(0)
            self.assertIsNone(dialog.bottom_material_bar.material.advantage)
            self.assertEqual(dialog.bottom_material_bar.material.captures, ())

            # At index 3 (after exd5)
            dialog.show(3)
            self.assertEqual(dialog.bottom_material_bar.material.advantage, 1)
            self.assertEqual(len(dialog.bottom_material_bar.material.captures), 1)
        finally:
            dialog.destroy()


class SessionRecoveryUiTests(AppTestCase):
    def test_startup_resumes_autosave_with_redo_without_library_entry(self):
        with tempfile.TemporaryDirectory() as folder:
            layout = DataLayout(Path(folder))
            app = self.make_app(data_layout=layout)
            app.start_game("human-vs-human")
            app._play_move(Move.from_uci("e2e4"))
            app._play_move(Move.from_uci("e7e5"))
            app._undo()
            self.assertEqual(app.db.list_games(), [])
            app.close()

            resumed = self.make_app(data_layout=layout)
            self.assertEqual(resumed.game.moves, [Move.from_uci("e2e4")])
            self.assertTrue(resumed.controller.view().can_redo)
            resumed._redo()
            self.assertEqual(resumed.game.moves, [Move.from_uci("e2e4"), Move.from_uci("e7e5")])
            resumed.close()


    def test_bot_resume_preserves_color_and_does_not_fall_back_to_other_engine(self):
        with tempfile.TemporaryDirectory() as folder:
            layout = DataLayout(Path(folder))
            factory = mock_factory()
            app = self.make_app(data_layout=layout, provider_factory=factory)
            app.start_game("human-vs-bot-black")
            self.pump_until(lambda: len(app.game.moves) == 1)
            saved, _ = app.db.load_session()
            app.close()

            # The app refuses the mismatched identity, then permits an explicit retry.
            resumed = self.make_app(data_layout=layout, provider_factory=factory)
            self.assertEqual(resumed.controller.setup.bot_color, Color.WHITE)
            self.assertEqual(resumed.orientation, "black")
            self.assertEqual(resumed.db.load_session()[0], saved)
            self.assertEqual(resumed.game.timeline().moves, saved.timeline.moves)
            resumed.close()
            with patch.object(ChessApp, "_engine_reference", return_value="other engine"):
                blocked = self.make_app(data_layout=layout, provider_factory=factory)
            self.assertTrue(blocked._session_blocked)
            self.assertEqual(blocked.game.moves, [])
            self.assertEqual(blocked.db.load_session()[0], saved)
            blocked._resume_session()
            self.assertFalse(blocked._session_blocked)
            self.assertEqual(blocked.controller.setup.bot_color, Color.WHITE)
            blocked.close()

    def test_library_continues_saved_bot_game_without_mutating_saved_record(self):
        with tempfile.TemporaryDirectory() as folder:
            layout = DataLayout(Path(folder))
            factory = mock_factory()
            app = self.make_app(data_layout=layout, provider_factory=factory)
            app.start_game("human-vs-bot-white")
            before = app.db.load_game(app._save_game())
            app.start_game("human-vs-human")
            app._continue_saved_game(before)
            self.assertEqual(app.controller.setup.bot_color, Color.BLACK)
            self.assertEqual(app.db.load_game(before.id), before)
            app.close()


    def test_custom_clock_rejects_invalid_input_then_starts_with_entered_values(self):
        app = self.make_app()

        def fill_dialog(_root, dialog):
            frame, = dialog.winfo_children()
            initial, increment = [widget for widget in frame.winfo_children() if isinstance(widget, ttk.Entry)]
            start, _cancel = [widget for widget in frame.winfo_children() if isinstance(widget, ttk.Button)]
            initial.delete(0, "end")
            initial.insert(0, "0")
            start.invoke()
            self.assertTrue(dialog.winfo_exists())
            self.assertIsNone(app.controller.setup.time_control)
            initial.delete(0, "end")
            initial.insert(0, "42")
            increment.delete(0, "end")
            increment.insert(0, "7")
            start.invoke()

        with patch.object(app, "_choose_item", side_effect=lambda _title, labels, _confirm: len(labels) - 1), patch(
            "chess_and_chains.ui.dialogs.modal_session.wait_modal", side_effect=fill_dialog,
        ):
            app._new_timed_game()
        self.assertEqual(app.controller.setup.time_control, TimeControl(42_000, 7000))
        self.assertTrue(app.controller.view().clock_running)

    def test_timeout_updates_native_status_and_archives_pgn_termination(self):
        with tempfile.TemporaryDirectory() as folder:
            app = self.make_app(data_layout=DataLayout(Path(folder)), locale="de")
            now = 0
            app.controller._now = lambda: now
            app.controller.new_game(GameSetup(initial_fen="7k/8/5K2/6Q1/8/8/8/8 b - - 0 1",
                                              time_control=TimeControl(1000)))
            now = 1_000_000_000
            app.controller.poll()
            self.assertEqual(app.panel_text.get(), "Weiß gewinnt auf Zeit.")
            row = app.db.load_game(app._save_game())
            self.assertEqual(row.result, "1-0")
            self.assertEqual(dict(row.pgn_tags)["Termination"], "time forfeit")
            session, _ = app.db.load_session()
            self.assertEqual(session.clock.current.remaining_ms(Color.BLACK), 0)
            self.assertEqual(session.timeline.result, "1-0")
            app.close()

    def test_timed_session_starts_paused_with_saved_times_after_reopen(self):
        with tempfile.TemporaryDirectory() as folder:
            layout = DataLayout(Path(folder))
            app = self.make_app(data_layout=layout)
            now = 1_000_000_000
            app.controller._now = lambda: now
            app.start_game("human-vs-human", time_control=TimeControl(60_000, 2000))
            now += 1_250_000_000
            app._play_move(Move.from_uci("e2e4"))
            now += 3_500_000_000
            app.close()

            resumed = self.make_app(data_layout=layout)
            reading = resumed.controller.clock_reading()
            self.assertEqual((reading.remaining_ms(Color.WHITE), reading.remaining_ms(Color.BLACK)), (60_750, 56_500))
            self.assertFalse(resumed.controller.view().clock_running)
            self.assertEqual(resumed.game.moves, [Move.from_uci("e2e4")])
            self.assertIn("Black 0:57", resumed.clock_text.get())
            resumed.controller.toggle_clock()
            self.assertTrue(resumed.controller.view().clock_running)
            resumed.close()


class AnalysisArchiveUiTests(AppTestCase):
    def test_library_analysis_is_reopened_without_starting_an_engine(self):
        from chess_and_chains.engines.analysis import AnalysisMode
        from tests.test_engine_analysis import FIXTURE

        with tempfile.TemporaryDirectory() as folder:
            layout = DataLayout(Path(folder))
            app = self.make_app(data_layout=layout)
            app._play_move(Move.from_uci("e2e4"))
            game_id = app._save_game()
            original = app.db.load_game(game_id)
            config = EngineConfig(
                (sys.executable, "-u", "-c", FIXTURE, str(Path(folder) / "uci.log"), "normal"),
                "Protocol fixture", False, "fixture",
            )

            def wait_for_report(_root, window):
                self.pump_until(lambda: bool(app.db.analysis_reports()))
                window.destroy()

            with patch("chess_and_chains.ui.app.resolve_engine_config", return_value=(config, None)), patch(
                "chess_and_chains.ui.app.modal_session.wait_modal", side_effect=wait_for_report,
            ):
                app._analyse_game(original.to_game(), AnalysisMode.GAME, source_game_id=game_id)
            self.assertEqual(app.db.load_game(game_id), original)
            app.close()

            reopened = self.make_app(data_layout=layout)
            displayed = []

            def capture_output(_root, window):
                text, = [item for frame in window.winfo_children() for item in frame.winfo_children()
                         if isinstance(item, tk.Text)]
                displayed.append(text.get("1.0", "end"))
                window.destroy()

            with patch.object(reopened, "_choose_item", return_value=0), patch(
                "chess_and_chains.ui.app.modal_session.wait_modal", side_effect=capture_output,
            ):
                reopened._open_analysis_reports()
            self.assertIsNone(reopened._analysis)
            self.assertIn("Critical moments", displayed[0])
            self.assertIn("d2d4", displayed[0])
            reopened.close()


class PuzzleUiTests(AppTestCase):
    def test_mate_chain_resumes_a_hint_and_grades_once_after_reopening(self):
        with tempfile.TemporaryDirectory() as folder:
            layout = DataLayout(Path(folder))
            app = self.make_app(data_layout=layout)
            app._open_mate_chain()
            self.assertIn("1/3", app.panel_text.get())
            first = app.puzzle.puzzle
            app._puzzle_hint()
            app.close()

            resumed = self.make_app(data_layout=layout)
            resumed._open_mate_chain()
            self.assertEqual(resumed.puzzle.puzzle, first)
            self.assertEqual(resumed.puzzle.hints_used, 1)
            self.assertEqual(resumed._puzzle_hint_stage, 1)
            while resumed.puzzle.expected_move is not None:
                resumed._play_move(resumed.puzzle.expected_move)
            self.assertEqual(resumed.db.puzzle_progress(resumed.pack.manifest.pack_id, first.puzzle_id).attempts, 1)
            resumed.close()

            following = self.make_app(data_layout=layout)
            following._open_mate_chain()
            self.assertEqual(following.puzzle_index, 1)
            self.assertNotEqual(following.puzzle.puzzle, first)
            self.assertEqual(following.db.puzzle_progress(following.pack.manifest.pack_id, first.puzzle_id).attempts, 1)
            following.close()

    def test_due_filter_reads_persisted_attempt_dates(self):
        with tempfile.TemporaryDirectory() as folder:
            layout = DataLayout(Path(folder))
            app = self.make_app(data_layout=layout)
            pack_id = app.pack.manifest.pack_id
            due, future = app.pack.puzzles[:2]
            for puzzle in (due, future):
                app.db.record_puzzle_attempt(pack_id, puzzle.puzzle_id, solved=True, mistakes=0,
                                             hints_used=0, duration_ms=1000)
            app.db._conn.execute(
                "UPDATE puzzle_attempts SET attempted_utc = ? WHERE pack_id = ? AND puzzle_id = ?",
                ("2000-01-01", pack_id, due.puzzle_id),
            )
            app.tab_rail.set_active("puzzles")
            app.puzzle_status_filter.current(3)
            app._apply_puzzle_filters()
            self.assertEqual(app._puzzle_selection, (due,))
            self.assertEqual(app.puzzle.puzzle, due)
            app.close()

    def test_staged_hints_and_retry_keep_completed_attempts_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = self.make_app(data_layout=DataLayout(Path(tmp) / "data"), locale="de")
            try:
                app.tab_rail.set_active("puzzles")
                session = app.puzzle
                first_position = session.state
                move = session.expected_move
                app.hint_button.invoke()
                self.assertEqual(app.board._hint_square, move.from_square)
                self.assertEqual(app.hint_button.cget("text"), "Zielfeld zeigen")
                app.hint_button.invoke()
                self.assertEqual(app.board._hint_square, move.to_square)
                self.assertEqual(session.hints_used, 2)
                self.assertEqual(app.hint_button.cget("state"), tk.DISABLED)
                with patch("chess_and_chains.ui.app.messagebox.askyesno", return_value=False):
                    app.retry_puzzle_button.invoke()
                self.assertIs(app.puzzle, session)
                app._play_move(move)
                first = app.db.latest_puzzle_attempt("demo", session.puzzle.puzzle_id)
                self.assertEqual(first.hints_used, 2)

                app.retry_puzzle_button.invoke()
                self.assertEqual(app.puzzle.state, first_position)
                self.assertEqual(app.puzzle.hints_used, 0)
                self.assertIsNone(app.board._hint_square)
                self.assertEqual(app.hint_button.cget("state"), tk.NORMAL)
                app._play_move(app.puzzle.expected_move)
                progress = app.db.puzzle_progress("demo", session.puzzle.puzzle_id)
                self.assertEqual((progress.attempts, progress.clean_solves), (2, 1))
            finally:
                app.close()

    def test_training_filter_uses_saved_attempts_and_retires_clean_solves_on_next(self):
        with tempfile.TemporaryDirectory() as tmp:
            layout = DataLayout(Path(tmp) / "data")
            app = self.make_app(data_layout=layout, locale="de")
            first, second, third, *_ = app.pack.puzzles
            pack_id = app.pack.manifest.pack_id
            try:
                for puzzle, solved, mistakes, hints in (
                    (first, False, 2, 1), (second, True, 0, 0), (third, True, 0, 1),
                ):
                    app.db.record_puzzle_attempt(pack_id, puzzle.puzzle_id, solved=solved, mistakes=mistakes,
                                                 hints_used=hints, duration_ms=8000)
                app.db.record_puzzle_attempt("different-pack", first.puzzle_id, solved=True, mistakes=0,
                                             hints_used=0, duration_ms=1000)
                app.tab_rail.set_active("puzzles")
                self.assertTrue(app.puzzle_status_filter.bind("<<ComboboxSelected>>"))

                def select(value):
                    app.puzzle_status_filter.current(value)
                    # A withdrawn Aqua window cannot reliably deliver virtual selection events.
                    app._apply_puzzle_filters()

                select(1)  # Unsolved, including revealed and never attempted.
                self.assertIn(first, app._puzzle_selection)
                self.assertNotIn(third, app._puzzle_selection)
                select(2)  # Review only attempted puzzles without a clean solve.
                self.assertEqual(app._puzzle_selection, (first, third))
                history = app.puzzle_history_text.get()
                self.assertIn("Zuletzt: ungelöst", history)
                self.assertIn("Fehler: 2 · Hinweise: 1 · Zeit: 0:08", history)
                app._play_move(app.puzzle.expected_move)
                self.assertTrue(app.puzzle.finished)
                self.assertIs(app.puzzle.puzzle, first)
                self.assertIn("Versuche: 2", app.puzzle_history_text.get())
                app.next_puzzle_button.invoke()
                self.assertEqual(app._puzzle_selection, (third,))
                self.assertIs(app.puzzle.puzzle, third)
                for move in third.solution[::2]:
                    app._play_move(move)
                self.assertTrue(app.puzzle.solved)
                app.next_puzzle_button.invoke()
                self.assertIsNone(app.puzzle)
                self.assertEqual(app.puzzle_history_text.get(), "")
                self.assertEqual(app.next_puzzle_button.cget("state"), tk.DISABLED)
                select(0)
                self.assertEqual(app._puzzle_selection, app.pack.puzzles)
            finally:
                app.close()

            reopened = self.make_app(data_layout=layout, locale="de")
            try:
                reopened.tab_rail.set_active("puzzles")
                self.assertIn("Versuche: 2", reopened.puzzle_history_text.get())
                self.assertIn("Zuletzt: gelöst", reopened.puzzle_history_text.get())
            finally:
                reopened.close()

    def test_local_pack_import_switch_and_restart_keep_progress_separate(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        layout = DataLayout(root / "data")
        source = root / "source"
        puzzle = load_demo_pack().puzzles[0]
        write_pack(source, [puzzle], pack_id="local-study", version="3", source="Project study", license_note="MPL-2.0")
        app = self.make_app(data_layout=layout)
        app.tab_rail.set_active("puzzles")
        app._play_move(app.puzzle.expected_move)
        self.assertEqual(app.db.solved_puzzle_ids("demo"), {puzzle.puzzle_id})

        def choose_import(_title, _labels, _confirm, **options):
            options["actions"][0][1](None)

        with patch.object(app, "_choose_item", side_effect=choose_import), patch(
            "chess_and_chains.ui.app.filedialog.askdirectory", return_value=str(source),
        ):
            app.puzzle_pack_button.invoke()
        self.assertTrue(app._pack_loading)
        self.pump_until(lambda: not app._pack_loading)
        self.assertEqual(app.pack.manifest.pack_id, "local-study")
        self.assertIn("Project study", app.puzzle_pack_text.get())
        self.assertEqual(app.puzzle_progress_text.get(), "Solved 0 of 1 in this selection.")
        self.assertEqual(app.puzzle.puzzle.puzzle_id, puzzle.puzzle_id)
        app._play_move(app.puzzle.expected_move)
        self.assertEqual(app.db.solved_puzzle_ids("local-study"), {puzzle.puzzle_id})
        app.puzzle_theme_filter.current(app.puzzle_theme_filter.cget("values").index("Mate"))
        app.puzzle_rating_filter.current(1)
        app._apply_puzzle_filters()

        with patch.object(app, "_choose_item", return_value=0) as chooser:
            app.puzzle_pack_button.invoke()
        self.assertEqual(chooser.call_args.args[1], ("Built-in demo", "local-study"))
        self.assertEqual(chooser.call_args.kwargs["initial_index"], 1)
        self.assertEqual(app.pack.manifest.pack_id, "demo")
        self.assertEqual(app.puzzle_theme_filter.current(), 0)
        self.assertEqual(app.puzzle_rating_filter.current(), 0)
        self.assertEqual(app.puzzle_progress_text.get(), "Solved 1 of 5 in this selection.")
        with patch.object(app, "_choose_item", return_value=1):
            app.puzzle_pack_button.invoke()
        self.pump_until(lambda: not app._pack_loading)
        self.assertEqual(load_settings(layout.settings)[0].last_pack_id, "local-study")
        app.close()

        reopened = self.make_app(data_layout=layout, locale="de")
        self.pump_until(lambda: not reopened._pack_loading)
        self.assertEqual(reopened.active_panel, "play")
        reopened.tab_rail.set_active("puzzles")
        self.assertEqual(reopened.pack.manifest.pack_id, "local-study")
        self.assertEqual(reopened.puzzle_progress_text.get(), "1 von 1 Rätseln dieser Auswahl gelöst.")

    def test_invalid_pack_validation_keeps_the_current_session_responsive(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        app = self.make_app(data_layout=DataLayout(root / "data"), locale="de")
        app.tab_rail.set_active("puzzles")
        session = app.puzzle
        started = threading.Event()
        release = threading.Event()
        self.addCleanup(release.set)
        install = app._pack_library.install

        def slow_install(path):
            started.set()
            release.wait(5)
            return install(path)

        with patch.object(app._pack_library, "install", side_effect=slow_install), patch(
            "chess_and_chains.ui.app.filedialog.askdirectory", return_value=str(root / "invalid-pack"),
        ):
            app._pick_pack_folder()
            try:
                self.pump_until(started.is_set)
                self.assertIn("wird geprüft", app.puzzle_pack_feedback.get())
                self.assertEqual(app.puzzle_pack_button.cget("state"), tk.DISABLED)
                app._puzzle_hint()
                self.assertEqual(session.hints_used, 1)
            finally:
                release.set()
            self.pump_until(lambda: not app._pack_loading)
        self.assertIn("konnte nicht geöffnet", app.puzzle_pack_feedback.get())
        self.assertIs(app.puzzle, session)
        self.assertEqual(app.puzzle_pack_button.cget("state"), tk.NORMAL)
        self.assertIsNone(app.settings.last_pack_id)

    def test_missing_saved_pack_falls_back_to_demo_without_rewriting_preferences(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        layout = DataLayout(root / "data")
        update_settings(layout.settings, last_pack_id="missing-pack")
        app = self.make_app(data_layout=layout)
        self.pump_until(lambda: not app._pack_loading)
        app.tab_rail.set_active("puzzles")
        self.assertEqual(app.pack.manifest.pack_id, "demo")
        self.assertIsNotNone(app.puzzle)
        self.assertIn("Could not open the puzzle pack", app.puzzle_pack_feedback.get())
        self.assertEqual(load_settings(layout.settings)[0].last_pack_id, "missing-pack")

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
                ("signet", 1, _png_size("signet.png")), ("app-icon", 1, (256, 256)),
                ("brand-emblem", 1, (96, 96)), ("wordmark", 1, (254, 40)),
            ):
                image = brand_image(root, name, scale=scale)
                self.assertEqual((image.width(), image.height()), expected_size)
                self.assertTrue(image.transparency_get(0, 0))

    @staticmethod
    def _opaque_colors(photo: tk.PhotoImage) -> set[tuple[int, int, int]]:
        return {
            tuple(int(v) for v in photo.get(x, y))
            for y in range(photo.height())
            for x in range(photo.width())
            if not photo.transparency_get(x, y)
        }

    def test_logo_roles_signet_follows_theme_emblem_and_app_icon_keep_colours(self):
        """Logo 01 is tinted in every theme/accent; Logo 02 and 03 keep the master colours."""
        from chess_and_chains.ui.appearance_dialog import AppearanceDialog
        from chess_and_chains.ui.theme import ACCENT_CHOICES, THEMES

        app = self.make_app()
        self.root.deiconify()
        self.root.update()
        logo = app.header_logo
        for theme_id in (k for k in THEMES if k != "w06-provisional"):
            for accent, _label in ACCENT_CHOICES:
                palette = app.apply_appearance(theme_id=theme_id, accent_choice=accent, persist=False)
                self.root.update()
                if not logo.winfo_manager():
                    continue
                self.assertEqual(self._opaque_colors(logo._logo_image), {_hex_rgb(palette.view_title)})
                self.assertTrue(logo._logo_image.transparency_get(0, 0))
        # Logo 02 in the About dialog keeps yellow, blue and the dark board.
        about = app.show_about_dialog(modal=False)
        self.addCleanup(lambda: about.winfo_exists() and about.destroy())
        emblem_colours = self._opaque_colors(about._about_emblem)
        for colour in ((255, 220, 11), (36, 71, 216), (23, 25, 32)):
            self.assertIn(colour, emblem_colours)
        about.destroy()
        # Logo 03 is the window icon, never tinted.
        icon_colours = self._opaque_colors(app._window_icons[-1])
        self.assertIn((255, 220, 11), icon_colours)
        self.assertTrue(app._window_icons[0].transparency_get(0, 0))
        # Theme colour changes while the settings dialog is open update its signet preview.
        dialog = app.open_appearance_dialog(modal=False)
        self.addCleanup(lambda: dialog.winfo_exists() and dialog.destroy())
        self.assertIsInstance(dialog, AppearanceDialog)
        before = dialog._swatch_canvas._logo_color
        dialog.accent_var.set("flag")
        dialog._on_any_change("flag")
        self.root.update()
        self.assertEqual(dialog._swatch_canvas._logo_color, dialog._palette.view_title)
        self.assertNotEqual(dialog._swatch_canvas._logo_color, before)

    def test_in_app_monochrome_logo_renders_transparent_fallback_without_svg(self):
        from chess_and_chains.ui.branding import in_app_logo_photo

        root = create_root(self)
        with patch("chess_and_chains.ui.branding.has_svg_support", return_value=False):
            photo = in_app_logo_photo(root, 44, "#0767C7")
            self.assertEqual(photo.height(), 44)
            self.assertTrue(photo.transparency_get(0, 0))
            opaque = {
                tuple(int(v) for v in photo.get(x, y))
                for y in range(photo.height())
                for x in range(photo.width())
                if not photo.transparency_get(x, y)
            }
            self.assertEqual(opaque, {(7, 103, 199)})

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
            lit_side = root.tk.call(image, "get", 20, 35)[0]
            shaded_side = root.tk.call(image, "get", 33, 35)[0]
            self.assertGreaterEqual(abs(lit_side - shaded_side), minimum_drop)

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

        # The top-view disc extends farther sideways than the V.06 front-view king.
        front = OwnerSvgPieces()
        band = PIECE_FALLBACK_SIZES.index(64)
        self.assertTrue(front._copy_png_piece(app.board, "wK.svg", band).transparency_get(10, 32))
        self.assertFalse(renderer._copy_png_piece(app.board, "wK.svg", band).transparency_get(10, 32))

    def test_piece_images_share_the_visible_dimensions_within_each_view(self):
        root = create_root(self)
        canvas = tk.Canvas(root)
        # Render at 2× so that the half-unit edges land on whole pixels.
        size = 128
        band = PIECE_FALLBACK_SIZES.index(size)
        v06_bounds = {
            "wK.svg": (30, 14, 97, 107), "bK.svg": (30, 14, 97, 107),
            "wQ.svg": (31, 18, 95, 107), "bQ.svg": (31, 18, 95, 107),
            "wR.svg": (30, 18, 97, 107), "bR.svg": (30, 18, 97, 107),
            "wB.svg": (33, 18, 94, 107), "bB.svg": (33, 18, 94, 107),
            "wN.svg": (31, 18, 96, 107), "bN.svg": (31, 17, 96, 107),
            "wP.svg": (36, 18, 91, 107), "bP.svg": (36, 18, 91, 107),
        }
        for top_view in (False, True):
            renderer = OwnerSvgPieces(top_view=top_view)
            for name in PIECE_FILE_NAMES:
                expected = (11, 11, 116, 116) if top_view else v06_bounds[name]
                with self.subTest(top_view=top_view, piece=name):
                    tile = renderer._copy_png_piece(canvas, name, band)
                    visible = [(x, y) for y in range(size) for x in range(size)
                               if not tile.transparency_get(x, y)]
                    xs, ys = zip(*visible)
                    self.assertEqual((min(xs), min(ys), max(xs), max(ys)), expected)


class TextBoardUiTests(AppTestCase):
    def test_real_keys_select_move_and_escape_restores_focus(self):
        app = self.make_app()
        app.controller.new_game(GameSetup(initial_fen="4k3/8/8/8/8/8/8/RR2K3 w - - 0 1"))
        self.root.deiconify()
        self.root.update()
        app.text_board_button.focus_force()
        self.root.update()
        errors = []

        def drive():
            dialog = app._text_board
            try:
                self.assertIsInstance(dialog, TextBoardDialog)
                dialog.pieces.focus_force()
                self.root.update()
                self.assertIs(self.root.focus_get(), dialog.pieces)
                initial_index = dialog.pieces.curselection()[0]
                dialog.pieces.event_generate("<Down>", when="tail")
                self.root.update()
                self.assertEqual(dialog.pieces.curselection(), (initial_index + 1,))
                dialog.pieces.event_generate("<Return>", when="tail")
                self.root.update()
                self.assertIs(self.root.focus_get(), dialog.targets)
                self.assertTrue(dialog.targets.bind("<KP_Enter>"))
                expected = dialog._targets[0]
                dialog.targets.event_generate("<Return>", when="tail")
                self.root.update()
                self.assertEqual(app.game.moves, [expected])
                self.assertIs(self.root.focus_get(), dialog.pieces)
                dialog.pieces.event_generate("<Escape>", when="tail")
                self.root.update()
                self.assertFalse(dialog.winfo_exists())
            except Exception as error:
                errors.append(error)
            finally:
                if dialog is not None and dialog.winfo_exists():
                    dialog.destroy()

        self.root.after(0, drive)
        app.text_board_button.invoke()
        if errors:
            raise errors[0]
        self.assertIs(self.root.focus_lastfor(), app.text_board_button)

    def test_text_board_plays_a_promotion_and_a_puzzle_via_the_same_controller(self):
        app = self.make_app(locale="de")
        app.controller.new_game(GameSetup(initial_fen="4k3/P7/8/8/8/8/8/4K3 w - - 0 1"))
        dialog = TextBoardDialog(self.root, app.t, app._play_move)
        app._text_board = dialog
        try:
            app._refresh()
            index = dialog._sources.index(parse_square("a7"))
            dialog.pieces.selection_clear(0, tk.END)
            dialog.pieces.selection_set(index)
            dialog._select_piece()
            self.assertIn("a8 · Turm", dialog.targets.get(0, tk.END))
            index = dialog._targets.index(Move.from_uci("a7a8r"))
            dialog.targets.selection_clear(0, tk.END)
            dialog.targets.selection_set(index)
            dialog.play_button.invoke()
            self.assertEqual(app.game.moves, [Move.from_uci("a7a8r")])

            app.tab_rail.set_active("puzzles")
            expected = app.puzzle.expected_move
            index = dialog._sources.index(expected.from_square)
            dialog.pieces.selection_clear(0, tk.END)
            dialog.pieces.selection_set(index)
            dialog._select_piece()
            index = dialog._targets.index(expected)
            dialog.targets.selection_clear(0, tk.END)
            dialog.targets.selection_set(index)
            dialog.play_button.invoke()
            self.assertTrue(app.puzzle.solved)
            self.assertEqual(dialog.targets.size(), 0)
            self.assertTrue(dialog.play_button.instate(("disabled",)))
        finally:
            app._text_board = None
            dialog.destroy()


class PositionExchangeUiTests(AppTestCase):
    def test_position_file_copy_save_and_continue_from_black_to_move(self):
        fen = "r3k2r/8/8/8/3pP3/8/8/R3K2R b KQkq e3 0 17"
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source, target = folder / "start.fen", folder / "exchange.fen"
            source.write_text(fen, encoding="utf-8-sig")
            app = self.make_app(data_layout=DataLayout(folder / "data"))
            self.root.deiconify()
            self.root.update()
            original_game = app.game
            app._play_move(Move.from_uci("e2e4"))
            original_position = to_fen(app.game.state)
            callback_errors = []

            def use_dialog():
                dialog = self.root.grab_current()
                assert isinstance(dialog, PositionDialog)
                try:
                    self.assertEqual(dialog.draft.get(), original_position)
                    dialog.draft.set("invalid")
                    dialog._play()
                    self.assertTrue(dialog.entry.instate(("invalid",)))
                    self.assertIs(app.game, original_game)
                    dialog._open()
                    self.assertEqual(dialog.draft.get(), fen)
                    dialog._copy()
                    self.assertEqual(self.root.clipboard_get(), fen)
                    dialog._save()
                    self.assertEqual(target.read_bytes(), (fen + "\n").encode("ascii"))
                    dialog._play()  # Decline replacing the active game.
                    self.assertTrue(dialog.winfo_exists())
                    self.assertIs(app.game, original_game)
                    self.assertEqual(dialog.draft.get(), fen)
                    dialog._play()
                except Exception as error:
                    callback_errors.append(error)
                finally:
                    if dialog.winfo_exists():
                        dialog.destroy()

            try:
                with (
                    patch("chess_and_chains.ui.dialogs.filedialog.askopenfilename", return_value=str(source)),
                    patch("chess_and_chains.ui.dialogs.filedialog.asksaveasfilename", return_value=str(target)),
                    patch("chess_and_chains.ui.app.messagebox.askyesno", side_effect=[False, True]) as confirm,
                ):
                    self.root.after(0, use_dialog)
                    app.position_button.invoke()
                if callback_errors:
                    raise callback_errors[0]
                self.assertEqual(confirm.call_count, 2)
                self.assertEqual(to_fen(app.game.state), fen)
                self.assertEqual(app.game.state.turn, Color.BLACK)
                self.assertIn(f'[FEN "{fen}"]', app._current_pgn())
                app._play_move(Move.from_uci("d4e3"))
                self.assertIsNone(app.game.state.board[parse_square("e4")])
                game_id = app._save_game()
                self.assertIsNotNone(game_id)
                self.assertEqual(to_fen(app.db.load_game(game_id).to_game().initial_state), fen)
                app._undo()
                self.assertEqual(to_fen(app.game.state), fen)
            finally:
                app.close()

    def test_position_escape_restores_focus_and_does_not_replace_game(self):
        app = self.make_app()
        self.root.deiconify()
        self.root.update()
        app.position_button.focus_force()
        self.root.update()
        game = app.game
        dialog = PositionDialog(self.root, app.t, game.state, lambda _parent: True)
        self.root.update()
        dialog.entry.focus_force()
        self.root.update()
        dialog.draft.set("not applied")

        with patch.object(app.position_button, "focus_set", wraps=app.position_button.focus_set) as restore:
            dialog.entry.event_generate("<Escape>", when="tail")
            self.root.update()
        self.assertFalse(dialog.winfo_exists())
        restore.assert_called_once_with()
        self.assertIs(self.root.focus_lastfor(), app.position_button)
        self.assertIs(app.game, game)


class StorageAndLocaleUiTests(AppTestCase):
    def test_marble_switch_preserves_game_and_uses_projected_move_targets(self):
        app = self.make_app(locale="de")
        self.root.deiconify()
        self.root.update()
        live = app.game
        app._play_move(Move.from_uci("e2e4"))
        app._undo()
        before = app.controller.view()
        self.assertTrue(before.can_redo)

        app.marble_button.invoke()
        self.assertTrue(app.board.marble)
        self.assertEqual(app.controller.view(), before)
        self.assertEqual(len(app.board.find_withtag("piece")), 32)
        self.assertTrue(app.board.find_withtag("marble-board"))
        app._redo()
        self.assertEqual(app.game.moves, [Move.from_uci("e2e4")])
        app.flip_button.invoke()
        self.assertEqual(app.board.orientation, "black")

        for square in ("e7", "e5"):
            expected = parse_square(square)
            col, row = screen_cell(expected, app.board.orientation)
            x, y = app.board._point(col + 0.5, row + 0.5)
            event = tk.Event()
            event.x, event.y = round(x), round(y)
            self.assertEqual(app.board._square_at(event.x, event.y), expected)
            app.board._on_button_press(event)
            app.board._on_button_release(event)

        self.assertIs(app.game, live)
        self.assertEqual(app.game.moves, [Move.from_uci("e2e4"), Move.from_uci("e7e5")])
        recording = app._current_pgn()
        app.marble_button.invoke()
        self.assertFalse(app.board.marble)
        self.assertFalse(app.board.find_withtag("marble-board"))
        self.assertEqual(app.board.orientation, "black")
        self.assertEqual(app._current_pgn(), recording)
        app._undo()
        self.assertTrue(app.game.can_redo)

    def test_saved_game_replay_keeps_active_game_and_handles_black_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = self.make_app(data_layout=DataLayout(Path(tmp) / "data"))
            fen = "r3k2r/8/8/8/3pP3/8/8/R3K2R b KQkq e3 0 17"
            game_id = app.db.import_pgn(f'[SetUp "1"]\n[FEN "{fen}"]\n\n17... dxe3 1/2-1/2')
            app._play_move(Move.from_uci("d2d4"))
            live = app.game
            original_pgn = app.db.load_game(game_id).pgn
            errors = []

            def inspect():
                dialog = self.root.grab_current()
                try:
                    self.assertIsInstance(dialog, ReplayDialog)
                    self.assertEqual(to_fen(dialog.board._state), fen)
                    self.assertEqual(dialog.move_list.get(1), "17… dxe3")
                    dialog.move_list.focus_force()
                    self.root.update()
                    dialog.move_list.event_generate("<Right>", when="tail")
                    self.root.update()
                    self.assertEqual(dialog.index, 1)
                    self.assertIsNone(dialog.board._state.board[parse_square("e4")])
                    self.assertIn("½–½", dialog.status.cget("text"))
                    self.assertFalse(dialog.board._legal_moves)
                    dialog._previous.invoke()
                    self.assertEqual(to_fen(dialog.board._state), fen)
                    dialog._close()
                except Exception as error:
                    errors.append(error)
                finally:
                    if dialog is not None and dialog.winfo_exists():
                        dialog.destroy()

            def choose():
                dialog = self.root.grab_current()
                button = next(child for child in dialog.winfo_children()[0].winfo_children()
                              if isinstance(child, ttk.Button) and child.cget("text") == app.t("replay.title"))
                self.root.after(0, inspect)
                button.invoke()

            try:
                self.root.deiconify()
                self.root.update()
                self.root.after(0, choose)
                app.library_button.invoke()
                if errors:
                    raise errors[0]
                self.assertIs(app.game, live)
                self.assertEqual(app.game.moves, [Move.from_uci("d2d4")])
                self.assertEqual(app.db.load_game(game_id).pgn, original_pgn)
            finally:
                app.close()

    def test_library_search_keeps_open_and_export_bound_to_filtered_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            app = self.make_app(data_layout=DataLayout(path / "data"))
            wanted = app.db.import_pgn('[White "Éva Szabó"]\n[Event "Club Cup"]\n\n1. e4 *')
            app.db.import_pgn('[White "Other player"]\n\n1. d4 *')
            errors = []

            def choose(action):
                dialog = self.root.grab_current()
                try:
                    content = dialog.winfo_children()[0]
                    children = content.winfo_children()
                    search = next(child for child in children if type(child) is ttk.Entry)
                    selection = next(child for child in children if isinstance(child, ttk.Combobox))
                    button = next(child for child in children if isinstance(child, ttk.Button)
                                  and child.cget("text") == action)
                    search.insert(0, "no matching player")
                    self.assertTrue(button.instate(("disabled",)))
                    search.delete(0, tk.END)
                    search.insert(0, "ÉVA club")
                    self.assertIn(f"#{wanted}", selection.get())
                    self.assertFalse(button.instate(("disabled",)))
                    button.invoke()
                except Exception as error:
                    errors.append(error)
                finally:
                    if dialog.winfo_exists():
                        dialog.destroy()

            try:
                target = path / "filtered.pgn"
                with patch("chess_and_chains.ui.app.filedialog.asksaveasfilename", return_value=str(target)):
                    self.root.after(0, choose, app.t("library.export"))
                    app.library_button.invoke()
                if errors:
                    raise errors[0]
                self.assertIn("1. e4 *", target.read_text(encoding="utf-8"))
                self.root.after(0, choose, app.t("library.open"))
                app.library_button.invoke()
                if errors:
                    raise errors[0]
                self.assertEqual(app.game.moves, [Move.from_uci("e2e4")])
            finally:
                app.close()

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
                timed_out = False

                def close_after_timeout(dialog):
                    nonlocal timed_out
                    timed_out = True
                    dialog.destroy()

                def press_when_focused():
                    nonlocal pending, sent, keypad_bound
                    pending = None
                    dialog = self.root.grab_current()
                    content = dialog.winfo_children()[0]
                    button = next(child for child in content.winfo_children()
                                  if isinstance(child, ttk.Button) and child.cget("text") == label)
                    if time.monotonic() >= deadline:
                        close_after_timeout(dialog)
                    elif not button.winfo_viewable():
                        pending = self.root.after(10, press_when_focused)
                    elif self.root.focus_get() is not button:
                        button.focus_force()
                        pending = self.root.after(10, press_when_focused)
                    else:
                        sent = True
                        keypad_bound = bool(button.bind("<KP_Enter>"))
                        button.event_generate(f"<{key}>", when="tail")
                        pending = self.root.after(1000, close_after_timeout, dialog)

                pending = self.root.after(0, press_when_focused)
                try:
                    with patch.object(app.library_button, "focus_set", wraps=app.library_button.focus_set) as restore:
                        app.library_button.invoke()
                finally:
                    if pending is not None:
                        self.root.after_cancel(pending)
                self.assertTrue(sent, f"{label} did not receive focus")
                self.assertFalse(timed_out, f"{key} did not close the chooser for {label}")
                self.assertTrue(keypad_bound, f"{label} has no keypad Enter binding")
                restore.assert_called_once_with()
                self.assertIs(self.root.focus_lastfor(), app.library_button)

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

    def test_large_german_text_keeps_play_actions_visible_when_focused(self):
        folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        app = self.make_app(locale="de", tk_dpi=192, data_layout=DataLayout(folder / "data"))
        self.root.geometry("860x700")
        self.root.deiconify()
        self.root.update()
        self.assertAlmostEqual(self.root.winfo_fpixels("1i"), 192, delta=3)
        app._play_move(Move.from_uci("e2e4"))
        app._undo()

        for button in (app.redo_button, app.library_button, app.engine_button):
            with self.subTest(action=button.cget("text")):
                self.assertGreaterEqual(button.winfo_width() + 1, button.winfo_reqwidth())
                self.assertEqual(button.cget("state"), "normal")
                button.focus_force()
                self.root.update()
                self.assertIs(self.root.focus_get(), button)
                top = button.winfo_rooty()
                viewport_top = app.play_canvas.winfo_rooty()
                self.assertGreaterEqual(top, viewport_top - 1)
                self.assertLessEqual(top + button.winfo_height(),
                                     viewport_top + app.play_canvas.winfo_height() + 1)

    def test_marble_keyboard_moves_and_tabs_with_scaled_english_text(self):
        app = self.make_app(tk_dpi=144)
        self.root.geometry("860x700")
        self.root.deiconify()
        self.root.update()
        self.assertAlmostEqual(self.root.winfo_fpixels("1i"), 144, delta=3)

        app.marble_button.focus_force()
        self.root.update()
        app.marble_button.event_generate("<Return>", when="tail")
        self.root.update()
        self.assertTrue(app.board.marble)
        app.board.focus_force()
        self.root.update()
        for key in ("Return", "Up", "Up", "Return"):
            app.board.event_generate(f"<{key}>")
        self.assertEqual(app.game.moves, [Move.from_uci("e2e4")])

        app.board.event_generate("<Tab>")
        self.root.update()
        self.assertIs(self.root.focus_get(), app.tab_rail.children["play"])
        app.tab_rail.children["play"].event_generate("<Right>")
        self.root.update()
        self.assertEqual(app.tab_rail.active, "moves")
        self.assertTrue(app.move_list.winfo_viewable())
        self.assertIn("e4", app.move_list.get(0))


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
