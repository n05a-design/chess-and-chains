"""Pure domain material calculations and captured piece tracking."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .model import Color, GameState, Move, Piece, PieceType

PIECE_MATERIAL_VALUES: dict[PieceType, int] = {
    PieceType.PAWN: 1,
    PieceType.KNIGHT: 3,
    PieceType.BISHOP: 3,
    PieceType.ROOK: 5,
    PieceType.QUEEN: 9,
}

MATERIAL_SORT_ORDER: tuple[PieceType, ...] = (
    PieceType.PAWN,
    PieceType.KNIGHT,
    PieceType.BISHOP,
    PieceType.ROOK,
    PieceType.QUEEN,
)


@dataclass(frozen=True, slots=True)
class CapturedGroup:
    """Group of captured pieces of the same kind, with original piece color preserved."""

    piece: Piece
    count: int


@dataclass(frozen=True, slots=True)
class PlayerMaterial:
    """Captured pieces and material score for one player side."""

    color: Color
    captures: tuple[Piece, ...]
    groups: tuple[CapturedGroup, ...]
    score: int
    advantage: int | None  # +N if this player has advantage; None if equal or trailing


@dataclass(frozen=True, slots=True)
class CapturedMaterial:
    """Complete captured piece and material difference snapshot."""

    white: PlayerMaterial
    black: PlayerMaterial
    difference: int  # white.score - black.score

    def for_color(self, color: Color) -> PlayerMaterial:
        return self.white if color is Color.WHITE else self.black

    @property
    def white_score(self) -> int:
        return self.white.score

    @property
    def black_score(self) -> int:
        return self.black.score

    @property
    def white_advantage(self) -> int | None:
        return self.white.advantage

    @property
    def black_advantage(self) -> int | None:
        return self.black.advantage


def calculate_captured_material(
    positions: Sequence[GameState],
    moves: Sequence[Move],
) -> CapturedMaterial:
    """Calculate captured pieces and material advantage from a timeline.

    Args:
        positions: Sequence of positions, starting with the initial board state.
            Must contain at least 1 position.
        moves: Sequence of moves played between the positions.
            len(moves) must be at least len(positions) - 1.

    Returns:
        CapturedMaterial containing captures, grouped counts, score, and advantage.
    """
    if not positions:
        raise ValueError("calculate_captured_material requires at least one position.")

    white_captures: list[Piece] = []
    black_captures: list[Piece] = []

    for move, before in zip(moves, positions[:-1], strict=False):
        capturing_color = before.turn
        captured_color = capturing_color.opposite

        captured_piece: Piece | None = None
        target_square = move.to_square

        # Normal capture (including capture with promotion, or capture of previously promoted piece)
        if before.board[target_square] is not None:
            captured_piece = before.board[target_square]
        # En passant capture
        elif (
            before.board[move.from_square] is not None
            and before.board[move.from_square].kind is PieceType.PAWN
            and before.en_passant is not None
            and target_square == before.en_passant
        ):
            captured_piece = Piece(captured_color, PieceType.PAWN)

        if captured_piece is not None:
            if capturing_color is Color.WHITE:
                white_captures.append(captured_piece)
            else:
                black_captures.append(captured_piece)

    white_score = sum(PIECE_MATERIAL_VALUES.get(p.kind, 0) for p in white_captures)
    black_score = sum(PIECE_MATERIAL_VALUES.get(p.kind, 0) for p in black_captures)
    difference = white_score - black_score

    white_advantage = difference if difference > 0 else None
    black_advantage = abs(difference) if difference < 0 else None

    def make_groups(captures: list[Piece], opp_color: Color) -> tuple[CapturedGroup, ...]:
        groups: list[CapturedGroup] = []
        for kind in MATERIAL_SORT_ORDER:
            count = sum(1 for p in captures if p.kind is kind)
            if count > 0:
                groups.append(CapturedGroup(Piece(opp_color, kind), count))
        return tuple(groups)

    white_groups = make_groups(white_captures, Color.BLACK)
    black_groups = make_groups(black_captures, Color.WHITE)

    white_mat = PlayerMaterial(
        color=Color.WHITE,
        captures=tuple(white_captures),
        groups=white_groups,
        score=white_score,
        advantage=white_advantage,
    )
    black_mat = PlayerMaterial(
        color=Color.BLACK,
        captures=tuple(black_captures),
        groups=black_groups,
        score=black_score,
        advantage=black_advantage,
    )

    return CapturedMaterial(
        white=white_mat,
        black=black_mat,
        difference=difference,
    )
