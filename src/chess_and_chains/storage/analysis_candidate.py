"""Portable, self-contained training positions derived from archived analysis.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json

from ..chess import ChessGame, Move, parse_fen, to_fen
from ..engines.analysis import AnalysisProgress, AnalysisResult, MAX_PLIES, critical_moments
from ..engines.analysis_report import decode_position, encode_position

CANDIDATE_SCHEMA = 1
MAX_CANDIDATE_BYTES = 256 * 1024
_CATEGORIES = {"mistake", "blunder", "missed-mate", "allowed-mate", "defended-mate", "mate-distance"}


class CandidateStatus(StrEnum):
    UNCHECKED = "unchecked"
    LEGAL_POSITION = "legal-position"
    FREE_PRACTICE = "free-practice"
    VALIDATED_EXERCISE = "validated-exercise"
    PERSONAL_PUZZLE = "personal-puzzle"


@dataclass(frozen=True, slots=True)
class AnalysisTrainingCandidate:
    candidate_id: str
    source_game_id: int
    report_id: str
    played_move: Move
    category: str
    result: AnalysisResult
    profile_id: str = "local"
    status: CandidateStatus = CandidateStatus.LEGAL_POSITION

    @property
    def ply(self) -> int:
        return len(self.result.history)

    @property
    def fen(self) -> str:
        return self.result.fen

    @property
    def content_id(self) -> str:
        variations = [[move.to_uci() for move in line.moves] for line in self.result.lines]
        best = self.result.best_move
        identity = [
            self.result.initial_fen, [move.to_uci() for move in self.result.history],
            self.played_move.to_uci(), best.to_uci() if best else None, sorted(variations),
        ]
        return hashlib.sha256(json.dumps(identity, separators=(",", ":")).encode("ascii")).hexdigest()

    def encode(self) -> str:
        data = {
            "schema": CANDIDATE_SCHEMA, "id": self.candidate_id, "profile": self.profile_id,
            "game_id": self.source_game_id, "report_id": self.report_id, "status": self.status,
            "kind": self.category, "played": self.played_move.to_uci(),
            "initial_fen": self.result.initial_fen, "history": [move.to_uci() for move in self.result.history],
            "position": encode_position(self.result),
        }
        return json.dumps(data, ensure_ascii=True, separators=(",", ":"))

    @classmethod
    def from_report(cls, game_id: int, report: AnalysisProgress, ply: int) -> AnalysisTrainingCandidate:
        moment = next((item for item in critical_moments(report.results) if item.ply - 1 == ply), None)
        if moment is None:
            raise ValueError("The analysis has no verified critical moment at this position.")
        result = report.results[ply]
        candidate = cls("", game_id, report.job_id, moment.played_move, moment.category, result)
        return cls(candidate.content_id, game_id, report.job_id, moment.played_move, moment.category, result)

    @classmethod
    def decode(cls, data: str) -> AnalysisTrainingCandidate:
        try:
            if not isinstance(data, str) or len(data.encode("utf-8")) > MAX_CANDIDATE_BYTES:
                raise ValueError("Training candidate exceeds its size limit.")
            raw = json.loads(data)
            if type(raw["schema"]) is not int or raw["schema"] != CANDIDATE_SCHEMA or raw["profile"] != "local":
                raise ValueError("Unsupported training candidate.")
            if (type(raw["game_id"]) is not int or raw["game_id"] < 1 or not isinstance(raw["report_id"], str)
                    or not 1 <= len(raw["report_id"]) <= 128 or raw["kind"] not in _CATEGORIES):
                raise ValueError("Invalid training provenance.")
            if not isinstance(raw["history"], list) or len(raw["history"]) > MAX_PLIES:
                raise ValueError("Invalid training history.")
            game = ChessGame(parse_fen(raw["initial_fen"]))
            if to_fen(game.initial_state) != raw["initial_fen"]:
                raise ValueError("Invalid canonical training FEN.")
            with game.replay_record():
                for move in raw["history"]:
                    game.play_uci(move)
            result = decode_position(raw["position"], game)
            played = Move.from_uci(raw["played"])
            if (played not in game.rules.legal_moves(game.state) or result.best_move is None
                    or played == result.best_move or not result.lines
                    or result.lines[0].moves[0] != result.best_move
                    or (result.comparison is not None and result.comparison[1].moves[0] != played)):
                raise ValueError("Training candidate cannot be reproduced from its position.")
            status = CandidateStatus(raw["status"])
            if status is not CandidateStatus.LEGAL_POSITION:
                raise ValueError("Unsupported candidate validation status.")
            candidate = cls(raw["id"], raw["game_id"], raw["report_id"], played, raw["kind"], result, status=status)
            if candidate.candidate_id != candidate.content_id:
                raise ValueError("Training candidate content identity differs.")
            return candidate
        except (TypeError, KeyError, AttributeError, RecursionError) as error:
            raise ValueError("Invalid training candidate data.") from error

