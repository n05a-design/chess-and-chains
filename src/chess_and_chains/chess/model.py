"""Typed value objects for the independent chess rules domain."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntFlag, auto

Square = int


class ChessError(ValueError):
    """Base class for invalid chess-domain input."""


class FenError(ChessError):
    """A FEN string is malformed or describes an impossible position."""


class PGNError(ChessError):
    """A PGN record cannot be parsed as a legal mainline."""


class IllegalMoveError(ChessError):
    """A move is malformed or illegal in the current position."""


class Color(str, Enum):
    WHITE = "w"
    BLACK = "b"

    @property
    def opposite(self) -> Color:
        return Color.BLACK if self is Color.WHITE else Color.WHITE


class PieceType(str, Enum):
    KING = "k"
    QUEEN = "q"
    ROOK = "r"
    BISHOP = "b"
    KNIGHT = "n"
    PAWN = "p"


class CastlingRights(IntFlag):
    NONE = 0
    WHITE_KINGSIDE = 1
    WHITE_QUEENSIDE = 2
    BLACK_KINGSIDE = 4
    BLACK_QUEENSIDE = 8


class GameStatus(Enum):
    ACTIVE = auto()
    CHECKMATE = auto()
    STALEMATE = auto()
    DRAW_INSUFFICIENT_MATERIAL = auto()
    DRAW_FIVEFOLD_REPETITION = auto()
    DRAW_SEVENTY_FIVE_MOVE = auto()
    DRAW_CLAIMED = auto()
    RESIGNED = auto()
    RECORDED_RESULT = auto()


class DrawClaim(Enum):
    THREEFOLD_REPETITION = auto()
    FIFTY_MOVE_RULE = auto()


@dataclass(frozen=True, slots=True)
class Piece:
    color: Color
    kind: PieceType

    def __post_init__(self) -> None:
        if not isinstance(self.color, Color) or not isinstance(self.kind, PieceType):
            raise ChessError("Pieces require a Color and PieceType value.")

    @property
    def fen_symbol(self) -> str:
        symbol = self.kind.value
        return symbol.upper() if self.color is Color.WHITE else symbol


@dataclass(frozen=True, slots=True)
class Move:
    from_square: Square
    to_square: Square
    promotion: PieceType | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.from_square, int)
            or isinstance(self.from_square, bool)
            or not isinstance(self.to_square, int)
            or isinstance(self.to_square, bool)
        ):
            raise IllegalMoveError("Square indices must be integers.")
        if not (0 <= self.from_square < 64 and 0 <= self.to_square < 64):
            raise IllegalMoveError("Square index must be between 0 and 63.")
        if self.from_square == self.to_square:
            raise IllegalMoveError("A move must change squares.")
        if self.promotion not in (None, PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT):
            raise IllegalMoveError("Promotion must be queen, rook, bishop, or knight.")

    @classmethod
    def from_uci(cls, text: str) -> Move:
        token = text.strip()
        if len(token) not in (4, 5):
            raise IllegalMoveError(f"Invalid UCI move: {text!r}")
        promotion = None
        if len(token) == 5:
            try:
                promotion = PieceType(token[4].lower())
            except ValueError as exc:
                raise IllegalMoveError(f"Invalid UCI promotion: {text!r}") from exc
        try:
            return cls(parse_square(token[:2]), parse_square(token[2:4]), promotion)
        except ChessError as exc:
            raise IllegalMoveError(f"Invalid UCI move: {text!r}") from exc

    def to_uci(self) -> str:
        suffix = self.promotion.value if self.promotion is not None else ""
        return f"{square_name(self.from_square)}{square_name(self.to_square)}{suffix}"


@dataclass(frozen=True, slots=True)
class GameState:
    board: tuple[Piece | None, ...]
    turn: Color
    castling_rights: CastlingRights = CastlingRights.NONE
    en_passant: Square | None = None
    halfmove_clock: int = 0
    fullmove_number: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.board, tuple):
            raise ChessError("GameState.board must be an immutable tuple.")
        if len(self.board) != 64:
            raise ChessError("A chess board must contain exactly 64 squares.")
        if any(piece is not None and not isinstance(piece, Piece) for piece in self.board):
            raise ChessError("Board squares must contain Piece values or None.")
        if not isinstance(self.turn, Color):
            raise ChessError("GameState.turn must be a Color.")
        if not isinstance(self.castling_rights, CastlingRights):
            raise ChessError("GameState.castling_rights must be CastlingRights.")
        if self.en_passant is not None and (
            not isinstance(self.en_passant, int) or isinstance(self.en_passant, bool)
        ):
            raise ChessError("En-passant square index must be an integer.")
        if (
            not isinstance(self.halfmove_clock, int)
            or isinstance(self.halfmove_clock, bool)
            or not isinstance(self.fullmove_number, int)
            or isinstance(self.fullmove_number, bool)
        ):
            raise ChessError("FEN counters must be integers.")
        if self.halfmove_clock < 0 or self.fullmove_number < 1:
            raise ChessError("FEN move counters are out of range.")
        if self.en_passant is not None and not 0 <= self.en_passant < 64:
            raise ChessError("En-passant square index must be between 0 and 63.")

    def piece_at(self, square: Square) -> Piece | None:
        return self.board[square]

    def king_square(self, color: Color) -> Square:
        for square, piece in enumerate(self.board):
            if piece == Piece(color, PieceType.KING):
                return square
        raise ChessError(f"Position has no {color.name.lower()} king.")


def parse_square(text: str) -> Square:
    if len(text) != 2 or text[0] not in "abcdefgh" or text[1] not in "12345678":
        raise ChessError(f"Invalid algebraic square: {text!r}")
    return (ord(text[1]) - ord("1")) * 8 + ord(text[0]) - ord("a")


def square_name(square: Square) -> str:
    if not 0 <= square < 64:
        raise ChessError(f"Invalid square index: {square}")
    return f"{chr(ord('a') + square % 8)}{square // 8 + 1}"


@dataclass(frozen=True, slots=True)
class MoveOutcome:
    status: GameStatus
    winner: Color | None = None
    in_check: bool = False
    claimable_draws: frozenset[DrawClaim] = frozenset()
    claimed_draw: DrawClaim | None = None
