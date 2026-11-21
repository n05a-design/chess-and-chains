"""Conservative proof for dead positions behind a closed pawn barrier."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from .model import Color, GameState, PieceType, Square


_KING_NEIGHBORS = tuple(
    tuple(rank * 8 + file
          for rank in range(max(0, square // 8 - 1), min(8, square // 8 + 2))
          for file in range(max(0, square % 8 - 1), min(8, square % 8 + 2))
          if rank * 8 + file != square)
    for square in range(64)
)


def _king_area(
    start: Square, own_pawns: set[Square], enemy_pawns: set[Square], pawn_attacks: set[Square],
) -> set[Square] | None:
    """Overestimate the king's reach by ignoring the other king."""
    if start in pawn_attacks:
        return None
    visited = {start}
    frontier = [start]
    while frontier:
        square = frontier.pop()
        for target in _KING_NEIGHBORS[square]:
            if target in visited or target in own_pawns or target in pawn_attacks:
                continue
            if target in enemy_pawns:
                return None  # The barrier might be opened by a king capture.
            visited.add(target)
            frontier.append(target)
    return visited


def closed_pawn_barrier(state: GameState) -> bool:
    """Prove that neither side can ever give check in this king-and-pawn position."""
    if state.en_passant is not None:
        return False
    pawns: dict[Color, set[Square]] = {Color.WHITE: set(), Color.BLACK: set()}
    for square, piece in enumerate(state.board):
        if piece is None or piece.kind is PieceType.KING:
            continue
        if piece.kind is not PieceType.PAWN:
            return False
        pawns[piece.color].add(square)
    if not pawns[Color.WHITE] or not pawns[Color.BLACK]:
        return False

    attacks: dict[Color, set[Square]] = {Color.WHITE: set(), Color.BLACK: set()}
    for color, step in ((Color.WHITE, 8), (Color.BLACK, -8)):
        enemies = pawns[color.opposite]
        for square in pawns[color]:
            front = square + step
            if front not in enemies:
                return False
            if square % 8 > 0:
                attacks[color].add(front - 1)
            if square % 8 < 7:
                attacks[color].add(front + 1)
        if attacks[color] & enemies:
            return False

    white = _king_area(state.king_square(Color.WHITE), pawns[Color.WHITE], pawns[Color.BLACK], attacks[Color.BLACK])
    if white is None:
        return False
    black = _king_area(state.king_square(Color.BLACK), pawns[Color.BLACK], pawns[Color.WHITE], attacks[Color.WHITE])
    if black is None or white & black:
        return False
    # The only remaining moves are king steps in these disjoint areas.
    # The pawn structure stays fixed, and the kings can never threaten each other.
    return not any(target in black for square in white for target in _KING_NEIGHBORS[square])
