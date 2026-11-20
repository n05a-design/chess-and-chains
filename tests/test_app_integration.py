"""Tk app integration: mock-bot vertical slice, non-blocking UI, puzzles, storage.

Runs a real Tk root (withdrawn). The bot is the project-owned mock UCI
engine in a subprocess; this is not a test against a real chess engine.
"""
import sys
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from chess_and_chains.chess import Color, GameStatus, Move, parse_square  # noqa: E402
from chess_and_chains.engines.bot import EngineConfig, UCIBot  # noqa: E402
from chess_and_chains.game import BotStatus, GameSetup  # noqa: E402
from chess_and_chains.storage import DataLayout, load_settings  # noqa: E402
from chess_and_chains.ui.app import ChessApp  # noqa: E402
from chess_and_chains.ui.pieces import PIECE_FILE_NAMES, GeometricTestPieces, validate_svg_piece_set  # noqa: E402
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
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.root.update()
            if predicate():
                return
            time.sleep(0.005)
        self.fail("condition not reached while pumping Tk events")


class PromotionUiTests(AppTestCase):
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
        while len(app.game.moves) < 2 and time.monotonic() - start < 10:
            self.root.update()
            now = time.monotonic()
            gaps.append(now - last)
            last = now
            time.sleep(0.01)
        self.assertEqual(len(app.game.moves), 2)
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
        deadline = time.monotonic() + 0.8
        while time.monotonic() < deadline:
            self.root.update()
            time.sleep(0.01)
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


class PuzzleUiTests(AppTestCase):
    def test_puzzle_tab_uses_same_board_and_records_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = self.make_app(data_layout=DataLayout(Path(tmp) / "data"))
            app.tab_rail.set_active("puzzles")
            self.assertEqual(app.active_panel, "puzzles")
            self.assertIn("PUZZLE LAB", app.header_mode_text.get())
            session = app.puzzle
            self.assertIs(app.board._state, session.state)
            app._play_move(Move.from_uci("a1a2"))  # not legal: board would never offer it
            app._play_move(session.expected_move)
            self.assertEqual(app.puzzle_feedback_text.get(), "Solved!")
            self.assertEqual(app.db.solved_puzzle_ids("demo"), {session.puzzle.puzzle_id})
            app._next_puzzle()
            app._puzzle_hint()
            self.assertEqual(app.board._hint_square, app.puzzle.expected_move.from_square)
            app._puzzle_reveal()
            self.assertIn("Solution:", app.puzzle_feedback_text.get())
            self.assertEqual(app.db.statistics().puzzles_attempted, 2)
            app.tab_rail.set_active("play")
            self.assertIs(app.board._state, app.game.state)
            app.close()

    def test_game_undo_is_ignored_in_puzzle_mode(self):
        app = self.make_app()
        app._play_move(Move.from_uci("e2e4"))
        app.tab_rail.set_active("puzzles")
        app._undo()
        self.assertEqual(len(app.game.moves), 1)


class StorageAndLocaleUiTests(AppTestCase):
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

    def test_library_imports_into_an_empty_collection_and_exports_selected_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            app = self.make_app(data_layout=DataLayout(directory / "data"))
            source, target = directory / "game.pgn", directory / "saved.pgn"
            source.write_text("1. e4 e5 *", encoding="utf-8")

            def choose_import(_title, labels, _confirm, *, actions, **_options):
                self.assertEqual(labels, [])
                label, run, requires_selection = actions[0]
                self.assertEqual(label, "Import PGN…")
                self.assertFalse(requires_selection)
                run(None)

            with patch.object(app, "_choose_item", side_effect=choose_import), patch(
                "chess_and_chains.ui.app.filedialog.askopenfilename", return_value=str(source),
            ):
                app.library_button.invoke()
            self.assertEqual(app.game.moves, [])
            self.assertIn("Imported game #1", app.interaction_text.get())

            def choose_export(_title, labels, _confirm, *, actions, **_options):
                self.assertEqual(len(labels), 1)
                actions[1][1](0)

            with patch.object(app, "_choose_item", side_effect=choose_export), patch(
                "chess_and_chains.ui.app.filedialog.asksaveasfilename", return_value=str(target),
            ):
                app.library_button.invoke()
            self.assertIn("1. e4 e5 *", target.read_text(encoding="utf-8"))
            app.close()

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

    def test_small_window_keeps_board_usable(self):
        app = self.make_app()
        self.root.deiconify()
        self.root.geometry("860x700")
        self.root.update()
        self.assertGreater(app.board._square_size, 20)
        self.root.withdraw()


class PieceRendererContractTests(unittest.TestCase):
    def test_geometric_renderer_is_the_default(self):
        self.assertEqual(GeometricTestPieces.renderer_id, "geometric-test")

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
