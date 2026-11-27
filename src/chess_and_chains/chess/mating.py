"""Bounded proof of a specific side's ability to deliver checkmate.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

from collections.abc import Mapping
from enum import Enum, auto

from .dead_positions import closed_pawn_barrier
from .model import Color, GameState, PieceType
from .rules import RulesPort


class MatePossibility(Enum):
    POSSIBLE = auto()
    IMPOSSIBLE = auto()
    UNKNOWN = auto()


def prove_mate_possibility(
    state: GameState, side: Color, rules: RulesPort, repetitions: Mapping[tuple[object, ...], int],
    *, max_plies: int = 3, max_positions: int = 192,
) -> MatePossibility:
    """Look for a cooperative legal mate, or prove that every branch fails.

    Automatic move-count and repetition draws stop the witness search. When
    such a draw is the only obstruction, leave the physical mating question
    open. Exhausting the depth or position budget also leaves it open.
    """
    seen = dict(repetitions)
    remaining = max_positions
    # The built-in rules already validated each move in legal_moves().
    advance = getattr(rules, "_apply_unchecked", rules.apply)

    def visit(position: GameState, repeat_count: int, depth: int) -> MatePossibility:
        nonlocal remaining
        if remaining <= 0:
            return MatePossibility.UNKNOWN
        remaining -= 1

        if not any(piece is not None and piece.color is side and piece.kind is not PieceType.KING
                   for piece in position.board):
            return MatePossibility.IMPOSSIBLE
        legal = rules.legal_moves(position)
        if not legal:
            if position.turn is side.opposite and rules.is_in_check(position):
                return MatePossibility.POSSIBLE
            return MatePossibility.IMPOSSIBLE
        if rules.insufficient_material(position) or closed_pawn_barrier(position):
            return MatePossibility.IMPOSSIBLE
        if depth <= 0 or repeat_count >= 5 or position.halfmove_clock >= 150:
            return MatePossibility.UNKNOWN

        result = MatePossibility.IMPOSSIBLE
        for move in legal:
            if remaining <= 0:
                return MatePossibility.UNKNOWN
            child = advance(position, move)
            key = rules.position_key(child)
            previous = seen.get(key, 0)
            seen[key] = previous + 1
            branch = visit(child, previous + 1, depth - 1)
            if previous:
                seen[key] = previous
            else:
                del seen[key]
            if branch is MatePossibility.POSSIBLE:
                return branch
            if branch is MatePossibility.UNKNOWN:
                result = branch
        return result

    return visit(state, seen.get(rules.position_key(state), 1), max_plies)
