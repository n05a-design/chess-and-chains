"""UCI analysis with project-owned protocol fixtures.

SPDX-License-Identifier: MPL-2.0
"""
from dataclasses import replace
import sys
import tempfile
from pathlib import Path
import time
import unittest

from chess_and_chains.chess import INITIAL_FEN, Color, Move
from chess_and_chains.engines.analysis import (
    AnalysisMode,
    AnalysisRequest,
    AnalysisService,
    Evaluation,
    EvaluationKind,
    JobStatus,
    ScoreBound,
    critical_moments,
    parse_info,
)
from chess_and_chains.engines.bot import EngineConfig


FIXTURE = """
import sys

def say(line):
    print(line, flush=True)

for raw in sys.stdin:
    line = raw.strip()
    with open(sys.argv[1], "a", encoding="utf-8") as log:
        log.write(line + "\\n")
    if line == "uci":
        say("id name Local UCI analysis fixture")
        say("option name MultiPV type spin default 1 min 1 max 2")
        say("option name Threads type spin default 4 min 1 max 4")
        say("option name Hash type spin default 64 min 1 max 128")
        say("uciok")
    elif line == "isready":
        say("readyok")
    elif line.startswith("setoption name MultiPV value "):
        variants = int(line.split()[-1])
    elif line.startswith("position fen "):
        moves = line.partition(" moves ")[2].split()
        board, turn = line.split()[2:4]
        black_turn = turn == "b"
    elif line.startswith("go movetime "):
        if sys.argv[2] in ("stall", "ignores-stop"):
            continue
        if sys.argv[2] == "crash" and moves:
            sys.exit(3)
        if board == "7k/P7/8/8/8/8/8/K7":
            say("info depth 10 score cp 20 pv a7a8n")
            say("info depth 11 score cp 20 pv a7a8n h8g8")
            say("bestmove a7a8n")
        elif not moves and not black_turn:
            say("info depth 9 score cp 30 pv d2d4 d7d5")
            say("info depth 10 seldepth 14 score cp 35 nodes 100 nps 200 time 50 pv d2d4 d7d5")
            say("info depth 11 score cp 45 pv d2d4 a8a6")
            if variants == 2:
                say("info multipv 2 depth 10 score cp 20 pv e2e4 e7e5")
            say("bestmove d2d4")
        elif len(moves) == 1 or black_turn:
            say("info depth 12 score cp 180 pv e7e5 g1f3")
            say("bestmove e7e5")
        else:
            say("info depth 13 score mate 3 pv g1f3")
            say("bestmove g1f3")
    elif line == "stop" and sys.argv[2] != "ignores-stop":
        say("bestmove d2d4")
    elif line == "quit":
        break
"""


def move(text):
    return Move.from_uci(text)


class InfoParserTests(unittest.TestCase):
    def test_fields_and_normalized_black_score(self):
        line = parse_info(
            "info extra 88 depth 15 seldepth 21 multipv 2 score cp 36 lowerbound "
            "pv e7e5 g1f3 time 50 nodes 2000 nps 40000",
            Color.BLACK,
        )
        self.assertEqual(line.rank, 2)
        self.assertEqual(line.moves, (move("e7e5"), move("g1f3")))
        self.assertEqual(line.evaluation, Evaluation(EvaluationKind.CENTIPAWNS, -36, ScoreBound.UPPER))
        self.assertEqual((line.depth, line.selective_depth, line.nodes, line.nodes_per_second, line.time_ms),
                         (15, 21, 2000, 40000, 50))

    def test_mate_keeps_its_units_and_bound(self):
        line = parse_info("info score mate -3 upperbound pv h2h1q", Color.BLACK)
        self.assertEqual(line.moves, (move("h2h1q"),))
        self.assertEqual(line.evaluation, Evaluation(EvaluationKind.MATE, 3, ScoreBound.LOWER))

    def test_partial_metrics_and_unavailable_score(self):
        line = parse_info("info depth nodes 5 score cp broken pv e2e4", Color.WHITE)
        self.assertIsNone(line.depth)
        self.assertEqual(line.nodes, 5)
        self.assertIsNone(line.evaluation)

    def test_no_pv_bad_pv_and_free_text_are_not_analysis(self):
        for report in ("info depth 14", "info pv", "info pv e2e4 bad", "info string pv e2e4"):
            with self.subTest(report=report):
                self.assertIsNone(parse_info(report, Color.WHITE))


class AnalysisServiceTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        self.log = Path(directory) / "uci.log"

    def service(self, mode="normal", *, cache_size=8, version="fixture-v1"):
        config = EngineConfig(
            (sys.executable, "-u", "-c", FIXTURE, str(self.log), mode),
            "Local UCI analysis fixture", True, "mock",
        )
        return AnalysisService(config, engine_id="fixture", engine_version=version, cache_size=cache_size)

    def run_job(self, service, request):
        job = service.start(request)
        self.assertTrue(job.wait(10))
        return job.progress()

    def commands(self):
        return self.log.read_text(encoding="utf-8").splitlines()

    def test_fixture_multivariant_analysis_and_illegal_pv(self):
        progress = self.run_job(self.service(), AnalysisRequest("start", multipv=3))
        self.assertIs(progress.status, JobStatus.COMPLETED, progress.error)
        self.assertEqual(progress.total, 1)
        result, = progress.results
        self.assertEqual(result.best_move, move("d2d4"))
        self.assertEqual(result.fen, INITIAL_FEN)
        self.assertEqual(result.configuration.multipv, 2)
        self.assertEqual(result.configuration.requested_multipv, 3)
        self.assertTrue(result.configuration.is_mock)
        self.assertEqual([line.rank for line in result.lines], [1, 2])
        self.assertEqual(result.lines[0].depth, 10)
        self.assertEqual(result.lines[0].moves, (move("d2d4"), move("d7d5")))
        commands = self.commands()
        self.assertIn("setoption name Threads value 1", commands)
        self.assertIn("setoption name Hash value 16", commands)
        self.assertIn("setoption name MultiPV value 2", commands)
        self.assertIn("quit", commands)

    def test_game_progress_and_critical_moment(self):
        request = AnalysisRequest("game", moves=(move("e2e4"), move("e7e5")), mode=AnalysisMode.GAME)
        progress = self.run_job(self.service(), request)
        self.assertIs(progress.status, JobStatus.COMPLETED, progress.error)
        self.assertEqual(progress.job_id, "game")
        self.assertEqual([len(result.history) for result in progress.results], [0, 1, 2])
        self.assertEqual(progress.results[1].turn, Color.BLACK)
        self.assertEqual(progress.results[1].lines[0].evaluation.value, -180)
        self.assertEqual(progress.results[2].lines[0].evaluation.kind, EvaluationKind.MATE)
        critical, = critical_moments(progress.results)
        self.assertEqual((critical.ply, critical.played_move, critical.alternative, critical.centipawn_loss),
                         (1, move("e2e4"), move("d2d4"), 215))
        self.assertIn("position fen " + INITIAL_FEN + " moves e2e4 e7e5", self.commands())

    def test_selected_plies_snapshot_copies_input_and_returns_ordered_subset(self):
        moves = [move("e2e4"), move("e7e5")]
        plies = [2, 0, 2]
        request = AnalysisRequest("selected", moves=moves, mode=AnalysisMode.SELECTED, selected_plies=plies)
        moves.clear()
        plies.clear()
        progress = self.run_job(self.service(), request)
        self.assertIs(progress.status, JobStatus.COMPLETED, progress.error)
        self.assertEqual([len(result.history) for result in progress.results], [0, 2])

    def test_variation_underpromotion_is_valid_but_cannot_move_after_terminal_state(self):
        request = AnalysisRequest("promotion", "7k/P7/8/8/8/8/8/K7 w - - 0 1")
        progress = self.run_job(self.service(), request)
        self.assertIs(progress.status, JobStatus.COMPLETED, progress.error)
        result, = progress.results
        self.assertEqual(result.best_move, move("a7a8n"))
        self.assertEqual(result.lines[0].depth, 10)
        self.assertEqual(result.lines[0].moves, (move("a7a8n"),))

    def test_terminal_position_does_not_start_engine(self):
        progress = self.run_job(self.service(), AnalysisRequest("terminal", "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"))
        self.assertIs(progress.status, JobStatus.COMPLETED, progress.error)
        result, = progress.results
        self.assertEqual((result.outcome, result.lines, result.best_move), ("checkmate", (), None))
        self.assertFalse(self.log.exists())

    def test_illegal_history_is_rejected_even_beyond_last_selected_ply(self):
        request = AnalysisRequest("invalid", moves=(move("e2e5"),), mode=AnalysisMode.SELECTED, selected_plies=(0,))
        progress = self.run_job(self.service(), request)
        self.assertIs(progress.status, JobStatus.FAILED)
        self.assertIn("Illegal move", progress.error)
        self.assertFalse(self.log.exists())

    def test_failure_retains_already_completed_positions(self):
        request = AnalysisRequest("partial", moves=(move("e2e4"),), mode=AnalysisMode.GAME)
        progress = self.run_job(self.service("crash"), request)
        self.assertIs(progress.status, JobStatus.FAILED)
        self.assertIn("exit code", progress.error)
        self.assertEqual([result.history for result in progress.results], [()])

    def test_cancellation_and_serial_job_limit(self):
        service = self.service("stall")
        request = AnalysisRequest("cancel", movetime_ms=5000)
        job = service.start(request)
        try:
            deadline = time.monotonic() + 10
            while not self.log.exists() or "go movetime 5000" not in self.commands():
                self.assertLess(time.monotonic(), deadline, job.progress())
                time.sleep(0.01)
            self.assertIs(job.progress().status, JobStatus.RUNNING)
            with self.assertRaisesRegex(RuntimeError, "already running"):
                service.start(request)
            job.cancel()
            self.assertTrue(job.wait(5))
            progress = job.progress()
            self.assertIs(progress.status, JobStatus.CANCELLED)
            self.assertEqual(progress.results, ())
            self.assertIn("stop", self.commands())
            self.assertIn("quit", self.commands())
        finally:
            job.cancel()
            job.wait(10)

    def test_cancel_releases_an_engine_that_ignores_stop(self):
        service = self.service("ignores-stop")
        request = AnalysisRequest("ignore-stop", movetime_ms=5000)
        job = service.start(request)
        try:
            deadline = time.monotonic() + 10
            while not self.log.exists() or "go movetime 5000" not in self.commands():
                self.assertLess(time.monotonic(), deadline, job.progress())
                time.sleep(0.01)
            job.cancel()
            self.assertTrue(job.wait(5))
            self.assertIs(job.progress().status, JobStatus.CANCELLED)
            self.assertIn("stop", self.commands())
            self.assertNotIn("quit", self.commands())
        finally:
            job.cancel()
            job.wait(10)

    def test_cache_includes_history_and_budget_and_is_bounded(self):
        service = self.service(cache_size=1)
        request = AnalysisRequest("original", moves=(move("e2e4"),))
        first = self.run_job(service, request).results[0]
        self.assertFalse(first.cached)
        self.assertTrue(self.run_job(service, request).results[0].cached)
        self.assertEqual(self.commands().count("go movetime 100"), 1)
        changed = self.run_job(service, replace(request, movetime_ms=200)).results[0]
        self.assertFalse(changed.cached)
        self.assertFalse(self.run_job(service, request).results[0].cached)
        other_origin = AnalysisRequest("same-board", initial_fen=first.fen)
        self.assertFalse(self.run_job(service, other_origin).results[0].cached)
        self.assertEqual(self.commands().count("go movetime 100"), 3)

    def test_legacy_mock_without_multipv_has_an_explicit_single_line_budget(self):
        config = EngineConfig.mock(delay_ms=0)
        service = AnalysisService(config, engine_id="project-mock")
        progress = self.run_job(service, AnalysisRequest("legacy-mock", multipv=3))
        self.assertIs(progress.status, JobStatus.COMPLETED, progress.error)
        result, = progress.results
        self.assertEqual(result.configuration.multipv, 1)
        self.assertIsNotNone(result.best_move)
        self.assertEqual(result.lines, ())

    def test_no_cache_without_trusted_version(self):
        service = self.service(version=None)
        request = AnalysisRequest("versionless")
        for _ in range(2):
            self.assertFalse(self.run_job(service, request).results[0].cached)


if __name__ == "__main__":
    unittest.main()
