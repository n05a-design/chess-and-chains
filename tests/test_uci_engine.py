"""Local subprocess tests for the user-configured UCI adapter."""

from concurrent.futures import ThreadPoolExecutor
import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chess_and_chains.chess import ChessRules, Move, parse_square
from chess_and_chains.engines.uci import (
    EngineLaunchError,
    EngineProtocolError,
    EngineTimeoutError,
    UCIEngine,
)

_MOCK_ENGINE = r"""
import sys
import time

mode = sys.argv[1]
for raw in sys.stdin:
    command = raw.strip()
    if command == "uci":
        print("id name Local Mock", flush=True)
        print("option name Threads type spin default 1 min 1 max 4", flush=True)
        print("option name Style type combo default Normal var Normal var Risky", flush=True)
        print("uciok", flush=True)
    elif command == "isready":
        print("readyok", flush=True)
    elif command.startswith("go "):
        if mode == "stall":
            time.sleep(2)
        elif mode == "crash":
            sys.exit(7)
        elif mode == "illegal":
            print("bestmove e2e5", flush=True)
        elif mode == "malformed":
            print("bestmove e9e4", flush=True)
        elif mode == "none":
            print("bestmove (none)", flush=True)
        elif mode == "stop":
            pass
        else:
            print("bestmove e2e4 ponder e7e5", flush=True)
    elif command == "stop" and mode == "stop":
        print("bestmove e2e4", flush=True)
    elif command == "quit":
        break
"""


def create_engine(mode: str = "normal", **kwargs) -> UCIEngine:
    timeouts = {
        "startup_timeout": 1,
        "command_timeout": 1,
        "shutdown_timeout": 0.1,
    }
    timeouts.update(kwargs)
    return UCIEngine(
        (sys.executable, "-u", "-c", _MOCK_ENGINE, mode),
        **timeouts,
    )


class UCIEngineTests(unittest.TestCase):
    def test_handshake_options_position_and_legal_bestmove(self):
        engine = create_engine()
        try:
            engine.start()
            self.assertTrue(engine.running)
            self.assertEqual(engine.options["Threads"].kind, "spin")
            self.assertEqual(engine.options["Threads"].minimum, 1)
            self.assertEqual(engine.options["Threads"].maximum, 4)
            self.assertEqual(engine.options["Style"].kind, "combo")
            self.assertEqual(engine.options["Style"].choices, ("Normal", "Risky"))
            engine.is_ready()
            engine.new_game()
            engine.set_option("Threads", 2)
            with self.assertRaises(ValueError):
                engine.set_option("Threads", 5)
            with self.assertRaises(ValueError):
                engine.set_option("Style", "Unadvertised")
            engine.set_position(
                moves=(Move(parse_square("e2"), parse_square("e4")),)
            )

            rules = ChessRules()
            legal_moves = rules.legal_moves(rules.initial_state())
            self.assertEqual(
                engine.go_movetime(25, legal_moves),
                Move(parse_square("e2"), parse_square("e4")),
            )
        finally:
            engine.close()
        self.assertFalse(engine.running)

    def test_engine_can_be_restarted_after_close(self):
        engine = create_engine()
        engine.start()
        engine.close()
        engine.start()
        engine.is_ready()
        engine.close()
        self.assertFalse(engine.running)

    def test_missing_engine_path_is_reported(self):
        engine = UCIEngine(("/definitely/not/a/chess/engine",))
        with self.assertRaises(EngineLaunchError):
            engine.start()

    def test_illegal_bestmove_is_rejected_by_the_rules_boundary(self):
        engine = create_engine("illegal")
        try:
            engine.start()
            legal_moves = ChessRules().legal_moves(ChessRules().initial_state())
            with self.assertRaisesRegex(EngineProtocolError, "illegal move"):
                engine.go_movetime(25, legal_moves)
        finally:
            engine.close()

    def test_engine_exit_during_search_is_reported(self):
        engine = create_engine("crash")
        try:
            engine.start()
            legal_moves = ChessRules().legal_moves(ChessRules().initial_state())
            with self.assertRaisesRegex(EngineProtocolError, "closed its output"):
                engine.go_movetime(25, legal_moves)
        finally:
            engine.close()

    def test_malformed_bestmove_is_reported(self):
        engine = create_engine("malformed")
        try:
            engine.start()
            legal_moves = ChessRules().legal_moves(ChessRules().initial_state())
            with self.assertRaisesRegex(EngineProtocolError, "Malformed bestmove"):
                engine.go_movetime(25, legal_moves)
        finally:
            engine.close()

    def test_engine_may_report_no_move_only_when_position_has_none(self):
        engine = create_engine("none")
        try:
            engine.start()
            self.assertIsNone(engine.go_movetime(25, ()))
        finally:
            engine.close()

    def test_stop_search_can_be_requested_while_worker_waits(self):
        engine = create_engine("stop")
        engine.start()
        legal_moves = ChessRules().legal_moves(ChessRules().initial_state())
        started = threading.Event()

        def search():
            started.set()
            return engine.go_movetime(5000, legal_moves, timeout=1)

        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(search)
                self.assertTrue(started.wait(timeout=1))
                deadline = time.monotonic() + 1
                while not engine.searching and time.monotonic() < deadline:
                    time.sleep(0.005)
                self.assertTrue(engine.stop_search())
                self.assertEqual(
                    future.result(timeout=1),
                    Move(parse_square("e2"), parse_square("e4")),
                )
        finally:
            engine.close()

    def test_concurrent_search_calls_are_serialized(self):
        engine = create_engine()
        engine.start()
        legal_moves = ChessRules().legal_moves(ChessRules().initial_state())
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(engine.go_movetime, 25, legal_moves)
                second = pool.submit(engine.go_movetime, 25, legal_moves)
                expected = Move(parse_square("e2"), parse_square("e4"))
                self.assertEqual(first.result(timeout=1), expected)
                self.assertEqual(second.result(timeout=1), expected)
        finally:
            engine.close()

    def test_search_timeout_is_reported_and_process_can_be_closed(self):
        engine = create_engine("stall", command_timeout=0.05)
        engine.start()
        legal_moves = ChessRules().legal_moves(ChessRules().initial_state())
        with self.assertRaises(EngineTimeoutError):
            engine.go_movetime(25, legal_moves)
        self.assertFalse(engine.running)
        engine.close()
        self.assertFalse(engine.running)


if __name__ == "__main__":
    unittest.main()
