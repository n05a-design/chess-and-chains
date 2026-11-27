"""Headless training regressions using the existing Chess & Chains demo pack.

SPDX-License-Identifier: MPL-2.0
"""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from chess_and_chains.chess import INITIAL_FEN
from chess_and_chains.puzzles.pack import load_demo_pack
from chess_and_chains.puzzles.training import (
    AttemptStatus,
    ChainCompletion,
    DEMO_MATE_CHAIN,
    PuzzleKey,
    QueueMode,
    ReviewSchedule,
    TrainingAttempt,
    TrainingCandidate,
    TrainingSelection,
    TrainingSession,
    TrainingTask,
    build_training_queue,
    summarize_attempts,
)

NOW = datetime(2026, 11, 27, 15, tzinfo=timezone.utc)
BACK_RANK = PuzzleKey("demo", "ccBR01")
SCHOLAR = PuzzleKey("demo", "ccSC01")
SMOTHERED = PuzzleKey("demo", "ccSM02")


def attempt(
    index: int, *, key: PuzzleKey = BACK_RANK, offset: int = 0,
    status: AttemptStatus = AttemptStatus.SOLVED, mistakes: int = 0, hints: int = 0,
    milliseconds: int | None = None,
) -> TrainingAttempt:
    return TrainingAttempt(
        str(index), key, NOW + timedelta(days=offset), status, mistakes, hints, milliseconds,
    )


class AttemptProjectionTests(unittest.TestCase):
    def test_clean_intervals_grow_and_use_final_interval_for_later_solves(self):
        history = []
        for offset, interval in enumerate((1, 3, 7, 14, 30, 30), start=1):
            history.append(attempt(offset, offset=offset))
            item = summarize_attempts(reversed(history))[BACK_RANK]
            self.assertEqual(item.clean_streak, offset)
            self.assertEqual(item.due_at, NOW + timedelta(days=offset + interval))
            self.assertEqual(item.secure, offset >= 2)

    def test_mistakes_and_hints_reduce_next_interval_without_losing_best_times(self):
        history = (
            attempt(1, milliseconds=900),
            attempt(2, offset=1, milliseconds=600),
            attempt(3, offset=4, mistakes=1, hints=2, milliseconds=500),
            attempt(4, offset=5, status=AttemptStatus.REVEALED, milliseconds=300),
        )
        progress = summarize_attempts(history, ReviewSchedule((2, 6), timedelta(minutes=5)))
        item = progress[BACK_RANK]
        self.assertEqual((item.attempts, item.solved, item.clean_solves, item.hints_used), (4, 3, 2, 2))
        self.assertEqual(item.solve_rate, 0.75)
        self.assertEqual(item.best_solve_ms, 500)
        self.assertEqual(item.clean_streak, 0)
        self.assertEqual(item.due_at, NOW + timedelta(days=5, minutes=5))

    def test_retries_deduplicate_and_ungraded_dispositions_do_not_change_review(self):
        solved = attempt(1)
        ungraded = [
            attempt(index, status=status) for index, status in enumerate(
                (AttemptStatus.STARTED, AttemptStatus.SKIPPED, AttemptStatus.ABANDONED, AttemptStatus.INTERRUPTED),
                start=2,
            )
        ]
        self.assertEqual(
            summarize_attempts((solved, solved, *ungraded)), summarize_attempts((solved,)),
        )
        with self.assertRaisesRegex(ValueError, "Conflicting graded"):
            summarize_attempts((solved, replace(solved, hints_used=1)))

    def test_legacy_rows_remain_counted_and_same_puzzle_id_isolated_by_pack(self):
        archived = PuzzleKey("study", BACK_RANK.puzzle_id)
        legacy = TrainingAttempt.from_legacy(42, archived.pack_id, archived.puzzle_id, "2026-11-26", False, 2, 0, 500)
        self.assertEqual(legacy.status, AttemptStatus.UNSOLVED)
        self.assertEqual(legacy.recorded_at, datetime(2026, 11, 26, tzinfo=timezone.utc))
        items = summarize_attempts((legacy, attempt(1)))
        self.assertEqual(items[archived].solve_rate, 0.0)
        self.assertIsNone(items[archived].best_solve_ms)
        self.assertEqual(items[BACK_RANK].solve_rate, 1.0)

    def test_order_respects_insertion_for_equal_timestamps(self):
        clean = attempt(1)
        shaky = attempt(2, hints=1)
        self.assertEqual(summarize_attempts((clean, shaky))[BACK_RANK].clean_streak, 0)
        self.assertEqual(summarize_attempts((shaky, clean))[BACK_RANK].clean_streak, 1)


class TrainingQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pack = load_demo_pack()
        tasks = (TrainingTask(PuzzleKey(pack.manifest.pack_id, puzzle.puzzle_id), puzzle) for puzzle in pack.puzzles)
        cls.catalog = {task.key: task for task in tasks}

    def queue(self, mode: QueueMode, **options) -> tuple[PuzzleKey, ...]:
        progress = summarize_attempts((
            attempt(1, key=BACK_RANK, offset=-1),
            attempt(2, key=SCHOLAR, hints=1, mistakes=1),
        ))
        tasks = (*reversed(tuple(self.catalog.values())), self.catalog[BACK_RANK])
        return tuple(task.key for task in build_training_queue(
            tasks, progress, as_of=NOW, selection=TrainingSelection(mode, **options),
        ))

    def test_due_boundary_mixed_priority_and_repeat_prevention(self):
        self.assertEqual(self.queue(QueueMode.DUE), (BACK_RANK,))
        self.assertEqual(self.queue(QueueMode.MIXED, limit=1), (BACK_RANK,))
        self.assertEqual(len(self.queue(QueueMode.MIXED)), 4)

    def test_filter_rating_theme_mistakes_and_uncertain(self):
        self.assertEqual(self.queue(QueueMode.NEW, theme="mate", minimum_rating=1200), (SMOTHERED,))
        self.assertEqual(self.queue(QueueMode.NEW, theme="fork"), ())
        self.assertEqual(self.queue(QueueMode.MISTAKES), (SCHOLAR,))
        self.assertEqual(self.queue(QueueMode.UNCERTAIN), (BACK_RANK, SCHOLAR))

    def test_curated_chain_runs_real_puzzle_sessions_and_grades_once(self):
        chain = replace(DEMO_MATE_CHAIN, prerequisites=("warmup",), completion=ChainCompletion.CLEAN)
        with self.assertRaisesRegex(ValueError, "Prerequisites"):
            chain.open(self.catalog)
        with self.assertRaisesRegex(ValueError, "Missing catalog task"):
            chain.open({}, completed_chains=("warmup",))
        training = chain.open(self.catalog, completed_chains=("warmup",))
        for key in chain.tasks:
            session, started = training.start_next(NOW)
            self.assertEqual(started.key, key)
            self.assertEqual(started.status, AttemptStatus.STARTED)
            while not session.finished:
                session.submit(session.expected_move)
            finished = training.finish_current(NOW)
            self.assertEqual(finished.attempt_id, started.attempt_id)
            self.assertTrue(finished.clean)
            with self.assertRaisesRegex(ValueError, "No active"):
                training.finish_current(NOW)
        self.assertTrue(training.exhausted)
        self.assertTrue(training.passed)
        with self.assertRaisesRegex(ValueError, "no unstarted"):
            training.start_next(NOW)

    def test_review_session_can_skip_without_counting_as_solve(self):
        training = TrainingSession((self.catalog[BACK_RANK],))
        training.start_next(NOW)
        with self.assertRaises(ValueError):
            training.finish_current(NOW)
        with self.assertRaises(ValueError):
            training.finish_current(NOW - timedelta(seconds=1), unfinished=AttemptStatus.SKIPPED)
        finished = training.finish_current(NOW, unfinished=AttemptStatus.SKIPPED)
        self.assertTrue(training.exhausted)
        self.assertFalse(training.passed)
        self.assertEqual(summarize_attempts((finished,)), {})

    def test_position_candidate_stays_separate_from_catalog_tasks(self):
        candidate = TrainingCandidate(42, 0, f" {INITIAL_FEN} ")
        self.assertEqual(candidate.fen, INITIAL_FEN)
        self.assertFalse(hasattr(candidate, "rating"))
        with self.assertRaises(ValueError):
            TrainingCandidate(42, 0, "not a FEN")
