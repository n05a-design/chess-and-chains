"""Puzzle solving flow, independent of any GUI toolkit.

1. ``PuzzleSession(puzzle)`` applies the opponent's setup move.
2. ``submit(move)`` checks legality via the rules domain, then the solution.
3. Correct non-final moves trigger the scripted opponent reply.
4. On the final player move, any checkmating move is accepted as an
   equivalent alternative (the only alternative we can validate reliably).
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum

from ..chess import ChessGame, Color, GameState, GameStatus, IllegalMoveError, Move
from .model import Puzzle


class Verdict(str, Enum):
    CORRECT = "correct"      # continue; opponent replied
    SOLVED = "solved"
    WRONG = "wrong"          # legal but not the solution; position unchanged
    ILLEGAL = "illegal"


@dataclass(frozen=True, slots=True)
class Feedback:
    verdict: Verdict
    reply: Move | None = None
    alternative: bool = False


class PuzzleSession:
    def __init__(self, puzzle: Puzzle, *, clock=time.monotonic) -> None:
        self.puzzle = puzzle
        self._clock = clock
        self.game = ChessGame(puzzle.initial_state())
        self.game.play(puzzle.setup_move)
        self._index = 0  # index into puzzle.solution of the next player move
        self.mistakes = 0
        self.hints_used = 0
        self.revealed = False
        self.solved = False
        self._started = clock()
        self.duration_ms: int | None = None

    @property
    def player_color(self) -> Color:
        return self.puzzle.player_color

    @property
    def state(self) -> GameState:
        return self.game.state

    @property
    def finished(self) -> bool:
        return self.solved or self.revealed

    @property
    def last_move(self) -> Move | None:
        return self.game.moves[-1] if self.game.moves else None

    @property
    def expected_move(self) -> Move | None:
        if self.finished or self._index >= len(self.puzzle.solution):
            return None
        return self.puzzle.solution[self._index]

    def legal_moves(self) -> tuple[Move, ...]:
        if self.finished:
            return ()
        return self.game.rules.legal_moves(self.game.state)

    def submit(self, move: Move) -> Feedback:
        if self.finished:
            raise IllegalMoveError("The puzzle is already finished.")
        if move not in self.legal_moves():
            return Feedback(Verdict.ILLEGAL)
        expected = self.expected_move
        final = self._index == len(self.puzzle.solution) - 1
        alternative = False
        if move != expected:
            if final and self._mates(move):
                alternative = True
            else:
                self.mistakes += 1
                return Feedback(Verdict.WRONG)
        self.game.play(move)
        self._index += 1
        if self._index >= len(self.puzzle.solution):
            self.solved = True
            self.duration_ms = int((self._clock() - self._started) * 1000)
            return Feedback(Verdict.SOLVED, alternative=alternative)
        reply = self.puzzle.solution[self._index]
        self.game.play(reply)
        self._index += 1
        return Feedback(Verdict.CORRECT, reply=reply)

    def hint(self) -> int | None:
        """Return the source square of the expected move and count the hint."""
        expected = self.expected_move
        if expected is None:
            return None
        self.hints_used += 1
        return expected.from_square

    def reveal(self) -> tuple[Move, ...]:
        """Play out the remaining solution; the puzzle counts as not solved."""
        remaining = self.puzzle.solution[self._index:]
        for move in remaining:
            self.game.play(move)
        self._index = len(self.puzzle.solution)
        self.revealed = True
        self.duration_ms = int((self._clock() - self._started) * 1000)
        return remaining

    @property
    def clean_solve(self) -> bool:
        return self.solved and self.mistakes == 0 and self.hints_used == 0

    def _mates(self, move: Move) -> bool:
        rules = self.game.rules
        child = rules.apply(self.game.state, move)
        return rules.is_in_check(child) and not rules.legal_moves(child)


def is_game_over(session: PuzzleSession) -> bool:
    return session.game.outcome().status is not GameStatus.ACTIVE
