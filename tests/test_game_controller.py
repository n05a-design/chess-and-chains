"""GameController + async worker + mock UCI engine vertical slice.

The mock engine is project-owned test code, not a chess AI; nothing here
proves play against a real engine such as Stockfish.
"""
import sys
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chess_and_chains.chess import ChessError, Color, GameStatus, IllegalMoveError, Move  # noqa: E402
from chess_and_chains.engines.bot import (  # noqa: E402
    BotRequest,
    EngineConfig,
    UCIBot,
    resolve_engine_config,
    split_engine_command,
)
from chess_and_chains.engines.presets import load_presets  # noqa: E402
from chess_and_chains.game import BotStatus, GameController, GameSetup, PlayMode  # noqa: E402

PRESET = load_presets()[0]  # 50 ms movetime


def wait_for(controller, predicate, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        controller.poll()
        if predicate(controller.view()):
            return controller.view()
        time.sleep(0.01)
    raise AssertionError(f"Condition not reached; view={controller.view()}")


class ScriptedProvider:
    """In-process provider for deterministic race tests."""

    display_name = "scripted"
    is_mock = True

    def __init__(self, *, block=False, fail=None, move=None):
        self.block = block
        self.fail = fail
        self.move = move
        self.release = threading.Event()
        self.started = threading.Event()
        self.requests = []
        self.cancelled = 0
        self.closed = False
        self.killed = False

    def choose_move(self, request: BotRequest):
        self.requests.append(request)
        self.started.set()
        if self.block:
            self.release.wait(5)
        if self.fail:
            raise RuntimeError(self.fail)
        if self.move is not None:
            return self.move
        return request.legal_moves[0] if request.legal_moves else None

    def cancel(self):
        self.cancelled += 1

    def kill(self):
        self.killed = True
        self.release.set()

    def close(self):
        self.closed = True


class ControllerUnitTests(unittest.TestCase):
    def test_two_player_mode_has_no_bot(self):
        c = GameController()
        c.new_game(GameSetup.two_players())
        c.play_human(Move.from_uci("e2e4"))
        c.play_human(Move.from_uci("e7e5"))
        view = c.view()
        self.assertEqual(view.bot_status, BotStatus.NONE)
        self.assertEqual(view.san_moves, ("e4", "e5"))
        c.undo()
        self.assertEqual(c.view().san_moves, ("e4",))
        c.redo()
        self.assertEqual(c.view().san_moves, ("e4", "e5"))
        c.shutdown()

    def test_setup_validation_and_missing_provider(self):
        with self.assertRaises(ValueError):
            GameSetup(PlayMode.HUMAN_VS_BOT)
        with self.assertRaises(ChessError):
            GameController().new_game(GameSetup.against_bot(Color.WHITE))

    def test_stale_result_after_new_game_is_discarded(self):
        provider = ScriptedProvider(block=True)
        c = GameController(provider)
        c.new_game(GameSetup.against_bot(Color.BLACK))  # bot plays white, starts at once
        self.assertTrue(provider.started.wait(2))
        old_generation = c.generation
        c.new_game(GameSetup.against_bot(Color.WHITE))  # human white now; no bot request
        provider.release.set()
        time.sleep(0.1)
        c.poll()
        self.assertGreater(c.generation, old_generation)
        self.assertEqual(c.game.moves, [], "a move from the abandoned game must never be applied")
        self.assertTrue(c.view().human_to_move)
        c.shutdown()

    def test_undo_during_search_cancels_and_returns_to_human(self):
        provider = ScriptedProvider(block=True)
        c = GameController(provider)
        c.new_game(GameSetup.against_bot(Color.WHITE))
        c.play_human(Move.from_uci("e2e4"))
        self.assertTrue(provider.started.wait(2))
        self.assertEqual(c.view().bot_status, BotStatus.THINKING)
        self.assertFalse(c.view().human_to_move)
        with self.assertRaises(IllegalMoveError):
            c.play_human(Move.from_uci("d2d4"))
        c.undo()
        self.assertGreaterEqual(provider.cancelled, 1)
        provider.release.set()
        time.sleep(0.1)
        c.poll()
        self.assertEqual(c.game.moves, [])
        self.assertTrue(c.view().human_to_move)
        c.shutdown()

    def test_provider_exception_becomes_error_state_not_crash(self):
        provider = ScriptedProvider(fail="engine exploded")
        c = GameController(provider)
        c.new_game(GameSetup.against_bot(Color.WHITE))
        c.play_human(Move.from_uci("e2e4"))
        view = wait_for(c, lambda v: v.bot_status is BotStatus.ERROR)
        self.assertIn("engine exploded", view.bot_error)
        self.assertEqual(len(c.game.moves), 1)
        provider.fail = None
        c.retry_bot()
        wait_for(c, lambda v: len(v.san_moves) == 2)
        c.shutdown()

    def test_illegal_provider_move_is_rejected_by_domain(self):
        provider = ScriptedProvider(move=Move.from_uci("e2e4"))  # illegal for black
        c = GameController(provider)
        c.new_game(GameSetup.against_bot(Color.WHITE))
        c.play_human(Move.from_uci("d2d4"))
        view = wait_for(c, lambda v: v.bot_status is BotStatus.ERROR)
        self.assertIn("rejected", view.bot_error)
        self.assertEqual(len(c.game.moves), 1)
        c.shutdown()

    def test_bot_undo_redo_skip_bot_plies(self):
        provider = ScriptedProvider()
        c = GameController(provider)
        c.new_game(GameSetup.against_bot(Color.WHITE))
        c.play_human(Move.from_uci("e2e4"))
        wait_for(c, lambda v: len(v.san_moves) == 2 and v.human_to_move)
        c.undo()
        self.assertEqual(c.game.moves, [])
        self.assertTrue(c.view().can_redo)
        c.redo()
        self.assertEqual(len(c.game.moves), 2)
        self.assertTrue(c.view().human_to_move)
        c.shutdown()

    def test_shutdown_stops_worker_even_if_provider_hangs(self):
        provider = ScriptedProvider(block=True)
        c = GameController(provider)
        c.new_game(GameSetup.against_bot(Color.BLACK))
        self.assertTrue(provider.started.wait(2))
        start = time.monotonic()
        self.assertTrue(c.shutdown(timeout=1.0))
        self.assertLess(time.monotonic() - start, 3)
        self.assertTrue(provider.closed)
        self.assertTrue(provider.killed)
        with self.assertRaises(ChessError):
            c.new_game()

    def test_listener_receives_views(self):
        c = GameController()
        seen = []
        unsubscribe = c.subscribe(seen.append)
        c.new_game()
        c.play_human(Move.from_uci("g1f3"))
        unsubscribe()
        c.play_human(Move.from_uci("g8f6"))
        self.assertEqual(len(seen), 2)
        self.assertEqual(seen[-1].san_moves, ("Nf3",))

    def test_incremental_san_matches_full_rebuild_after_branching(self):
        c = GameController()
        for uci in ("e2e4", "e7e5", "g1f3", "b8c6"):
            c.play_human(Move.from_uci(uci))
        c.undo(); c.undo()
        c.play_human(Move.from_uci("f1c4"))
        self.assertEqual(c.view().san_moves, ("e4", "e5", "Bc4"))


class MockEngineVerticalSliceTests(unittest.TestCase):
    """User move -> controller -> worker -> UCI mock process -> validated bot move."""

    def make(self, mode="normal", **kwargs):
        bot = UCIBot(EngineConfig.mock(mode, delay_ms=kwargs.pop("delay_ms", None)), PRESET, **kwargs)
        controller = GameController(bot)
        self.addCleanup(controller.shutdown)
        return controller, bot

    def test_full_game_against_mock_engine_reaches_rule_based_end(self):
        c, bot = self.make(delay_ms=0)
        c.new_game(GameSetup.against_bot(Color.WHITE))
        # Fool's-mate-style sequence for the bot side is not guaranteed; instead
        # play the human side with first legal moves until the game ends.
        for _ in range(1000):
            view = c.view()
            if view.outcome.status is not GameStatus.ACTIVE:
                break
            if view.human_to_move:
                c.play_human(view.legal_moves[0])
            else:
                wait_for(c, lambda v: v.human_to_move or v.outcome.status is not GameStatus.ACTIVE
                         or v.bot_status is BotStatus.ERROR)
                self.assertIsNone(c.view().bot_error)
        final = c.view()
        self.assertIsNot(final.outcome.status, GameStatus.ACTIVE, "game should end by rules")
        self.assertTrue(final.bot_is_mock)
        self.assertIn("mock", final.bot_name.lower())
        self.assertIsNotNone(bot.last_plan)
        applied = dict(bot.last_plan.apply)
        self.assertEqual(applied["Skill Level"], PRESET.skill_level)

    def test_bot_plays_white_first(self):
        c, _ = self.make()
        c.new_game(GameSetup.against_bot(Color.BLACK))
        view = wait_for(c, lambda v: v.human_to_move)
        self.assertEqual(len(view.san_moves), 1)
        self.assertEqual(view.state.turn, Color.BLACK)

    def test_engine_crash_is_reported_and_engine_restarts_on_retry(self):
        c, bot = self.make("crash")
        c.new_game(GameSetup.against_bot(Color.WHITE))
        c.play_human(Move.from_uci("e2e4"))
        view = wait_for(c, lambda v: v.bot_status is BotStatus.ERROR)
        self.assertIn("EngineProtocolError", view.bot_error)
        bot.config = EngineConfig.mock("normal")
        bot.close()
        c.retry_bot()
        wait_for(c, lambda v: len(v.san_moves) == 2)

    def test_stalled_engine_times_out_without_blocking_owner_thread(self):
        c, _ = self.make("stall", search_margin=0.3)
        c.new_game(GameSetup.against_bot(Color.WHITE))
        start = time.monotonic()
        c.play_human(Move.from_uci("e2e4"))
        self.assertLess(time.monotonic() - start, 0.5, "play_human must not wait for the engine")
        view = wait_for(c, lambda v: v.bot_status is BotStatus.ERROR, timeout=5)
        self.assertIn("Timeout", view.bot_error)

    def test_illegal_engine_move_never_reaches_game(self):
        c, _ = self.make("illegal")
        c.new_game(GameSetup.against_bot(Color.WHITE))
        c.play_human(Move.from_uci("e2e4"))
        wait_for(c, lambda v: v.bot_status is BotStatus.ERROR)
        self.assertEqual(len(c.game.moves), 1)

    def test_new_game_during_slow_search_discards_old_move(self):
        c, _ = self.make(delay_ms=400)
        c.new_game(GameSetup.against_bot(Color.BLACK))
        time.sleep(0.05)
        c.new_game(GameSetup.two_players())
        time.sleep(0.6)
        c.poll()
        self.assertEqual(c.game.moves, [])

    def test_shutdown_terminates_engine_process(self):
        c, bot = self.make(delay_ms=2000)
        c.new_game(GameSetup.against_bot(Color.BLACK))
        time.sleep(0.3)
        engine = bot._engine
        self.assertIsNotNone(engine)
        self.assertTrue(c.shutdown(timeout=2))
        self.assertFalse(engine.running)


class EngineConfigTests(unittest.TestCase):
    def test_default_is_mock_without_any_discovery(self):
        config, warning = resolve_engine_config(None, environ={})
        self.assertTrue(config.is_mock)
        self.assertIsNone(warning)

    def test_missing_configured_engine_falls_back_with_warning(self):
        config, warning = resolve_engine_config("/nonexistent/engine", environ={})
        self.assertTrue(config.is_mock)
        self.assertIn("not found", warning)

    def test_engine_command_split_keeps_windows_paths(self):
        """Regression (CI Windows): POSIX shlex stripped backslashes from engine paths."""
        self.assertEqual(
            split_engine_command(r"C:\Engines\sf\engine.exe -u", windows=True),
            [r"C:\Engines\sf\engine.exe", "-u"],
        )
        self.assertEqual(
            split_engine_command(r'"C:\Program Files\Engine\e.exe" --uci', windows=True),
            [r"C:\Program Files\Engine\e.exe", "--uci"],
        )
        self.assertEqual(
            split_engine_command("'/opt/my engine/bin' -u", windows=False),
            ["/opt/my engine/bin", "-u"],
        )

    def test_explicit_dev_environment_engine(self):
        config, warning = resolve_engine_config(None, environ={"CHESS_AND_CHAINS_ENGINE": sys.executable + " -u"})
        self.assertFalse(config.is_mock)
        self.assertEqual(config.source, "environment")
        self.assertEqual(config.command[-1], "-u")
        self.assertIsNone(warning)


if __name__ == "__main__":
    unittest.main()
