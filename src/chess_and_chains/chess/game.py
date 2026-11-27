"""Game history, undo/redo, and chess-game termination rules."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from .dead_positions import closed_pawn_barrier
from .mating import MatePossibility, prove_mate_possibility
from .material import CapturedMaterial, calculate_captured_material
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


_FORCED_DRAW_MAX_PLIES = 4


@dataclass(frozen=True, slots=True)
class _Termination:
    status: GameStatus
    winner: Color | None = None
    claim: DrawClaim | None = None
    declared_move: Move | None = None
    resigned_by: Color | None = None


@dataclass(frozen=True, slots=True)
class _HistoryEntry:
    before: GameState
    after: GameState
    move: Move | None = None
    position_key: tuple[object, ...] | None = None
    termination: _Termination | None = None


@dataclass(frozen=True, slots=True)
class GameTimeline:
    """Validated move line, optional final action, and current action index."""

    moves: tuple[Move, ...]
    cursor: int
    result: str | None = None
    resigned_by: Color | None = None
    claim: DrawClaim | None = None
    declared_move: Move | None = None
    agreed_draw: bool = False


class ChessGame:
    """A complete game timeline over a rules implementation."""

    def __init__(
        self,
        initial_state: GameState | None = None,
        *,
        rules: RulesPort | None = None,
        adjudicate_forced_capture_draws: bool = True,
    ) -> None:
        self.rules = rules if rules is not None else ChessRules()
        self.initial_state = initial_state if initial_state is not None else self.rules.initial_state()
        self.state = self.initial_state
        self.moves: list[Move] = []
        key = self.rules.position_key(self.state)
        self._repetitions: dict[tuple[object, ...], int] = {key: 1}
        self._termination: _Termination | None = None
        self._undo: list[_HistoryEntry] = []
        self._redo: list[_HistoryEntry] = []
        self._adjudicate_forced_draws = adjudicate_forced_capture_draws

    @contextmanager
    def replay_record(self) -> Iterator[None]:
        """Validate an existing timeline with the original automatic draw checks."""
        previous = self._adjudicate_forced_draws
        self._adjudicate_forced_draws = False
        try:
            yield
        finally:
            self._adjudicate_forced_draws = previous

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
        child = self.rules.apply(self.state, canonical)
        self._append(_HistoryEntry(self.state, child, canonical, self.rules.position_key(child)))
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
        self._finish(_Termination(GameStatus.DRAW_CLAIMED, claim=reason, declared_move=move))
        return self.outcome()

    def agree_draw(self) -> MoveOutcome:
        if self.outcome().status is not GameStatus.ACTIVE:
            raise ChessError("A draw cannot be agreed after the game has ended.")
        self._finish(_Termination(GameStatus.DRAW_AGREED))
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
        resigning = color or self.state.turn
        opponent = resigning.opposite
        has_piece_besides_king = any(
            piece is not None and piece.color is opponent and piece.kind is not PieceType.KING
            for piece in self.state.board
        )
        self._finish(_Termination(
            GameStatus.RESIGNED, winner=opponent if has_piece_besides_king else None, resigned_by=resigning,
        ))
        return self.outcome()

    def record_result(self, result: str, *, historical: bool = False) -> None:
        """Apply a validated result, preserving a historical win recorded before this draw check."""
        winners = {"1-0": Color.WHITE, "0-1": Color.BLACK, "1/2-1/2": None}
        if result == "*":
            return
        if result not in winners:
            raise ChessError(f"Invalid game result: {result!r}.")
        outcome = self.outcome()
        historical_win = (
            historical and outcome.status is GameStatus.DRAW_DEAD_POSITION and winners[result] is not None
        )
        if outcome.status is not GameStatus.ACTIVE and not historical_win:
            if winners[result] is not outcome.winner:
                raise ChessError("The declared result contradicts the game outcome.")
            return
        self._finish(_Termination(GameStatus.RECORDED_RESULT, winner=winners[result]))

    def outcome(self) -> MoveOutcome:
        if self._termination is not None:
            return MoveOutcome(
                self._termination.status,
                self._termination.winner,
                claimed_draw=self._termination.claim,
                declared_move=self._termination.declared_move,
                resigned_by=self._termination.resigned_by,
            )
        in_check = self.rules.is_in_check(self.state)
        legal = self.rules.legal_moves(self.state)
        if not legal:
            status = GameStatus.CHECKMATE if in_check else GameStatus.STALEMATE
            return MoveOutcome(status, self.state.turn.opposite if in_check else None, in_check)
        if self.rules.insufficient_material(self.state):
            return MoveOutcome(GameStatus.DRAW_INSUFFICIENT_MATERIAL, in_check=in_check)
        if self._adjudicate_forced_draws and (
            self._dead_after_forced_play(self.state, legal, _FORCED_DRAW_MAX_PLIES) or closed_pawn_barrier(self.state)
        ):
            return MoveOutcome(GameStatus.DRAW_DEAD_POSITION, in_check=in_check)
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

    def mate_possibility(self, side: Color) -> MatePossibility:
        """Conservatively decide whether a side could mate from the current position."""
        return prove_mate_possibility(self.state, side, self.rules, self._repetitions)

    def _dead_after_forced_play(self, state: GameState, legal: tuple[Move, ...], depth: int) -> bool:
        """Prove a draw in bounded forced lines or trees made only of mandatory captures."""
        if not legal:
            return not self.rules.is_in_check(state)
        if depth == 0:
            return False
        if len(legal) > 1 and any(state.board[move.to_square] is None for move in legal):
            return False
        for move in legal:
            child = self.rules.apply(state, move)
            if self.rules.insufficient_material(child):
                continue
            replies = self.rules.legal_moves(child)
            if not self._dead_after_forced_play(child, replies, depth - 1):
                return False
        return True

    def undo(self) -> GameState:
        if not self._undo:
            raise ChessError("There is no action to undo.")
        entry = self._undo.pop()
        self._redo.append(entry)
        self.state = entry.before
        self._termination = None
        if entry.position_key is not None:
            self.moves.pop()
            count = self._repetitions[entry.position_key] - 1
            if count:
                self._repetitions[entry.position_key] = count
            else:
                del self._repetitions[entry.position_key]
        return self.state

    def timeline(self) -> GameTimeline:
        history = (*self._undo, *reversed(self._redo))
        moves = tuple(entry.move for entry in history if entry.move is not None)
        end = history[-1].termination if history else None
        if end is None:
            return GameTimeline(moves, len(self._undo))
        result = {Color.WHITE: "1-0", Color.BLACK: "0-1", None: "1/2-1/2"}[end.winner]
        return GameTimeline(
            moves, len(self._undo), result, end.resigned_by, end.claim, end.declared_move,
            agreed_draw=end.status is GameStatus.DRAW_AGREED,
        )

    @classmethod
    def from_timeline(cls, initial_state: GameState, timeline: GameTimeline) -> ChessGame:
        game = cls(initial_state)
        with game.replay_record():
            for move in timeline.moves:
                game.play(move)
            if timeline.resigned_by is not None:
                game.resign(timeline.resigned_by)
            elif timeline.claim is not None:
                game.claim_draw(timeline.claim, timeline.declared_move)
            elif timeline.agreed_draw:
                game.agree_draw()
        if timeline.result is not None and game._termination is None:
            game.record_result(timeline.result, historical=True)
        action_count = len(game._undo)
        if not 0 <= timeline.cursor <= action_count:
            raise ChessError("Invalid game history cursor.")
        for _ in range(action_count - timeline.cursor):
            game.undo()
        if game.timeline() != timeline:
            raise ChessError("Game history does not match its recorded actions.")
        return game

    def played_positions(self) -> tuple[GameState, ...]:
        """Return the starting board and one immutable position per played move."""
        return (self.initial_state, *(entry.after for entry in self._undo if entry.move is not None))

    def captured_material(self) -> CapturedMaterial:
        """Return captured pieces and material difference for the active timeline."""
        return calculate_captured_material(self.played_positions(), tuple(self.moves))

    def redo(self) -> GameState:
        if not self._redo:
            raise ChessError("There is no action to redo.")
        self._apply_entry(self._redo.pop())
        return self.state

    def _finish(self, termination: _Termination) -> None:
        self._append(_HistoryEntry(self.state, self.state, termination=termination))

    def _append(self, entry: _HistoryEntry) -> None:
        self._apply_entry(entry)
        self._redo.clear()

    def _apply_entry(self, entry: _HistoryEntry) -> None:
        self.state = entry.after
        self._termination = entry.termination
        if entry.move is not None and entry.position_key is not None:
            self.moves.append(entry.move)
            self._repetitions[entry.position_key] = self._repetitions.get(entry.position_key, 0) + 1
        self._undo.append(entry)
