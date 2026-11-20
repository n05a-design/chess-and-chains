"""Game history, undo/redo, and chess-game termination rules."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

from dataclasses import dataclass

from .model import (
    ChessError,
    Color,
    DrawClaim,
    GameState,
    GameStatus,
    IllegalMoveError,
    Move,
    MoveOutcome,
    PieceType,
)
from .rules import ChessRules, RulesPort


@dataclass(frozen=True, slots=True)
class _Termination:
    status: GameStatus
    winner: Color | None = None
    claim: DrawClaim | None = None


@dataclass(frozen=True, slots=True)
class _Snapshot:
    state: GameState
    moves: tuple[Move, ...]
    repetitions: tuple[tuple[tuple[object, ...], int], ...]
    termination: _Termination | None


class ChessGame:
    """A complete game timeline over a rules implementation."""

    def __init__(
        self,
        initial_state: GameState | None = None,
        *,
        rules: RulesPort | None = None,
    ) -> None:
        self.rules = rules if rules is not None else ChessRules()
        self.initial_state = initial_state if initial_state is not None else self.rules.initial_state()
        self.state = self.initial_state
        self.moves: list[Move] = []
        key = self.rules.position_key(self.state)
        self._repetitions: dict[tuple[object, ...], int] = {key: 1}
        self._termination: _Termination | None = None
        self._undo: list[_Snapshot] = []
        self._redo: list[_Snapshot] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def play(self, move: Move) -> GameState:
        if self._termination is not None or self.outcome().status is not GameStatus.ACTIVE:
            raise IllegalMoveError("The game has already ended.")
        legal = self.rules.legal_moves(self.state)
        canonical = next((candidate for candidate in legal if candidate == move), None)
        if canonical is None:
            raise IllegalMoveError(f"Illegal move {move.to_uci()} in this position.")
        self._push_undo()
        self.state = self.rules.apply(self.state, canonical)
        self.moves.append(canonical)
        key = self.rules.position_key(self.state)
        self._repetitions[key] = self._repetitions.get(key, 0) + 1
        self._redo.clear()
        return self.state

    def play_uci(self, text: str) -> GameState:
        move = Move.from_uci(text)
        return self.play(move)

    def claim_draw(self, reason: DrawClaim, move: Move | None = None) -> MoveOutcome:
        if self._termination is not None or self.outcome().status is not GameStatus.ACTIVE:
            raise ChessError("A draw cannot be claimed after the game has ended.")
        if move is not None and move not in self.rules.legal_moves(self.state):
            raise IllegalMoveError(f"Illegal declared move {move.to_uci()}.")
        valid = (reason, move) in self.draw_claim_options()
        if not valid:
            raise ChessError(f"The {reason.name.lower().replace('_', ' ')} is not claimable.")
        self._push_undo()
        self._termination = _Termination(GameStatus.DRAW_CLAIMED, claim=reason)
        self._redo.clear()
        return self.outcome()

    def draw_claim_options(self) -> tuple[tuple[DrawClaim, Move | None], ...]:
        """Claims in the current position or by declaring a specific legal move."""
        outcome = self.outcome()
        if outcome.status is not GameStatus.ACTIVE:
            return ()
        options: list[tuple[DrawClaim, Move | None]] = [
            (reason, None) for reason in DrawClaim if reason in outcome.claimable_draws
        ]
        fifty = self.state.halfmove_clock >= 99
        repetition = any(count >= 2 for count in self._repetitions.values())
        if fifty or repetition:
            for move in self.rules.legal_moves(self.state):
                child = self.rules.apply(self.state, move)
                if fifty and child.halfmove_clock >= 100:
                    options.append((DrawClaim.FIFTY_MOVE_RULE, move))
                if repetition and self._repetitions.get(self.rules.position_key(child), 0) >= 2:
                    options.append((DrawClaim.THREEFOLD_REPETITION, move))
        return tuple(options)

    def resign(self, color: Color | None = None) -> MoveOutcome:
        if self._termination is not None or self.outcome().status is not GameStatus.ACTIVE:
            raise ChessError("A resignation cannot end a game that has already ended.")
        opponent = (color or self.state.turn).opposite
        has_piece_besides_king = any(
            piece is not None and piece.color is opponent and piece.kind is not PieceType.KING
            for piece in self.state.board
        )
        self._push_undo()
        self._termination = _Termination(GameStatus.RESIGNED, winner=opponent if has_piece_besides_king else None)
        self._redo.clear()
        return self.outcome()

    def record_result(self, result: str) -> None:
        """Apply a result from a validated record when the board alone has no outcome."""
        winners = {"1-0": Color.WHITE, "0-1": Color.BLACK, "1/2-1/2": None}
        if result == "*":
            return
        if result not in winners:
            raise ChessError(f"Invalid game result: {result!r}.")
        outcome = self.outcome()
        if outcome.status is not GameStatus.ACTIVE:
            if winners[result] is not outcome.winner:
                raise ChessError("The declared result contradicts the game outcome.")
            return
        self._push_undo()
        self._termination = _Termination(GameStatus.RECORDED_RESULT, winner=winners[result])
        self._redo.clear()

    def outcome(self) -> MoveOutcome:
        if self._termination is not None:
            return MoveOutcome(
                self._termination.status,
                self._termination.winner,
                claimed_draw=self._termination.claim,
            )
        in_check = self.rules.is_in_check(self.state)
        legal = self.rules.legal_moves(self.state)
        if not legal:
            status = GameStatus.CHECKMATE if in_check else GameStatus.STALEMATE
            return MoveOutcome(status, self.state.turn.opposite if in_check else None, in_check)
        if self.rules.insufficient_material(self.state):
            return MoveOutcome(GameStatus.DRAW_INSUFFICIENT_MATERIAL, in_check=in_check)
        key = self.rules.position_key(self.state)
        repetitions = self._repetitions.get(key, 0)
        if self.state.halfmove_clock >= 150:
            return MoveOutcome(GameStatus.DRAW_SEVENTY_FIVE_MOVE, in_check=in_check)
        if repetitions >= 5:
            return MoveOutcome(GameStatus.DRAW_FIVEFOLD_REPETITION, in_check=in_check)
        claims: set[DrawClaim] = set()
        if self.state.halfmove_clock >= 100:
            claims.add(DrawClaim.FIFTY_MOVE_RULE)
        if repetitions >= 3:
            claims.add(DrawClaim.THREEFOLD_REPETITION)
        return MoveOutcome(GameStatus.ACTIVE, in_check=in_check, claimable_draws=frozenset(claims))

    def undo(self) -> GameState:
        if not self._undo:
            raise ChessError("There is no action to undo.")
        self._redo.append(self._snapshot())
        self._restore(self._undo.pop())
        return self.state

    def redo(self) -> GameState:
        if not self._redo:
            raise ChessError("There is no action to redo.")
        self._undo.append(self._snapshot())
        self._restore(self._redo.pop())
        return self.state

    def _push_undo(self) -> None:
        self._undo.append(self._snapshot())

    def _snapshot(self) -> _Snapshot:
        return _Snapshot(
            self.state,
            tuple(self.moves),
            tuple(self._repetitions.items()),
            self._termination,
        )

    def _restore(self, snapshot: _Snapshot) -> None:
        self.state = snapshot.state
        self.moves = list(snapshot.moves)
        self._repetitions = dict(snapshot.repetitions)
        self._termination = snapshot.termination
