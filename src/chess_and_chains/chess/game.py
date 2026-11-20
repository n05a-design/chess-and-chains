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
        if move is None:
            available = self.outcome().claimable_draws
            valid = reason in available
        else:
            if move not in self.rules.legal_moves(self.state):
                raise IllegalMoveError(f"Illegal declared move {move.to_uci()}.")
            next_state = self.rules.apply(self.state, move)
            next_key = self.rules.position_key(next_state)
            if reason is DrawClaim.FIFTY_MOVE_RULE:
                valid = next_state.halfmove_clock >= 100
            else:
                valid = self._repetitions.get(next_key, 0) + 1 >= 3
            if valid:
                legal_after = self.rules.legal_moves(next_state)
                if not legal_after:
                    valid = False
        if not valid:
            raise ChessError(f"The {reason.name.lower().replace('_', ' ')} is not claimable.")
        self._push_undo()
        self._termination = _Termination(GameStatus.DRAW_CLAIMED, claim=reason)
        self._redo.clear()
        return self.outcome()

    def resign(self, color: Color | None = None) -> MoveOutcome:
        if self._termination is not None or self.outcome().status is not GameStatus.ACTIVE:
            raise ChessError("A resignation cannot end a game that has already ended.")
        resigning = color or self.state.turn
        self._push_undo()
        self._termination = _Termination(GameStatus.RESIGNED, winner=resigning.opposite)
        self._redo.clear()
        return self.outcome()

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
