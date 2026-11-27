"""Deterministic training queues and progress derived from recorded attempts.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from hashlib import sha256
import json
from time import monotonic
from uuid import UUID, uuid4

from ..chess import Move, parse_fen, to_fen
from .importer import MAX_SOLUTION_PLIES
from .model import Puzzle, ValidationStatus
from .pack import DEMO_PACK_ID, PuzzlePack
from .session import PuzzleSession, Verdict


def _utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        raise ValueError("Training timestamps must be timezone-aware.")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True, order=True)
class PuzzleKey:
    """Identify an installed puzzle across packs sharing the same puzzle IDs."""

    pack_id: str
    puzzle_id: str

    def __post_init__(self) -> None:
        if not self.pack_id or not self.puzzle_id:
            raise ValueError("A puzzle key requires both pack and puzzle IDs.")


class AttemptStatus(StrEnum):
    STARTED = "started"
    SOLVED = "solved"
    REVEALED = "revealed"
    SKIPPED = "skipped"
    ABANDONED = "abandoned"
    INTERRUPTED = "interrupted"
    UNSOLVED = "unsolved"  # Legacy rows lack a more specific disposition.


@dataclass(frozen=True, slots=True)
class TrainingAttempt:
    attempt_id: str
    key: PuzzleKey
    recorded_at: datetime
    status: AttemptStatus
    mistakes: int = 0
    hints_used: int = 0
    duration_ms: int | None = None

    def __post_init__(self) -> None:
        if not self.attempt_id or min(self.mistakes, self.hints_used) < 0:
            raise ValueError("Invalid attempt identity or counters.")
        if self.duration_ms is not None and self.duration_ms < 0:
            raise ValueError("Attempt duration must be non-negative.")
        object.__setattr__(self, "recorded_at", _utc(self.recorded_at))

    @property
    def clean(self) -> bool:
        return self.status is AttemptStatus.SOLVED and self.mistakes == self.hints_used == 0

    @property
    def counted(self) -> bool:
        return self.status in {AttemptStatus.SOLVED, AttemptStatus.REVEALED, AttemptStatus.UNSOLVED}

    @classmethod
    def from_legacy(
        cls, row_id: int, pack_id: str, puzzle_id: str, attempted_utc: str, solved: bool,
        mistakes: int, hints_used: int, duration_ms: int | None,
    ) -> TrainingAttempt:
        """Map a SQLite puzzle_attempts row without inferring missing lifecycle data."""
        recorded_at = datetime.fromisoformat(attempted_utc)
        if recorded_at.utcoffset() is None:
            recorded_at = recorded_at.replace(tzinfo=timezone.utc)
        return cls(
            f"legacy:{row_id}", PuzzleKey(pack_id, puzzle_id), recorded_at,
            AttemptStatus.SOLVED if solved else AttemptStatus.UNSOLVED, mistakes, hints_used, duration_ms,
        )


@dataclass(frozen=True, slots=True)
class ReviewSchedule:
    """Configurable product defaults in elapsed days (UTC)."""

    clean_intervals: tuple[int, ...] = (1, 3, 7, 14, 30)
    retry_delay: timedelta = timedelta(minutes=15)

    def __post_init__(self) -> None:
        intervals = self.clean_intervals
        if not intervals or intervals[0] <= 0 or any(a >= b for a, b in zip(intervals, intervals[1:])):
            raise ValueError("Review intervals must be positive and strictly increasing.")
        if self.retry_delay < timedelta(0):
            raise ValueError("Retry delay must be non-negative.")

    def due_at(self, recorded_at: datetime, clean_streak: int) -> datetime:
        delay = self.retry_delay
        if clean_streak > 0:
            index = min(clean_streak, len(self.clean_intervals)) - 1
            delay = timedelta(days=self.clean_intervals[index])
        return _utc(recorded_at) + delay


@dataclass(frozen=True, slots=True)
class TrainingProgress:
    attempts: int
    solved: int
    clean_solves: int
    hints_used: int
    best_solve_ms: int | None
    last_attempt: TrainingAttempt
    clean_streak: int
    due_at: datetime

    @property
    def solve_rate(self) -> float:
        """Solved attempts divided by graded attempts for this puzzle."""
        return self.solved / self.attempts

    @property
    def secure(self) -> bool:
        """A working training threshold of two consecutive clean solves."""
        return self.clean_streak >= 2


def summarize_attempts(
    attempts: Iterable[TrainingAttempt], schedule: ReviewSchedule = ReviewSchedule(),
) -> dict[PuzzleKey, TrainingProgress]:
    """Grade once per attempt ID, using input order to settle timestamp ties.

    Pass storage rows in insertion order so simultaneous attempts are reproducible.
    Only solved, revealed, and legacy unsolved attempts affect review and statistics.
    """
    graded: dict[str, TrainingAttempt] = {}
    for attempt in attempts:
        if not attempt.counted:
            continue
        previous = graded.setdefault(attempt.attempt_id, attempt)
        if previous != attempt:
            raise ValueError(f"Conflicting graded attempt {attempt.attempt_id}.")
    progress: dict[PuzzleKey, TrainingProgress] = {}
    for attempt in sorted(graded.values(), key=lambda item: item.recorded_at):
        old = progress.get(attempt.key)
        solved = attempt.status is AttemptStatus.SOLVED
        streak = (old.clean_streak if old else 0) + 1 if attempt.clean else 0
        best = old.best_solve_ms if old else None
        if solved and attempt.duration_ms is not None:
            best = attempt.duration_ms if best is None else min(best, attempt.duration_ms)
        progress[attempt.key] = TrainingProgress(
            attempts=(old.attempts if old else 0) + 1,
            solved=(old.solved if old else 0) + int(solved),
            clean_solves=(old.clean_solves if old else 0) + int(attempt.clean),
            hints_used=(old.hints_used if old else 0) + attempt.hints_used,
            best_solve_ms=best,
            last_attempt=attempt,
            clean_streak=streak,
            due_at=schedule.due_at(attempt.recorded_at, streak),
        )
    return progress


@dataclass(frozen=True, slots=True)
class TrainingTask:
    key: PuzzleKey
    puzzle: Puzzle

    def __post_init__(self) -> None:
        if self.key.puzzle_id != self.puzzle.puzzle_id or self.puzzle.validation is not ValidationStatus.VALID:
            raise ValueError("Training tasks require a matching, validated catalog puzzle.")


class QueueMode(StrEnum):
    NEW = "new"
    DUE = "due"
    MISTAKES = "mistakes"
    UNCERTAIN = "uncertain"
    MIXED = "mixed"


@dataclass(frozen=True, slots=True)
class TrainingSelection:
    mode: QueueMode = QueueMode.MIXED
    theme: str | None = None
    minimum_rating: int | None = None
    maximum_rating: int | None = None
    limit: int = 10

    def __post_init__(self) -> None:
        if self.limit < 1:
            raise ValueError("Training queue size must be positive.")
        if (self.minimum_rating is not None and self.maximum_rating is not None
                and self.minimum_rating > self.maximum_rating):
            raise ValueError("Invalid training rating range.")

    def includes(
        self, task: TrainingTask, progress: TrainingProgress | None, as_of: datetime,
    ) -> bool:
        puzzle = task.puzzle
        if self.theme is not None and self.theme not in puzzle.themes:
            return False
        if self.minimum_rating is not None and puzzle.rating < self.minimum_rating:
            return False
        if self.maximum_rating is not None and puzzle.rating > self.maximum_rating:
            return False
        if progress is None:
            return self.mode in {QueueMode.NEW, QueueMode.MIXED}
        if self.mode is QueueMode.NEW:
            return False
        if self.mode is QueueMode.MISTAKES:
            last = progress.last_attempt
            return last.mistakes > 0 or last.status is not AttemptStatus.SOLVED
        if self.mode is QueueMode.UNCERTAIN:
            return not progress.secure
        return progress.due_at <= as_of


def build_training_queue(
    tasks: Iterable[TrainingTask], progress: Mapping[PuzzleKey, TrainingProgress],
    *, as_of: datetime, selection: TrainingSelection = TrainingSelection(),
) -> tuple[TrainingTask, ...]:
    """Pick oldest due reviews first, then fresh tasks by rating and identity."""
    as_of = _utc(as_of)
    candidates: dict[PuzzleKey, TrainingTask] = {}
    for task in tasks:
        if selection.includes(task, progress.get(task.key), as_of):
            previous = candidates.setdefault(task.key, task)
            if previous != task:
                raise ValueError(f"Conflicting catalog task {task.key}.")
    return tuple(sorted(
        candidates.values(),
        key=lambda task: (
            task.key not in progress,
            progress[task.key].due_at if task.key in progress else as_of,
            task.puzzle.rating,
            task.key,
        ),
    )[:selection.limit])


class ChainCompletion(StrEnum):
    SOLVED = "solved"
    CLEAN = "clean"


MAX_TRAINING_CHECKPOINT_BYTES = 64 * 1024
_TRAINING_CHECKPOINT_VERSION = 1


@dataclass(frozen=True, slots=True)
class ActivePuzzleCheckpoint:
    started: TrainingAttempt
    moves: tuple[Move, ...]
    status: AttemptStatus
    mistakes: int
    hints_used: int
    elapsed_ms: int

    def __post_init__(self) -> None:
        if self.started.status is not AttemptStatus.STARTED or any(
            (self.started.mistakes, self.started.hints_used, self.started.duration_ms is not None)
        ):
            raise ValueError("The active puzzle needs an ungraded starting attempt.")
        if not 1 <= len(self.moves) <= MAX_SOLUTION_PLIES:
            raise ValueError("Invalid saved puzzle moves.")
        if self.status not in {AttemptStatus.STARTED, AttemptStatus.SOLVED, AttemptStatus.REVEALED}:
            raise ValueError("Invalid active puzzle status.")
        _checkpoint_integer(self.mistakes)
        _checkpoint_integer(self.hints_used)
        _checkpoint_integer(self.elapsed_ms)


@dataclass(frozen=True, slots=True)
class TrainingCheckpoint:
    """Serializable progress for a single run of a curated chain."""

    chain_id: str
    session_id: str
    signature: str
    attempts: tuple[TrainingAttempt, ...]
    active: ActivePuzzleCheckpoint | None = None

    def __post_init__(self) -> None:
        if not self.chain_id or not _is_uuid(self.session_id) or (
            len(self.signature) != 64 or any(char not in "0123456789abcdef" for char in self.signature)
        ):
            raise ValueError("Invalid chain checkpoint identity.")
        if any(attempt.status in {AttemptStatus.STARTED, AttemptStatus.UNSOLVED} for attempt in self.attempts):
            raise ValueError("Invalid completed chain attempt status.")
        attempts = self.attempts + ((self.active.started,) if self.active else ())
        if any(not _is_uuid(attempt.attempt_id) for attempt in attempts):
            raise ValueError("Invalid chain attempt ID.")
        if len({attempt.attempt_id for attempt in attempts}) != len(attempts):
            raise ValueError("A chain checkpoint cannot repeat an attempt ID.")
        if len({attempt.key for attempt in attempts}) != len(attempts):
            raise ValueError("A chain checkpoint cannot repeat a task.")

    def encode(self) -> str:
        active = self.active
        payload = json.dumps({
            "version": _TRAINING_CHECKPOINT_VERSION,
            "chain_id": self.chain_id,
            "session_id": self.session_id,
            "signature": self.signature,
            "attempts": [_attempt_record(attempt) for attempt in self.attempts],
            "active": {
                "started": _attempt_record(active.started),
                "moves": [move.to_uci() for move in active.moves],
                "status": active.status,
                "mistakes": active.mistakes,
                "hints_used": active.hints_used,
                "elapsed_ms": active.elapsed_ms,
            } if active else None,
        }, ensure_ascii=True, separators=(",", ":"))
        if len(payload) > MAX_TRAINING_CHECKPOINT_BYTES:
            raise ValueError("The chain checkpoint exceeds its size limit.")
        return payload

    @classmethod
    def decode(cls, payload: str) -> TrainingCheckpoint:
        """Decode bounded data. Resume against the catalog to validate the game."""
        if len(payload) > MAX_TRAINING_CHECKPOINT_BYTES or len(payload.encode("utf-8")) > MAX_TRAINING_CHECKPOINT_BYTES:
            raise ValueError("The chain checkpoint exceeds its size limit.")
        try:
            data = json.loads(payload)
            if not isinstance(data, dict) or type(data.get("version")) is not int or (
                data["version"] != _TRAINING_CHECKPOINT_VERSION
            ):
                raise ValueError("Unsupported chain checkpoint version.")
            if not isinstance(data["attempts"], list):
                raise ValueError("Invalid chain attempt list.")
            record = data["active"]
            active = None
            if record is not None:
                if not isinstance(record["moves"], list):
                    raise ValueError("Invalid saved puzzle moves.")
                active = ActivePuzzleCheckpoint(
                    _read_attempt(record["started"]),
                    tuple(Move.from_uci(_checkpoint_text(text)) for text in record["moves"]),
                    AttemptStatus(record["status"]),
                    _checkpoint_integer(record["mistakes"]),
                    _checkpoint_integer(record["hints_used"]),
                    _checkpoint_integer(record["elapsed_ms"]),
                )
            return cls(
                _checkpoint_text(data["chain_id"]), _checkpoint_text(data["session_id"]),
                _checkpoint_text(data["signature"]), tuple(_read_attempt(record) for record in data["attempts"]),
                active,
            )
        except (KeyError, TypeError, RecursionError) as error:
            raise ValueError("Invalid chain checkpoint data.") from error


def _checkpoint_integer(value: object) -> int:
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise ValueError("Invalid chain checkpoint counter.")
    return value


def _checkpoint_text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Invalid chain checkpoint text.")
    return value


def _is_uuid(value: str) -> bool:
    try:
        return str(UUID(value)) == value
    except ValueError:
        return False


def _attempt_record(attempt: TrainingAttempt) -> dict[str, object]:
    return {
        "id": attempt.attempt_id,
        "pack": attempt.key.pack_id,
        "puzzle": attempt.key.puzzle_id,
        "recorded_at": attempt.recorded_at.isoformat(),
        "status": attempt.status,
        "mistakes": attempt.mistakes,
        "hints_used": attempt.hints_used,
        "duration_ms": attempt.duration_ms,
    }


def _read_attempt(record: dict[str, object]) -> TrainingAttempt:
    duration = record["duration_ms"]
    return TrainingAttempt(
        _checkpoint_text(record["id"]),
        PuzzleKey(_checkpoint_text(record["pack"]), _checkpoint_text(record["puzzle"])),
        datetime.fromisoformat(_checkpoint_text(record["recorded_at"])),
        AttemptStatus(record["status"]),
        _checkpoint_integer(record["mistakes"]), _checkpoint_integer(record["hints_used"]),
        _checkpoint_integer(duration) if duration is not None else None,
    )


@dataclass(frozen=True, slots=True)
class TrainingChain:
    chain_id: str
    name_key: str
    goal_key: str
    tasks: tuple[PuzzleKey, ...]
    themes: tuple[str, ...] = ()
    prerequisites: tuple[str, ...] = ()
    completion: ChainCompletion = ChainCompletion.SOLVED

    def __post_init__(self) -> None:
        if not all((self.chain_id, self.name_key, self.goal_key, self.tasks)):
            raise ValueError("A training chain requires an ID, text keys and an ordered task list.")
        if len(set(self.tasks)) != len(self.tasks) or self.chain_id in self.prerequisites:
            raise ValueError("A chain cannot repeat tasks or require itself.")

    def open(
        self, catalog: Mapping[PuzzleKey, TrainingTask], *, completed_chains: Iterable[str] = (),
        clock: Callable[[], float] = monotonic,
    ) -> TrainingSession:
        if set(self.prerequisites).difference(completed_chains):
            raise ValueError(f"Prerequisites are missing for chain {self.chain_id}.")
        try:
            tasks = tuple(catalog[key] for key in self.tasks)
        except KeyError as error:
            raise ValueError(f"Missing catalog task for chain {self.chain_id}: {error}") from error
        if tuple(task.key for task in tasks) != self.tasks:
            raise ValueError(f"Catalog identity mismatch for chain {self.chain_id}.")
        signature = self._signature(tasks)
        return TrainingSession(tasks, completion=self.completion, chain_id=self.chain_id, signature=signature, clock=clock)

    def resume(
        self, catalog: Mapping[PuzzleKey, TrainingTask], checkpoint: TrainingCheckpoint,
        *, completed_chains: Iterable[str] = (), clock: Callable[[], float] = monotonic,
    ) -> TrainingSession:
        session = self.open(catalog, completed_chains=completed_chains, clock=clock)
        session._restore(checkpoint)
        return session

    def _signature(self, tasks: tuple[TrainingTask, ...]) -> str:
        puzzle_lines = [
            (task.key.pack_id, task.key.puzzle_id, to_fen(task.puzzle.initial_state()), task.puzzle.setup_move.to_uci(),
             [move.to_uci() for move in task.puzzle.solution])
            for task in tasks
        ]
        return sha256(json.dumps((self.chain_id, self.completion, self.prerequisites, puzzle_lines)).encode()).hexdigest()


class TrainingSession:
    """Run a bounded queue using the existing PuzzleSession rules.

    Each item may finish once and yields one record. The caller owns committing
    records and must retain a failed write for retry before advancing its UI.
    """

    def __init__(
        self, tasks: Iterable[TrainingTask], *, completion: ChainCompletion = ChainCompletion.SOLVED,
        chain_id: str | None = None, signature: str | None = None, clock: Callable[[], float] = monotonic,
    ) -> None:
        self.tasks = tuple(tasks)
        if len({task.key for task in self.tasks}) != len(self.tasks):
            raise ValueError("A training session cannot repeat a puzzle.")
        self._completion = completion
        self._chain_id = chain_id
        self._signature = signature
        self._session_id = str(uuid4())
        self._clock = clock
        self._elapsed: Callable[[], float] | None = None
        self._attempts: list[TrainingAttempt] = []
        self._current: PuzzleSession | None = None
        self._started_attempt: TrainingAttempt | None = None

    @property
    def current(self) -> PuzzleSession | None:
        return self._current

    def checkpoint(self) -> TrainingCheckpoint:
        if self._chain_id is None or self._signature is None:
            raise ValueError("Only curated chains can be checkpointed.")
        active = None
        current, started, elapsed = self._current, self._started_attempt, self._elapsed
        if current is not None and started is not None and elapsed is not None:
            status = AttemptStatus.STARTED
            if current.solved:
                status = AttemptStatus.SOLVED
            elif current.revealed:
                status = AttemptStatus.REVEALED
            time_ms = current.duration_ms if current.duration_ms is not None else int(elapsed() * 1000)
            active = ActivePuzzleCheckpoint(
                started, tuple(current.game.moves), status, current.mistakes, current.hints_used, time_ms,
            )
        return TrainingCheckpoint(self._chain_id, self._session_id, self._signature, self.attempts, active)

    def _restore(self, checkpoint: TrainingCheckpoint) -> None:
        if (checkpoint.chain_id, checkpoint.signature) != (self._chain_id, self._signature):
            raise ValueError("The saved chain differs from the installed chain.")
        active = checkpoint.active
        saved_keys = tuple(attempt.key for attempt in checkpoint.attempts)
        if active is not None:
            saved_keys += (active.started.key,)
        if saved_keys != tuple(task.key for task in self.tasks[:len(saved_keys)]):
            raise ValueError("The saved attempts do not match the chain order.")
        self._session_id = checkpoint.session_id
        self._attempts.extend(checkpoint.attempts)
        if active is not None:
            self._open_puzzle(active.started, checkpoint=active)

    def _open_puzzle(
        self, started: TrainingAttempt, *, checkpoint: ActivePuzzleCheckpoint | None = None,
    ) -> PuzzleSession:
        task = self.tasks[len(self._attempts)]
        origin = None
        offset = checkpoint.elapsed_ms / 1000 if checkpoint else 0.0

        def elapsed() -> float:
            # During setup and replay, the clock still reads zero.
            return 0.0 if origin is None else offset + self._clock() - origin

        puzzle = PuzzleSession(task.puzzle, clock=elapsed)
        if checkpoint is not None:
            if checkpoint.status is AttemptStatus.REVEALED:
                puzzle.reveal()
            else:
                for move in checkpoint.moves[1::2]:
                    if puzzle.finished or puzzle.submit(move).verdict not in {Verdict.CORRECT, Verdict.SOLVED}:
                        raise ValueError("Illegal move in the saved puzzle.")
            if tuple(puzzle.game.moves) != checkpoint.moves or puzzle.solved != (checkpoint.status is AttemptStatus.SOLVED):
                raise ValueError("The saved moves do not match the puzzle state.")
            puzzle.mistakes = checkpoint.mistakes
            puzzle.hints_used = checkpoint.hints_used
            if puzzle.finished:
                puzzle.duration_ms = checkpoint.elapsed_ms
        origin = self._clock()
        self._elapsed = elapsed
        self._current = puzzle
        self._started_attempt = started
        return puzzle

    @property
    def attempts(self) -> tuple[TrainingAttempt, ...]:
        return tuple(self._attempts)

    @property
    def exhausted(self) -> bool:
        return len(self._attempts) == len(self.tasks)

    @property
    def passed(self) -> bool:
        if not self.tasks or not self.exhausted:
            return False
        if self._completion is ChainCompletion.CLEAN:
            return all(attempt.clean for attempt in self._attempts)
        return all(attempt.status is AttemptStatus.SOLVED for attempt in self._attempts)

    def start_next(self, at: datetime) -> tuple[PuzzleSession, TrainingAttempt]:
        if self._current is not None or self.exhausted:
            raise ValueError("Training has no unstarted next task.")
        task = self.tasks[len(self._attempts)]
        attempt = TrainingAttempt(str(uuid4()), task.key, at, AttemptStatus.STARTED)
        return self._open_puzzle(attempt), attempt

    def finish_current(self, at: datetime, *, unfinished: AttemptStatus | None = None) -> TrainingAttempt:
        current, started = self._current, self._started_attempt
        if current is None or started is None:
            raise ValueError("No active training task.")
        if current.finished:
            if unfinished is not None:
                raise ValueError("A completed puzzle already has an outcome.")
            status = AttemptStatus.SOLVED if current.solved else AttemptStatus.REVEALED
        elif unfinished in {AttemptStatus.SKIPPED, AttemptStatus.ABANDONED, AttemptStatus.INTERRUPTED}:
            status = unfinished
        else:
            raise ValueError("An unfinished puzzle requires a disposition.")
        if _utc(at) < started.recorded_at:
            raise ValueError("An attempt cannot finish before it started.")
        attempt = TrainingAttempt(
            started.attempt_id, started.key, at, status, current.mistakes, current.hints_used, current.duration_ms,
        )
        self._attempts.append(attempt)
        self._current = None
        self._started_attempt = None
        self._elapsed = None
        return attempt


@dataclass(frozen=True, slots=True)
class TrainingCandidate:
    """A position from analysis awaiting validation as a playable puzzle."""

    source_game_id: int
    ply: int
    fen: str

    def __post_init__(self) -> None:
        if self.source_game_id < 1 or self.ply < 0:
            raise ValueError("A training candidate requires a saved game and valid ply.")
        object.__setattr__(self, "fen", to_fen(parse_fen(self.fen)))


DEMO_MATE_CHAIN = TrainingChain(
    chain_id="demo-mating-patterns",
    name_key="training.chain.demo_mate.name",
    goal_key="training.chain.demo_mate.goal",
    tasks=tuple(PuzzleKey(DEMO_PACK_ID, puzzle_id) for puzzle_id in ("ccBR01", "ccQB01", "ccSM02")),
    themes=("mate",),
)


def demo_chain_catalog(pack: PuzzlePack) -> dict[PuzzleKey, TrainingTask]:
    """Use the bundled demo's validated tasks for curated chain play and restore."""
    if pack.manifest.pack_id != DEMO_PACK_ID:
        raise ValueError("The curated demo chain requires the demo puzzle pack.")
    tasks = (TrainingTask(PuzzleKey(DEMO_PACK_ID, puzzle.puzzle_id), puzzle) for puzzle in pack.puzzles)
    catalog = {task.key: task for task in tasks}
    if len(catalog) != len(pack.puzzles):
        raise ValueError("The demo puzzle pack repeats a puzzle ID.")
    return catalog
