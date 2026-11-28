"""Headless UCI analysis on a process separate from live play.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
from dataclasses import asdict, dataclass, field, replace
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import threading
import time
from uuid import uuid4

from ..chess import ChessError, ChessGame, Color, GameStatus, INITIAL_FEN, Move, parse_fen, to_fen
from .analysis_cache import PersistentAnalysisCache
from .bot import EngineConfig
from .uci import UCIEngine, UCIEngineError

ANALYSIS_SCHEMA = 1
MAX_PLIES = 512
MAX_PV_PLIES = 256
MAX_MOVETIME_MS = 5000
MAX_VARIANTS = 8
RESOURCE_OPTIONS = (("Threads", 1), ("Hash", 16))


class EvaluationKind(StrEnum):
    CENTIPAWNS = "cp"
    MATE = "mate"


class ScoreBound(StrEnum):
    EXACT = "exact"
    LOWER = "lower"
    UPPER = "upper"


@dataclass(frozen=True, slots=True)
class Evaluation:
    kind: EvaluationKind
    value: int
    bound: ScoreBound = ScoreBound.EXACT
    perspective: Color = Color.WHITE
    raw_value: int | None = field(default=None, compare=False)
    raw_bound: ScoreBound | None = field(default=None, compare=False)

    def for_player(self, player: Color) -> tuple[int, ScoreBound]:
        if player is self.perspective:
            return self.value, self.bound
        flipped = {ScoreBound.LOWER: ScoreBound.UPPER, ScoreBound.UPPER: ScoreBound.LOWER}.get(self.bound, self.bound)
        return -self.value, flipped


@dataclass(frozen=True, slots=True)
class AnalysisLine:
    rank: int
    moves: tuple[Move, ...]
    evaluation: Evaluation | None
    depth: int | None = None
    selective_depth: int | None = None
    nodes: int | None = None
    nodes_per_second: int | None = None
    time_ms: int | None = None


_INFO_INTS = {
    "depth", "seldepth", "multipv", "nodes", "nps", "time",
}
_INFO_FIELDS = _INFO_INTS | {
    "score", "pv", "string", "currmove", "currmovenumber", "hashfull", "tbhits",
    "sbhits", "cpuload", "refutation", "currline", "wdl",
}


def _integer(token: str) -> int | None:
    try:
        return int(token)
    except ValueError:
        return None


def parse_info(text: str, turn: Color) -> AnalysisLine | None:
    """Read one UCI PV update. The side-to-move score is normalized to White."""
    if len(text) > 8192:
        return None
    tokens = text.split()
    if tokens[:1] != ["info"]:
        return None
    values: dict[str, int] = {}
    evaluation = None
    moves = ()
    index = 1
    while index < len(tokens):
        field = tokens[index]
        index += 1
        if field == "string":
            break
        if field in _INFO_INTS and index < len(tokens):
            value = _integer(tokens[index])
            if value is not None and value >= 0:
                values[field] = value
                index += 1
        elif field == "score" and tokens[index:index + 1] in (["cp"], ["mate"]):
            if index + 1 >= len(tokens):
                continue
            kind = EvaluationKind(tokens[index])
            value = _integer(tokens[index + 1])
            if value is None:
                continue
            index += 2
            bound = ScoreBound.EXACT
            if tokens[index:index + 1] in (["lowerbound"], ["upperbound"]):
                bound = ScoreBound.LOWER if tokens[index] == "lowerbound" else ScoreBound.UPPER
                index += 1
            raw_value, raw_bound = value, bound
            if turn is Color.BLACK:
                value = -value
                bound = {ScoreBound.LOWER: ScoreBound.UPPER, ScoreBound.UPPER: ScoreBound.LOWER}.get(bound, bound)
            evaluation = Evaluation(kind, value, bound, raw_value=raw_value, raw_bound=raw_bound)
        elif field == "pv":
            start = index
            while index < len(tokens) and tokens[index] not in _INFO_FIELDS:
                index += 1
            if not 0 < index - start <= MAX_PV_PLIES:
                return None
            try:
                moves = tuple(Move.from_uci(token) for token in tokens[start:index])
            except ChessError:
                return None
    rank = values.get("multipv", 1)
    if not moves or not 1 <= rank <= MAX_VARIANTS:
        return None
    return AnalysisLine(rank, moves, evaluation, *(values.get(key) for key in ("depth", "seldepth", "nodes", "nps", "time")))


class AnalysisMode(StrEnum):
    POSITION = "position"
    SELECTED = "selected"
    GAME = "game"


@dataclass(frozen=True, slots=True)
class AnalysisRequest:
    job_id: str
    initial_fen: str = INITIAL_FEN
    moves: tuple[Move, ...] = ()
    mode: AnalysisMode = AnalysisMode.POSITION
    selected_plies: tuple[int, ...] = ()
    movetime_ms: int = 100
    multipv: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.job_id, str) or not 1 <= len(self.job_id) <= 128 or not isinstance(self.mode, AnalysisMode):
            raise ValueError("An analysis job requires an ID and a supported mode.")
        if not isinstance(self.initial_fen, str) or len(self.initial_fen) > 4096:
            raise ValueError("Invalid analysis FEN.")
        object.__setattr__(self, "moves", tuple(self.moves))
        object.__setattr__(self, "selected_plies", tuple(self.selected_plies))
        if type(self.movetime_ms) is not int or not 1 <= self.movetime_ms <= MAX_MOVETIME_MS:
            raise ValueError(f"Analysis movetime must be between 1 and {MAX_MOVETIME_MS} ms.")
        if type(self.multipv) is not int or not 1 <= self.multipv <= MAX_VARIANTS:
            raise ValueError(f"Analysis MultiPV must be between 1 and {MAX_VARIANTS}.")
        if len(self.moves) > MAX_PLIES or any(not isinstance(move, Move) for move in self.moves):
            raise ValueError(f"Analysis accepts at most {MAX_PLIES} chess moves.")
        if self.mode is AnalysisMode.SELECTED:
            if not self.selected_plies or any(
                type(ply) is not int or not 0 <= ply <= len(self.moves) for ply in self.selected_plies
            ):
                raise ValueError("Select existing position indices from the supplied game.")
        elif self.selected_plies:
            raise ValueError("Selected plies are only supported in selected mode.")

    @property
    def plies(self) -> tuple[int, ...]:
        if self.mode is AnalysisMode.GAME:
            return tuple(range(len(self.moves) + 1))
        if self.mode is AnalysisMode.SELECTED:
            return tuple(sorted(set(self.selected_plies)))
        return (len(self.moves),)


@dataclass(frozen=True, slots=True)
class AnalysisConfiguration:
    engine_id: str
    engine_name: str
    engine_version: str | None
    options: tuple[tuple[str, int], ...]
    movetime_ms: int
    multipv: int
    requested_multipv: int
    engine_source: str
    is_mock: bool


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    initial_fen: str
    history: tuple[Move, ...]
    fen: str
    turn: Color
    configuration: AnalysisConfiguration
    lines: tuple[AnalysisLine, ...]
    best_move: Move | None
    elapsed_ms: int
    outcome: str = "active"
    cached: bool = False
    comparison: tuple[AnalysisLine, AnalysisLine] | None = None


class JobStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class AnalysisProgress:
    job_id: str
    status: JobStatus
    total: int
    results: tuple[AnalysisResult, ...]
    error: str | None = None


class AnalysisJob:
    """UI-safe polling and cancellation. Wait only in a headless caller."""

    def __init__(self, request: AnalysisRequest) -> None:
        self._request = request
        self._cancel = threading.Event()
        self._done = threading.Event()
        self._lock = threading.Lock()
        self._status = JobStatus.RUNNING
        self._results: list[AnalysisResult] = []
        self._error: str | None = None

    def cancel(self) -> None:
        self._cancel.set()

    def wait(self, timeout: float | None = None) -> bool:
        return self._done.wait(timeout)

    def progress(self) -> AnalysisProgress:
        with self._lock:
            return AnalysisProgress(
                self._request.job_id, self._status, len(self._request.plies),
                tuple(self._results), self._error,
            )

    def _append(self, result: AnalysisResult) -> None:
        with self._lock:
            self._results.append(result)

    def _finish(self, status: JobStatus, error: str | None) -> None:
        with self._lock:
            self._status = status
            self._error = error
            self._done.set()


class AnalysisService:
    """One job at a time, independent engine, bounded process-local LRU cache."""

    def __init__(
        self, config: EngineConfig, *, engine_id: str, engine_version: str | None = None,
        cache_size: int = 64, cache_path: Path | None = None,
    ) -> None:
        if not engine_id or type(cache_size) is not int or not 0 <= cache_size <= 128:
            raise ValueError("Analysis requires an engine ID and a cache size from 0 to 128.")
        self._config = config
        self._engine_id = engine_id
        self._engine_version = engine_version
        self._cache_size = cache_size if engine_version is not None or config.provenance is not None else 0
        self._persistent = PersistentAnalysisCache(cache_path) if cache_path is not None and config.provenance else None
        self._cache: OrderedDict[
            tuple[int, str, tuple[Move, ...], AnalysisConfiguration, AnalysisMode, Move | None], AnalysisResult
        ] = OrderedDict()
        self._lock = threading.Lock()
        self._job: AnalysisJob | None = None

    def start(self, request: AnalysisRequest) -> AnalysisJob:
        with self._lock:
            if self._job is not None and not self._job.wait(0):
                raise RuntimeError("An analysis job is already running.")
            job = AnalysisJob(request)
            threading.Thread(target=self._run, args=(request, job), daemon=True, name="uci-analysis").start()
            self._job = job
            return job

    def _run(self, request: AnalysisRequest, job: AnalysisJob) -> None:
        error = None
        pending: list[tuple] = []
        try:
            self._analyse(request, job, pending)
        except Exception as exc:
            error = str(exc)
        if job._cancel.is_set():
            status = JobStatus.CANCELLED
            error = None
        else:
            status = JobStatus.COMPLETED if error is None else JobStatus.FAILED
        if status is JobStatus.COMPLETED:
            for key, persistent_key, result in pending:
                if self._persistent is not None and persistent_key is not None:
                    self._persistent.store(persistent_key, result)
                if self._cache_size:
                    self._cache[key] = result
                    if len(self._cache) > self._cache_size:
                        self._cache.popitem(last=False)
        job._finish(status, error)

    def _analyse(self, request: AnalysisRequest, job: AnalysisJob, pending: list[tuple]) -> None:
        initial = parse_fen(request.initial_fen)
        initial_fen = to_fen(initial)
        game = ChessGame(initial)
        # Validate the entire supplied record before starting an engine, including
        # positions beyond the last selected ply. Older supported archives may
        # continue through positions now adjudicated as dead.
        with game.replay_record():
            for move in request.moves:
                if job._cancel.is_set():
                    return
                game.play(move)
        game = ChessGame(initial)
        engine = UCIEngine(self._config.command, before_launch=self._config.before_launch)
        try:
            for ply in request.plies:
                if job._cancel.is_set():
                    return
                with game.replay_record():
                    for move in request.moves[len(game.moves):ply]:
                        game.play(move)
                result = self._analyse_position(request, job, engine, initial_fen, game, pending)
                if not job._cancel.is_set():
                    job._append(result)
        finally:
            engine.close()

    def _analyse_position(
        self, request: AnalysisRequest, job: AnalysisJob, engine: UCIEngine,
        initial_fen: str, game: ChessGame, pending: list[tuple],
    ) -> AnalysisResult:
        history = tuple(game.moves)
        fen = to_fen(game.state)
        outcome = game.outcome().status
        if outcome is not GameStatus.ACTIVE:
            details = AnalysisConfiguration(
                self._engine_id, self._config.display_name, self._engine_version, (),
                request.movetime_ms, 0, request.multipv,
                self._config.source, self._config.is_mock,
            )
            return AnalysisResult(initial_fen, history, fen, game.state.turn, details, (), None, 0, outcome.name.lower())
        if not engine.running:
            engine.start()
            for name, value in self._config.approved_options:
                engine.set_option(name, value)
        legal = game.rules.legal_moves(game.state)
        variants = min(len(legal), request.multipv)
        applied = _set_analysis_options(engine, variants)
        actual = next((value for name, value in applied if name.casefold() == "multipv"), 1)
        configuration = AnalysisConfiguration(
            self._engine_id, engine.name or self._config.display_name, self._engine_version,
            applied, request.movetime_ms, actual, request.multipv,
            self._config.source, self._config.is_mock,
        )
        played = request.moves[len(history)] if request.mode is AnalysisMode.GAME and len(history) < len(request.moves) else None
        key = ANALYSIS_SCHEMA, initial_fen, history, configuration, request.mode, played
        if key in self._cache:
            self._cache.move_to_end(key)
            return replace(self._cache[key], cached=True)
        persistent = self._persistent
        persistent_key = None
        if persistent is not None:
            assert self._config.provenance is not None
            persistent_key = persistent.key(
                initial_fen, tuple(move.to_uci() for move in history), configuration,
                engine_fingerprint=self._config.provenance.configuration_fingerprint,
                binary=self._config.provenance.binary_sha256, position=fen, requested_mode=request.mode,
                search_mode="movetime", approved_options=self._config.approved_options, version=ANALYSIS_SCHEMA,
                played=played.to_uci() if played is not None else None, comparison_schema=1,
            )
            cached = persistent.load(persistent_key, game, configuration)
            if cached is not None:
                return replace(cached, cached=True)
        engine.new_game()
        engine.set_position(initial_fen, history)
        lines: dict[int, AnalysisLine] = {}
        turn = game.state.turn

        def receive(text: str) -> None:
            line = parse_info(text, turn)
            if line is None or line.rank > actual:
                return
            previous = lines.get(line.rank)
            if previous is not None and (previous.depth or 0) > (line.depth or 0):
                return
            if _valid_line(game, line.moves):
                lines[line.rank] = line

        started = time.monotonic()
        best_move = engine.go_movetime(
            request.movetime_ms, legal, timeout=request.movetime_ms / 1000 + 3,
            cancelled=job._cancel, on_info=receive,
        )
        comparison = None
        if (self._config.provenance is not None and played is not None and best_move is not None
                and best_move != played and not job._cancel.is_set()):
            comparison = _compare_root_moves(engine, request, job, game, initial_fen, best_move, played)
        result = AnalysisResult(
            initial_fen, history, fen, turn, configuration,
            tuple(lines[rank] for rank in sorted(lines)), best_move,
            round((time.monotonic() - started) * 1000), comparison=comparison,
        )
        if (self._cache_size or persistent is not None) and result.lines and best_move is not None:
            if not job._cancel.is_set():
                pending.append((key, persistent_key, result))
        return result


def _compare_root_moves(
    engine: UCIEngine, request: AnalysisRequest, job: AnalysisJob, game: ChessGame,
    initial_fen: str, best: Move, played: Move,
) -> tuple[AnalysisLine, AnalysisLine] | None:
    legal = game.rules.legal_moves(game.state)
    candidates: list[AnalysisLine] = []
    try:
        _set_analysis_options(engine, 1)
        for root_move in (best, played):
            if job._cancel.is_set():
                return None
            candidate = None

            def receive(text: str) -> None:
                nonlocal candidate
                line = parse_info(text, game.state.turn)
                if (line is not None and line.rank == 1 and line.moves[0] == root_move
                        and _valid_line(game, line.moves)
                        and (candidate is None or (line.depth or 0) >= (candidate.depth or 0))):
                    candidate = line

            engine.new_game()
            engine.set_position(initial_fen, game.moves)
            selected = engine.go_movetime(
                request.movetime_ms, legal, timeout=request.movetime_ms / 1000 + 3,
                cancelled=job._cancel, on_info=receive, search_moves=(root_move,),
            )
            if selected != root_move or candidate is None:
                return None
            candidates.append(candidate)
    except (UCIEngineError, ValueError):
        engine.close()
        return None
    return candidates[0], candidates[1]


def _set_analysis_options(engine: UCIEngine, variants: int) -> tuple[tuple[str, int], ...]:
    declared = {name.casefold(): option for name, option in engine.options.items()}
    applied = []
    for name, desired in (*RESOURCE_OPTIONS, ("MultiPV", variants)):
        option = declared.get(name.casefold())
        if option is None or option.kind != "spin":
            continue
        if option.maximum is not None:
            desired = min(desired, option.maximum)
        if desired < 1 or (option.minimum is not None and option.minimum > desired):
            raise ValueError(f"Engine {option.name} option exceeds the analysis limit.")
        engine.set_option(option.name, desired)
        applied.append((option.name, desired))
    return tuple(applied)


def _valid_line(game: ChessGame, moves: tuple[Move, ...]) -> bool:
    start = len(game.moves)
    try:
        for move in moves:
            game.play(move)
    except ChessError:
        return False
    finally:
        while len(game.moves) > start:
            game.undo()
    return True


@dataclass(frozen=True, slots=True)
class CriticalMoment:
    ply: int
    played_move: Move
    alternative: Move
    centipawn_loss: int | None
    category: str = "mistake"
    comparison: str = "adjacent-estimate"


def critical_moments(
    results: tuple[AnalysisResult, ...], *, threshold_cp: int = 150, severe_cp: int = 300,
) -> tuple[CriticalMoment, ...]:
    """Prefer comparable same-root results and label legacy adjacent estimates."""
    if type(threshold_cp) is not int or type(severe_cp) is not int or not 0 < threshold_cp <= severe_cp:
        raise ValueError("A critical-moment threshold must be a positive CP value.")
    moments = []
    for before, after in zip(results, results[1:]):
        if before.initial_fen != after.initial_fen:
            continue
        if not after.history or after.history[:-1] != before.history:
            continue
        played = after.history[-1]
        alternative = before.best_move
        if alternative is None or played == alternative:
            continue
        method = "same-position" if before.comparison is not None else "adjacent-estimate"
        if before.comparison is not None:
            best_line, played_line = before.comparison
            if (best_line.moves[0] != alternative or played_line.moves[0] != played
                    or best_line.evaluation is None or played_line.evaluation is None):
                continue
            old, new = best_line.evaluation, played_line.evaluation
        else:
            if before.configuration.engine_id.startswith("uci1:") or before.configuration != after.configuration:
                continue
            if (not before.lines or not after.lines or before.lines[0].rank != 1 or after.lines[0].rank != 1
                    or alternative != before.lines[0].moves[0] or after.best_move != after.lines[0].moves[0]):
                continue
            old, new = before.lines[0].evaluation, after.lines[0].evaluation
        if old is None or new is None or old.bound is not ScoreBound.EXACT or new.bound is not ScoreBound.EXACT:
            continue
        old_value = old.for_player(before.turn)[0]
        new_value = new.for_player(before.turn)[0]
        ply = len(after.history)
        if _comparable_cp(old, new):
            loss = old_value - new_value
            if loss >= threshold_cp:
                moments.append(CriticalMoment(ply, played, alternative, loss,
                                              "blunder" if loss >= severe_cp else "mistake", method))
        elif method == "same-position":
            category = _mate_change(old, new, old_value, new_value)
            if category is not None:
                moments.append(CriticalMoment(ply, played, alternative, None, category, method))
    return tuple(moments)


def _mate_change(old: Evaluation, new: Evaluation, old_value: int, new_value: int) -> str | None:
    old_mate = old_value if old.kind is EvaluationKind.MATE else None
    new_mate = new_value if new.kind is EvaluationKind.MATE else None
    if old_mate is not None and new_mate is not None and old_mate * new_mate > 0:
        return "mate-distance" if old_mate != new_mate else None
    if new_mate is not None and new_mate < 0:
        return "allowed-mate"
    if old_mate is not None and old_mate > 0:
        return "missed-mate"
    if old_mate is not None and old_mate < 0:
        return "defended-mate"
    return None


def _comparable_cp(first: Evaluation | None, second: Evaluation | None) -> bool:
    return all(
        score is not None and score.kind is EvaluationKind.CENTIPAWNS
        and score.bound is ScoreBound.EXACT and score.perspective is Color.WHITE
        for score in (first, second)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True, help="Explicit path to the local UCI executable.")
    parser.add_argument("--fen", default=INITIAL_FEN)
    parser.add_argument("--moves", nargs="*", default=(), help="Played UCI moves in order.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--game", action="store_true", help="Analyse every supplied position.")
    mode.add_argument("--plies", type=int, nargs="+", help="Analyse selected position indices, starting from 0.")
    parser.add_argument("--movetime-ms", type=int, default=100)
    parser.add_argument("--multipv", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        executable_path = args.engine.resolve()
        config = EngineConfig.from_path(executable_path)
        with executable_path.open("rb") as executable:
            digest = hashlib.file_digest(executable, "sha256").hexdigest()
        analysis_mode = AnalysisMode.POSITION
        if args.game:
            analysis_mode = AnalysisMode.GAME
        elif args.plies:
            analysis_mode = AnalysisMode.SELECTED
        request = AnalysisRequest(
            uuid4().hex, args.fen, tuple(Move.from_uci(move) for move in args.moves), analysis_mode,
            tuple(args.plies or ()), movetime_ms=args.movetime_ms, multipv=args.multipv,
        )
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    service = AnalysisService(config, engine_id=config.display_name, engine_version=digest)
    job = service.start(request)
    try:
        job.wait()
    except KeyboardInterrupt:
        job.cancel()
        job.wait()
    progress = job.progress()
    print(json.dumps(asdict(progress)))
    return {JobStatus.COMPLETED: 0, JobStatus.CANCELLED: 130}.get(progress.status, 1)


if __name__ == "__main__":
    raise SystemExit(main())
