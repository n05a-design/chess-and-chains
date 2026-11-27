"""Versioned analysis reports linked to the immutable line of a saved game.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

from dataclasses import asdict
import json

from ..chess import ChessGame, Color, GameStatus, Move, to_fen
from .analysis import (
    MAX_MOVETIME_MS, MAX_PLIES, MAX_PV_PLIES, MAX_VARIANTS, AnalysisConfiguration, AnalysisLine, AnalysisProgress,
    AnalysisResult, Evaluation, EvaluationKind, JobStatus, ScoreBound, _valid_line,
)

REPORT_SCHEMA = 1
MAX_REPORT_BYTES = 4 * 1024 * 1024


def encode_report(progress: AnalysisProgress, source: ChessGame) -> str:
    if progress.status is not JobStatus.COMPLETED or progress.total != len(progress.results):
        raise ValueError("Only complete analysis reports can be saved.")
    rows = []
    for ply, result in enumerate(progress.results):
        if result.history != tuple(source.moves[:ply]) or result.initial_fen != to_fen(source.initial_state):
            raise ValueError("Analysis history differs from the saved game.")
        variants = []
        for line in result.lines:
            row = asdict(line)
            row["moves"] = [move.to_uci() for move in line.moves]
            variants.append(row)
        rows.append({
            "fen": result.fen, "configuration": asdict(result.configuration), "lines": variants,
            "best_move": result.best_move.to_uci() if result.best_move else None,
            "elapsed_ms": result.elapsed_ms, "outcome": result.outcome, "cached": result.cached,
        })
    text = json.dumps({"schema": REPORT_SCHEMA, "job_id": progress.job_id, "positions": rows},
                      ensure_ascii=True, separators=(",", ":"))
    decode_report(text, source)
    return text


def _nonnegative(value: int) -> int:
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise ValueError("Invalid analysis number.")
    return value


def _read_line(item: dict, game: ChessGame, variants: int) -> AnalysisLine:
    moves = item["moves"]
    if not isinstance(moves, list) or not 1 <= len(moves) <= MAX_PV_PLIES:
        raise ValueError("Invalid analysis variation length.")
    moves = tuple(Move.from_uci(move) for move in moves)
    with game.replay_record():
        if not _valid_line(game, moves):
            raise ValueError("Illegal move in saved analysis variation.")
    rank = _nonnegative(item["rank"])
    if not 1 <= rank <= variants:
        raise ValueError("Invalid analysis variation rank.")
    score = item["evaluation"]
    evaluation = None
    if score is not None:
        value = score["value"]
        if type(value) is not int or abs(value) > 2**31 - 1 or score["perspective"] != Color.WHITE:
            raise ValueError("Invalid saved analysis score.")
        evaluation = Evaluation(EvaluationKind(score["kind"]), value, ScoreBound(score["bound"]))
    metrics = [None if item[key] is None else _nonnegative(item[key])
               for key in ("depth", "selective_depth", "nodes", "nodes_per_second", "time_ms")]
    return AnalysisLine(rank, moves, evaluation, *metrics)


def _read_configuration(data: dict) -> AnalysisConfiguration:
    values = dict(data)
    for key in ("engine_id", "engine_name", "engine_source"):
        if not isinstance(values[key], str) or not 1 <= len(values[key]) <= 1024:
            raise ValueError("Invalid engine metadata.")
    version = values["engine_version"]
    if version is not None and (not isinstance(version, str) or len(version) > 1024):
        raise ValueError("Invalid engine version.")
    for key in ("movetime_ms", "multipv", "requested_multipv"):
        _nonnegative(values[key])
    if (not 1 <= values["requested_multipv"] <= MAX_VARIANTS
            or values["multipv"] > values["requested_multipv"]
            or not 1 <= values["movetime_ms"] <= MAX_MOVETIME_MS):
        raise ValueError("Invalid saved analysis configuration.")
    if type(values["is_mock"]) is not bool or not isinstance(values["options"], list):
        raise ValueError("Invalid saved engine options.")
    options = []
    for name, value in values["options"]:
        if not isinstance(name, str) or not 1 <= len(name) <= 128:
            raise ValueError("Invalid saved option name.")
        options.append((name, _nonnegative(value)))
    values["options"] = tuple(options)
    return AnalysisConfiguration(**values)


def decode_report(text: str, source: ChessGame) -> AnalysisProgress:
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_REPORT_BYTES:
        raise ValueError("Analysis report exceeds its size limit.")
    try:
        data = json.loads(text)
        if type(data.get("schema")) is not int or data["schema"] != REPORT_SCHEMA:
            raise ValueError("Unsupported analysis report schema.")
        job_id, rows = data["job_id"], data["positions"]
        if not isinstance(job_id, str) or not 1 <= len(job_id) <= 128:
            raise ValueError("Invalid analysis run identifier.")
        if not isinstance(rows, list) or len(rows) != len(source.moves) + 1 or len(rows) > MAX_PLIES + 1:
            raise ValueError("Analysis report does not cover the saved game.")
        initial_fen = to_fen(source.initial_state)
        outcomes = {status.name.lower() for status in GameStatus}
        game = ChessGame(source.initial_state)
        results = []
        for ply, row in enumerate(rows):
            if ply:
                with game.replay_record():
                    game.play(source.moves[ply - 1])
            if row["fen"] != to_fen(game.state) or row["outcome"] not in outcomes:
                raise ValueError("Analysis position differs from the saved game.")
            configuration = _read_configuration(row["configuration"])
            variants = row["lines"]
            if (not isinstance(variants, list) or len(variants) > configuration.multipv
                    or (row["outcome"] != "active" and variants)):
                raise ValueError("Invalid saved analysis variations.")
            lines = tuple(_read_line(item, game, configuration.multipv) for item in variants)
            if tuple(line.rank for line in lines) != tuple(sorted({line.rank for line in lines})):
                raise ValueError("Invalid saved analysis variation order.")
            best_move = Move.from_uci(row["best_move"]) if row["best_move"] is not None else None
            if best_move is not None and (row["outcome"] != "active" or best_move not in game.rules.legal_moves(game.state)):
                raise ValueError("Invalid best move in saved analysis.")
            if type(row["cached"]) is not bool:
                raise ValueError("Invalid saved analysis cache flag.")
            results.append(AnalysisResult(
                initial_fen, tuple(source.moves[:ply]), row["fen"], game.state.turn, configuration,
                lines, best_move, _nonnegative(row["elapsed_ms"]), row["outcome"], row["cached"],
            ))
        return AnalysisProgress(job_id, JobStatus.COMPLETED, len(results), tuple(results), None)
    except (KeyError, TypeError, AttributeError, RecursionError) as error:
        raise ValueError("Invalid saved analysis report.") from error
