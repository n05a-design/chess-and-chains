"""Independent, headless chess rules domain for Chess & Chains."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from .game import ChessGame
from .model import (
    CastlingRights,
    ChessError,
    Color,
    DrawClaim,
    FenError,
    GameState,
    GameStatus,
    IllegalMoveError,
    Move,
    MoveOutcome,
    PGNError,
    Piece,
    PieceType,
    Square,
    parse_square,
    square_name,
)
from .notation import (
    PGNDocument,
    export_pgn,
    parse_fen,
    parse_pgn,
    parse_san,
    to_fen,
    to_san,
)
from .rules import ChessRules, INITIAL_FEN, RulesPort

__all__ = [
    "CastlingRights",
    "ChessError",
    "ChessGame",
    "ChessRules",
    "Color",
    "DrawClaim",
    "FenError",
    "GameState",
    "GameStatus",
    "IllegalMoveError",
    "INITIAL_FEN",
    "Move",
    "MoveOutcome",
    "PGNDocument",
    "PGNError",
    "Piece",
    "PieceType",
    "RulesPort",
    "Square",
    "export_pgn",
    "parse_fen",
    "parse_pgn",
    "parse_san",
    "parse_square",
    "square_name",
    "to_san",
    "to_fen",
]
