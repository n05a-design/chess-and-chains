"""Monotonic Fischer clock for local games.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic_ns

from ..chess import Color


@dataclass(frozen=True, slots=True)
class TimeControl:
    initial_ms: int
    increment_ms: int = 0

    def __post_init__(self) -> None:
        if type(self.initial_ms) is not int or self.initial_ms <= 0:
            raise ValueError("Initial time must be a positive integer in milliseconds.")
        if type(self.increment_ms) is not int or self.increment_ms < 0:
            raise ValueError("Increment must be a non-negative integer in milliseconds.")


@dataclass(frozen=True, slots=True)
class ClockReading:
    white_ns: int
    black_ns: int
    turn: Color

    def __post_init__(self) -> None:
        if not isinstance(self.turn, Color) or any(type(value) is not int or value < 0
                                                   for value in (self.white_ns, self.black_ns)):
            raise ValueError("Invalid clock reading.")

    def remaining_ns(self, color: Color) -> int:
        return self.white_ns if color is Color.WHITE else self.black_ns

    def remaining_ms(self, color: Color) -> int:
        # A positive fraction of a millisecond is still playable time.
        return (self.remaining_ns(color) + 999_999) // 1_000_000


@dataclass(frozen=True, slots=True)
class ClockTimeline:
    current: ClockReading
    positions: tuple[ClockReading, ...]
    active_ns: int | None = None

    def move_annotations(self, plies: int) -> tuple[int, ...]:
        """PGN holds the remaining time of the player who just moved."""
        return tuple(after.remaining_ms(before.turn) for before, after
                     in zip(self.positions[:plies], self.positions[1:plies + 1]))


class GameClock:
    """Keep elapsed time independent of rendering, persistence, and move validation.

    Callers sample once at the point when a move is accepted. At exactly zero
    the flag wins. Illegal moves leave the active clock running.
    """

    def __init__(self, control: TimeControl, turn: Color, *, now: Callable[[], int] = monotonic_ns) -> None:
        self.control = control
        self._now = now
        initial_ns = control.initial_ms * 1_000_000
        self._reading = ClockReading(initial_ns, initial_ns, turn)
        self._started_at: int | None = None
        self._active_ns: int | None = 0

    @property
    def running(self) -> bool:
        return self._started_at is not None

    def sample_time(self) -> int:
        return self._now()

    def reading(self, at_ns: int | None = None) -> ClockReading:
        if self._started_at is None:
            return self._reading
        at_ns = self.sample_time() if at_ns is None else at_ns
        turn = self._reading.turn
        elapsed = max(0, at_ns - self._started_at)
        return self._with_time(turn, max(0, self._reading.remaining_ns(turn) - elapsed), turn)

    def active_time(self, at_ns: int | None = None) -> int | None:
        if self._active_ns is None:
            return None
        turn = self._reading.turn
        return self._active_ns + self._reading.remaining_ns(turn) - self.reading(at_ns).remaining_ns(turn)

    def restore_timeline(self, timeline: ClockTimeline) -> None:
        self.restore_paused(timeline.current)
        self._active_ns = timeline.active_ns

    def restore_paused(self, reading: ClockReading) -> None:
        self.pause()
        self._reading = reading

    def resume(self, at_ns: int | None = None) -> None:
        if not self.running and self._reading.remaining_ns(self._reading.turn) > 0:
            self._started_at = self.sample_time() if at_ns is None else at_ns

    def pause(self, at_ns: int | None = None) -> ClockReading:
        at_ns = self.sample_time() if at_ns is None else at_ns
        self._active_ns = self.active_time(at_ns)
        self._reading = self.reading(at_ns)
        self._started_at = None
        return self._reading

    def complete_move(self, at_ns: int) -> bool:
        """Commit the active side's time and switch turns at a sampled instant."""
        if not self.running:
            raise ValueError("The clock is paused.")
        self._active_ns = self.active_time(at_ns)
        self._reading = self.reading(at_ns)
        turn = self._reading.turn
        remaining = self._reading.remaining_ns(turn)
        if remaining == 0:
            self._started_at = None
            return False
        remaining += self.control.increment_ms * 1_000_000
        self._reading = self._with_time(turn, remaining, turn.opposite)
        self._started_at = at_ns
        return True

    def _with_time(self, color: Color, remaining_ns: int, turn: Color) -> ClockReading:
        if color is Color.WHITE:
            return ClockReading(remaining_ns, self._reading.black_ns, turn)
        return ClockReading(self._reading.white_ns, remaining_ns, turn)
