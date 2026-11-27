"""Independent, headless chess rules domain for Chess & Chains."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from .game import ChessGame
from .mating import MatePossibility
from .material import (
    CapturedGroup,
    CapturedMaterial,
    MATERIAL_SORT_ORDER,
    PIECE_MATERIAL_VALUES,
    PlayerMaterial,
    calculate_captured_material,
)
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
    "CapturedGroup",
    "CapturedMaterial",
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
    "MATERIAL_SORT_ORDER",
    "MatePossibility",
    "Move",
    "MoveOutcome",
    "PGNDocument",
    "PGNError",
    "Piece",
    "PIECE_MATERIAL_VALUES",
    "PieceType",
    "PlayerMaterial",
    "RulesPort",
    "Square",
    "calculate_captured_material",
    "export_pgn",
    "parse_fen",
    "parse_pgn",
    "parse_san",
    "parse_square",
    "square_name",
    "to_san",
    "to_fen",
]
