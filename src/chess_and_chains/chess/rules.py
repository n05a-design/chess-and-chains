"""Legal move generation and immutable position transitions."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import Protocol

from .model import (
    CastlingRights,
    ChessError,
    Color,
    GameState,
    IllegalMoveError,
    Move,
    Piece,
    PieceType,
    Square,
)

INITIAL_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
PROMOTION_TYPES = (PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT)


class RulesPort(Protocol):
    def initial_state(self) -> GameState: ...

    def legal_moves(self, state: GameState) -> tuple[Move, ...]: ...

    def apply(self, state: GameState, move: Move) -> GameState: ...

    def is_in_check(self, state: GameState, color: Color | None = None) -> bool: ...

    def position_key(self, state: GameState) -> tuple[object, ...]: ...

    def insufficient_material(self, state: GameState) -> bool: ...

    def parse_fen(self, fen: str) -> GameState: ...

    def to_fen(self, state: GameState) -> str: ...


class ChessRules:
    """Self-contained chess rules implementation; no GUI, engine, or I/O imports."""

    def initial_state(self) -> GameState:
        return self.parse_fen(INITIAL_FEN)

    @staticmethod
    def parse_fen(fen: str) -> GameState:
        from .notation import parse_fen

        return parse_fen(fen)

    @staticmethod
    def to_fen(state: GameState) -> str:
        from .notation import to_fen

        return to_fen(state)

    def legal_moves(self, state: GameState) -> tuple[Move, ...]:
        legal: list[Move] = []
        for move in self._pseudo_moves(state):
            child = self._apply_unchecked(state, move)
            if not self.is_square_attacked(
                child.board, child.king_square(state.turn), state.turn.opposite
            ):
                legal.append(move)
        return tuple(legal)

    def apply(self, state: GameState, move: Move) -> GameState:
        if move not in self.legal_moves(state):
            raise IllegalMoveError(f"Illegal move {move.to_uci()} in this position.")
        return self._apply_unchecked(state, move)

    def is_in_check(self, state: GameState, color: Color | None = None) -> bool:
        side = color or state.turn
        return self.is_square_attacked(state.board, state.king_square(side), side.opposite)

    @staticmethod
    def is_square_attacked(
        board: tuple[Piece | None, ...], target: Square, by_color: Color
    ) -> bool:
        target_file, target_rank = target % 8, target // 8
        for source, piece in enumerate(board):
            if piece is None or piece.color is not by_color:
                continue
            file_delta = target_file - source % 8
            rank_delta = target_rank - source // 8
            abs_file, abs_rank = abs(file_delta), abs(rank_delta)
            if piece.kind is PieceType.PAWN:
                direction = 1 if by_color is Color.WHITE else -1
                if abs_file == 1 and rank_delta == direction:
                    return True
            elif piece.kind is PieceType.KNIGHT:
                if (abs_file, abs_rank) in ((1, 2), (2, 1)):
                    return True
            elif piece.kind is PieceType.KING:
                if max(abs_file, abs_rank) == 1:
                    return True
            elif piece.kind in (PieceType.BISHOP, PieceType.ROOK, PieceType.QUEEN):
                diagonal = abs_file == abs_rank and abs_file > 0
                straight = (file_delta == 0) != (rank_delta == 0)
                if piece.kind is PieceType.BISHOP and not diagonal:
                    continue
                if piece.kind is PieceType.ROOK and not straight:
                    continue
                if piece.kind is PieceType.QUEEN and not (diagonal or straight):
                    continue
                step_file = (file_delta > 0) - (file_delta < 0)
                step_rank = (rank_delta > 0) - (rank_delta < 0)
                file_pos, rank_pos = source % 8 + step_file, source // 8 + step_rank
                blocked = False
                while (file_pos, rank_pos) != (target_file, target_rank):
                    if board[rank_pos * 8 + file_pos] is not None:
                        blocked = True
                        break
                    file_pos += step_file
                    rank_pos += step_rank
                if not blocked:
                    return True
        return False

    def position_key(self, state: GameState) -> tuple[object, ...]:
        ep = state.en_passant
        if ep is not None and not any(
            move.to_square == ep
            and state.board[move.from_square] is not None
            and state.board[move.from_square].kind is PieceType.PAWN
            for move in self.legal_moves(state)
        ):
            ep = None
        return state.board, state.turn, state.castling_rights, ep

    @staticmethod
    def insufficient_material(state: GameState) -> bool:
        material = [
            (square, piece)
            for square, piece in enumerate(state.board)
            if piece is not None and piece.kind is not PieceType.KING
        ]
        if not material:
            return True
        if any(piece.kind in (PieceType.PAWN, PieceType.ROOK, PieceType.QUEEN) for _, piece in material):
            return False
        knights = [(square, piece) for square, piece in material if piece.kind is PieceType.KNIGHT]
        bishops = [(square, piece) for square, piece in material if piece.kind is PieceType.BISHOP]
        if len(material) == 1:
            return True
        if not knights:
            return len({(square % 8 + square // 8) % 2 for square, _ in bishops}) <= 1
        return False

    def perft(self, state: GameState, depth: int) -> int:
        if depth < 0:
            raise ValueError("Perft depth cannot be negative.")
        if depth == 0:
            return 1
        total = 0
        for move in self.legal_moves(state):
            child = self._apply_unchecked(state, move)
            total += self.perft(child, depth - 1)
        return total

    def _pseudo_moves(self, state: GameState) -> tuple[Move, ...]:
        moves: list[Move] = []
        for source, piece in enumerate(state.board):
            if piece is None or piece.color is not state.turn:
                continue
            file_pos, rank_pos = source % 8, source // 8
            if piece.kind is PieceType.PAWN:
                direction = 1 if piece.color is Color.WHITE else -1
                start_rank = 1 if piece.color is Color.WHITE else 6
                promotion_rank = 7 if piece.color is Color.WHITE else 0
                one_rank = rank_pos + direction
                if 0 <= one_rank < 8:
                    one = one_rank * 8 + file_pos
                    if state.board[one] is None:
                        self._append_pawn_move(moves, source, one, promotion_rank)
                        two_rank = rank_pos + 2 * direction
                        two = two_rank * 8 + file_pos
                        if rank_pos == start_rank and state.board[two] is None:
                            moves.append(Move(source, two))
                    for target_file in (file_pos - 1, file_pos + 1):
                        if not 0 <= target_file < 8:
                            continue
                        target = one_rank * 8 + target_file
                        victim = state.board[target]
                        if victim is not None and victim.color is piece.color.opposite and victim.kind is not PieceType.KING:
                            self._append_pawn_move(moves, source, target, promotion_rank)
                        elif target == state.en_passant:
                            moves.append(Move(source, target))
            elif piece.kind is PieceType.KNIGHT:
                for df, dr in ((1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)):
                    self._append_step(moves, state, source, file_pos + df, rank_pos + dr)
            elif piece.kind in (PieceType.BISHOP, PieceType.ROOK, PieceType.QUEEN):
                directions: tuple[tuple[int, int], ...]
                if piece.kind is PieceType.BISHOP:
                    directions = ((1, 1), (-1, 1), (1, -1), (-1, -1))
                elif piece.kind is PieceType.ROOK:
                    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
                else:
                    directions = (
                        (1, 1), (-1, 1), (1, -1), (-1, -1),
                        (1, 0), (-1, 0), (0, 1), (0, -1),
                    )
                for df, dr in directions:
                    target_file, target_rank = file_pos + df, rank_pos + dr
                    while 0 <= target_file < 8 and 0 <= target_rank < 8:
                        target = target_rank * 8 + target_file
                        target_piece = state.board[target]
                        if target_piece is None:
                            moves.append(Move(source, target))
                        else:
                            if target_piece.color is piece.color.opposite and target_piece.kind is not PieceType.KING:
                                moves.append(Move(source, target))
                            break
                        target_file += df
                        target_rank += dr
            else:
                for df in (-1, 0, 1):
                    for dr in (-1, 0, 1):
                        if df or dr:
                            self._append_step(moves, state, source, file_pos + df, rank_pos + dr)
                moves.extend(self._castling_moves(state, source))
        return tuple(moves)

    @staticmethod
    def _append_pawn_move(
        moves: list[Move], source: Square, target: Square, promotion_rank: int
    ) -> None:
        if target // 8 == promotion_rank:
            moves.extend(Move(source, target, promotion) for promotion in PROMOTION_TYPES)
        else:
            moves.append(Move(source, target))

    @staticmethod
    def _append_step(
        moves: list[Move],
        state: GameState,
        source: Square,
        target_file: int,
        target_rank: int,
    ) -> None:
        if not (0 <= target_file < 8 and 0 <= target_rank < 8):
            return
        target = target_rank * 8 + target_file
        piece = state.board[target]
        moving = state.board[source]
        if moving is not None and (
            piece is None or (piece.color is moving.color.opposite and piece.kind is not PieceType.KING)
        ):
            moves.append(Move(source, target))

    def _castling_moves(self, state: GameState, source: Square | None = None) -> tuple[Move, ...]:
        color = state.turn
        king_start = 4 if color is Color.WHITE else 60
        if source is not None and source != king_start:
            return ()
        king = state.board[king_start]
        if king != Piece(color, PieceType.KING):
            return ()
        opponent = color.opposite
        rank_base = 0 if color is Color.WHITE else 56
        candidates: list[Move] = []
        rights = (
            (CastlingRights.WHITE_KINGSIDE, CastlingRights.BLACK_KINGSIDE, 7, (5, 6), (5, 6)),
            (CastlingRights.WHITE_QUEENSIDE, CastlingRights.BLACK_QUEENSIDE, 0, (1, 2, 3), (3, 2)),
        )
        for white_right, black_right, rook_file, empty_files, safe_files in rights:
            right = white_right if color is Color.WHITE else black_right
            rook = state.board[rank_base + rook_file]
            if not state.castling_rights & right or rook != Piece(color, PieceType.ROOK):
                continue
            if any(state.board[rank_base + file_pos] is not None for file_pos in empty_files):
                continue
            if self.is_square_attacked(state.board, king_start, opponent):
                continue
            if any(self.is_square_attacked(state.board, rank_base + file_pos, opponent) for file_pos in safe_files):
                continue
            target_file = 6 if rook_file == 7 else 2
            candidates.append(Move(king_start, rank_base + target_file))
        return tuple(candidates)

    @staticmethod
    def _apply_unchecked(state: GameState, move: Move) -> GameState:
        board = list(state.board)
        moving = board[move.from_square]
        if moving is None:
            raise IllegalMoveError(f"No piece on {move.from_square}.")
        captured = board[move.to_square]
        board[move.from_square] = None
        is_en_passant = (
            moving.kind is PieceType.PAWN
            and move.to_square == state.en_passant
            and captured is None
            and move.from_square % 8 != move.to_square % 8
        )
        if is_en_passant:
            capture_square = move.to_square - 8 if moving.color is Color.WHITE else move.to_square + 8
            captured = board[capture_square]
            board[capture_square] = None
        placed = Piece(moving.color, move.promotion) if move.promotion is not None else moving
        board[move.to_square] = placed

        rights = state.castling_rights
        if moving.kind is PieceType.KING:
            rights &= ~(
                CastlingRights.WHITE_KINGSIDE | CastlingRights.WHITE_QUEENSIDE
                if moving.color is Color.WHITE
                else CastlingRights.BLACK_KINGSIDE | CastlingRights.BLACK_QUEENSIDE
            )
            if abs(move.to_square - move.from_square) == 2:
                rank_base = 0 if moving.color is Color.WHITE else 56
                if move.to_square % 8 == 6:
                    rook_from, rook_to = rank_base + 7, rank_base + 5
                else:
                    rook_from, rook_to = rank_base, rank_base + 3
                board[rook_to] = board[rook_from]
                board[rook_from] = None
        for square, right in (
            (0, CastlingRights.WHITE_QUEENSIDE),
            (7, CastlingRights.WHITE_KINGSIDE),
            (56, CastlingRights.BLACK_QUEENSIDE),
            (63, CastlingRights.BLACK_KINGSIDE),
        ):
            if move.from_square == square or move.to_square == square:
                rights &= ~right

        en_passant = None
        if moving.kind is PieceType.PAWN and abs(move.to_square - move.from_square) == 16:
            en_passant = (move.from_square + move.to_square) // 2
        halfmove_clock = (
            0 if moving.kind is PieceType.PAWN or captured is not None else state.halfmove_clock + 1
        )
        return GameState(
            tuple(board),
            state.turn.opposite,
            rights,
            en_passant,
            halfmove_clock,
            state.fullmove_number + (state.turn is Color.BLACK),
        )
