"""Typed puzzle model following the Lichess puzzle CSV semantics.

Lichess semantics (verified against the published database description):
``FEN`` is the position *before* the opponent's move; the first UCI move in
``Moves`` is that opponent move and must be applied before the player is asked
to solve. The player then plays every other move starting with ``Moves[1]``.
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..chess import ChessRules, Color, GameState, Move, parse_fen

MIN_PUBLISHED_RATING = 1000


class ValidationStatus(str, Enum):
    VALID = "valid"
    UNVALIDATED = "unvalidated"


@dataclass(frozen=True, slots=True)
class Puzzle:
    puzzle_id: str
    fen: str
    setup_move: Move
    solution: tuple[Move, ...]
    rating: int
    rating_deviation: int
    popularity: int
    plays: int
    themes: tuple[str, ...]
    source: str
    game_url: str = ""
    opening_tags: tuple[str, ...] = ()
    validation: ValidationStatus = ValidationStatus.UNVALIDATED

    def initial_state(self) -> GameState:
        return parse_fen(self.fen)

    def start_state(self, rules: ChessRules | None = None) -> GameState:
        """Position presented to the player (after the opponent's setup move)."""
        chess_rules = rules or ChessRules()
        return chess_rules.apply(self.initial_state(), self.setup_move)

    @property
    def player_color(self) -> Color:
        return self.initial_state().turn.opposite

    def to_record(self) -> dict:
        return {
            "id": self.puzzle_id,
            "fen": self.fen,
            "moves": [self.setup_move.to_uci(), *(m.to_uci() for m in self.solution)],
            "rating": self.rating,
            "rating_deviation": self.rating_deviation,
            "popularity": self.popularity,
            "plays": self.plays,
            "themes": list(self.themes),
            "source": self.source,
            "game_url": self.game_url,
            "opening_tags": list(self.opening_tags),
        }

    @classmethod
    def from_record(cls, record: dict, validation: ValidationStatus = ValidationStatus.UNVALIDATED) -> Puzzle:
        moves = [Move.from_uci(text) for text in record["moves"]]
        return cls(
            puzzle_id=str(record["id"]),
            fen=str(record["fen"]),
            setup_move=moves[0],
            solution=tuple(moves[1:]),
            rating=int(record["rating"]),
            rating_deviation=int(record.get("rating_deviation", 0)),
            popularity=int(record.get("popularity", 0)),
            plays=int(record.get("plays", 0)),
            themes=tuple(record.get("themes", ())),
            source=str(record.get("source", "")),
            game_url=str(record.get("game_url", "")),
            opening_tags=tuple(record.get("opening_tags", ())),
            validation=validation,
        )
