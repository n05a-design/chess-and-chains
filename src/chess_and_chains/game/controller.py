"""UI-independent game controller with an asynchronous bot worker.

Threading contract
------------------
* Every public method except ``BotWorker`` internals must be called from one
  owner thread (the Tk main thread in the app).
* The worker thread receives game data and a cancellation signal and calls the
  provider; it never touches ``ChessGame``.
* Results are queued and applied by ``poll()`` on the owner thread. A result is
  discarded unless its generation id and ply still match the live game, and
  its move is legal according to the project's own rules domain.
* Any state change that invalidates a pending search (new game, undo, redo,
  mode change, shutdown) increments the generation id.
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import queue
import threading
from time import monotonic_ns
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from ..chess import (
    CapturedMaterial,
    ChessError,
    ChessGame,
    Color,
    DrawClaim,
    GameState,
    GameStatus,
    IllegalMoveError,
    Move,
    MoveOutcome,
    MatePossibility,
    parse_fen,
    to_fen,
    to_san,
)
from ..engines.bot import BotClock, BotRequest, MoveProvider
from .clock import ClockReading, ClockTimeline, GameClock, TimeControl


class PlayMode(str, Enum):
    HUMAN_VS_HUMAN = "human-vs-human"
    HUMAN_VS_BOT = "human-vs-bot"


@dataclass(frozen=True, slots=True)
class GameSetup:
    mode: PlayMode = PlayMode.HUMAN_VS_HUMAN
    bot_color: Color | None = None
    initial_fen: str | None = None
    time_control: TimeControl | None = None

    def __post_init__(self) -> None:
        if self.mode is PlayMode.HUMAN_VS_BOT and self.bot_color is None:
            raise ValueError("Bot mode requires bot_color.")
        if self.mode is PlayMode.HUMAN_VS_HUMAN and self.bot_color is not None:
            raise ValueError("Two-player mode cannot have a bot color.")

    @classmethod
    def two_players(cls) -> GameSetup:
        return cls()

    @classmethod
    def against_bot(cls, human: Color) -> GameSetup:
        return cls(PlayMode.HUMAN_VS_BOT, human.opposite)


class BotStatus(str, Enum):
    NONE = "none"
    IDLE = "idle"
    THINKING = "thinking"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class BotResult:
    generation: int
    ply: int
    move: Move | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class GameView:
    """Read-only snapshot for rendering."""

    state: GameState
    setup: GameSetup
    outcome: MoveOutcome
    legal_moves: tuple[Move, ...]
    last_move: Move | None
    san_moves: tuple[str, ...]
    bot_status: BotStatus
    bot_name: str | None
    bot_is_mock: bool
    bot_error: str | None
    can_undo: bool
    can_redo: bool
    human_to_move: bool
    generation: int
    captured_material: CapturedMaterial | None = None
    clock: ClockReading | None = None
    clock_running: bool = False
    flagged: Color | None = None


Listener = Callable[[GameView], None]


class BotWorker:
    """Single background thread executing provider searches."""

    def __init__(self, provider: MoveProvider) -> None:
        self.provider = provider
        self.results: queue.Queue[BotResult] = queue.Queue()
        self._requests: queue.Queue[BotRequest | None] = queue.Queue()
        self._thread = threading.Thread(target=self._run, name="bot-worker", daemon=True)
        self._thread.start()

    @property
    def alive(self) -> bool:
        return self._thread.is_alive()

    def submit(self, request: BotRequest) -> None:
        self._requests.put(request)

    def _run(self) -> None:
        while True:
            request = self._requests.get()
            if request is None:
                return
            if request.cancelled.is_set():
                continue
            try:
                move = self.provider.choose_move(request)
                result = BotResult(request.generation, request.ply, move=move)
            except Exception as error:  # noqa: BLE001 - every provider failure must reach the UI
                result = BotResult(request.generation, request.ply, error=f"{type(error).__name__}: {error}")
            self.results.put(result)

    def stop(self, timeout: float = 2.0) -> bool:
        """Stop the thread; returns True when it has terminated."""
        self.provider.cancel()
        self._requests.put(None)
        self._thread.join(timeout / 2)
        if self._thread.is_alive():
            self.provider.kill()
            self._thread.join(timeout / 2)
        self.provider.close()
        return not self._thread.is_alive()


class GameController:
    def __init__(self, provider: MoveProvider | None = None, *, now: Callable[[], int] = monotonic_ns) -> None:
        self._now = now
        self._clock: GameClock | None = None
        self._clock_positions: list[ClockReading] = []
        self._flagged: Color | None = None
        self._draw_offer: Color | None = None
        self._provider = provider
        self._worker: BotWorker | None = None
        self._listeners: list[Listener] = []
        self._generation = 0
        self._game_id = 0
        self._pending: BotRequest | None = None
        self._bot_error: str | None = None
        self._setup = GameSetup.two_players()
        self._game = ChessGame()
        self._initial_fen = to_fen(self._game.initial_state)
        self._san: list[str] = []
        self._san_moves: list[Move] = []
        self._closed = False

    # ----- observation -------------------------------------------------
    def subscribe(self, listener: Listener) -> Callable[[], None]:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    @property
    def game(self) -> ChessGame:
        return self._game

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def setup(self) -> GameSetup:
        return self._setup

    @property
    def provider(self) -> MoveProvider | None:
        return self._provider

    def view(self) -> GameView:
        outcome = self._game.outcome()
        active = outcome.status is GameStatus.ACTIVE
        human = self._human_to_move(outcome)
        legal = self._game.rules.legal_moves(self._game.state) if active and human else ()
        return GameView(
            state=self._game.state,
            setup=self._setup,
            outcome=outcome,
            legal_moves=legal,
            last_move=self._game.moves[-1] if self._game.moves else None,
            san_moves=tuple(self._sync_san()),
            bot_status=self.bot_status,
            bot_name=self._provider.display_name if self._provider else None,
            bot_is_mock=bool(self._provider and self._provider.is_mock),
            bot_error=self._bot_error,
            can_undo=self._can_undo(),
            can_redo=self._can_redo(),
            human_to_move=human,
            generation=self._generation,
            captured_material=self._game.captured_material(),
            clock=self._clock.reading() if self._clock else None,
            clock_running=bool(self._clock and self._clock.running),
            flagged=self._flagged,
        )

    @property
    def bot_status(self) -> BotStatus:
        if self._setup.mode is not PlayMode.HUMAN_VS_BOT:
            return BotStatus.NONE
        if self._bot_error:
            return BotStatus.ERROR
        return BotStatus.THINKING if self._pending else BotStatus.IDLE

    # ----- commands ----------------------------------------------------
    def new_game(self, setup: GameSetup | None = None) -> None:
        self._ensure_open()
        setup = setup or self._setup
        if setup.mode is PlayMode.HUMAN_VS_BOT and self._provider is None:
            raise ChessError("No bot provider is configured.")
        initial = parse_fen(setup.initial_fen) if setup.initial_fen else None
        self._replace_game(ChessGame(initial), setup)

    def load_game(self, game: ChessGame) -> None:
        """Open a validated record for local two-player play or review."""
        self._ensure_open()
        self._replace_game(game, GameSetup.two_players())

    def resume_game(
        self, game: ChessGame, setup: GameSetup, *, provider: MoveProvider | None = None,
        clock: ClockTimeline | None = None,
    ) -> None:
        """Resume a validated active game using its original setup."""
        self._ensure_open()
        if game.outcome().status is not GameStatus.ACTIVE:
            raise ChessError("A finished game cannot be resumed.")
        if setup.mode is PlayMode.HUMAN_VS_BOT and provider is None and self._provider is None:
            raise ChessError("No bot provider is configured.")
        if (setup.time_control is None) != (clock is None):
            raise ChessError("A restored timed game requires its saved clock.")
        self._replace_game(game, setup, provider=provider, clock=clock)

    def _replace_game(
        self, game: ChessGame, setup: GameSetup, *, provider: MoveProvider | None = None,
        clock: ClockTimeline | None = None,
    ) -> None:
        self._invalidate()
        if provider is not None and provider is not self._provider:
            if self._worker is None and self._provider is not None:
                self._provider.close()
            self._stop_worker()
            self._provider = provider
        self._game_id += 1
        self._setup = setup
        self._game = game
        self._clock = GameClock(setup.time_control, game.state.turn, now=self._now) if setup.time_control else None
        self._clock_positions.clear()
        self._flagged = None
        if self._clock is not None:
            if clock is None:
                self._clock_positions.append(self._clock.reading())
                if game.outcome().status is GameStatus.ACTIVE:
                    self._clock.resume()
            else:
                self._clock_positions.extend(clock.positions)
                self._clock.restore_timeline(clock)
                if clock.current.remaining_ns(clock.current.turn) == 0:
                    self._flagged = clock.current.turn
        self._initial_fen = to_fen(self._game.initial_state)
        self._san.clear()
        self._san_moves.clear()
        self._bot_error = None
        self._maybe_request_bot()
        self._notify()

    def set_provider(self, provider: MoveProvider | None) -> None:
        """Replace the bot; stops the old worker and its engine process."""
        self._invalidate()
        self._stop_worker()
        self._provider = provider
        self._bot_error = None
        if provider is None and self._setup.mode is PlayMode.HUMAN_VS_BOT:
            self._setup = GameSetup(time_control=self._setup.time_control)
        self._maybe_request_bot()
        self._notify()

    def play_human(self, move: Move) -> None:
        self._ensure_open()
        outcome = self._game.outcome()
        if not self._human_to_move(outcome):
            raise IllegalMoveError("It is not a human player's turn.")
        try:
            self._play_move(move)
        except ChessError:
            if self._flagged is not None:
                self._notify()
            raise
        self._maybe_request_bot()
        self._notify()

    def undo(self) -> None:
        """Undo one ply (two players) or back to the human's last decision (bot)."""
        self._ensure_open()
        if self._check_timeout():
            self._notify()
        if not self._can_undo():
            raise ChessError("There is no move to undo.")
        self._invalidate()
        self._bot_error = None
        self._game.undo()
        if self._clock is None and self._setup.mode is PlayMode.HUMAN_VS_BOT:
            while self._game.state.turn is self._setup.bot_color and self._game.moves:
                self._game.undo()
        self._restore_clock_after_edit()
        self._maybe_request_bot()
        self._notify()

    def redo(self) -> None:
        self._ensure_open()
        if self._check_timeout():
            self._notify()
        if not self._can_redo():
            raise ChessError("There is no move to redo.")
        self._invalidate()
        self._game.redo()
        if self._clock is None and self._setup.mode is PlayMode.HUMAN_VS_BOT:
            while self._game.state.turn is self._setup.bot_color and self._redo_available():
                self._game.redo()
        self._restore_clock_after_edit()
        self._maybe_request_bot()
        self._notify()

    def claim_draw(self, reason: DrawClaim, move: Move | None = None) -> None:
        self._ensure_open()
        if self._check_timeout():
            self._notify()
        if not self._human_to_move(self._game.outcome()):
            raise ChessError("Only the player to move may claim a draw.")
        self._game.claim_draw(reason, move)
        self._pause_clock()
        self._invalidate()
        self._notify()

    def offer_draw(self) -> Color:
        self._ensure_open()
        if self._check_timeout():
            self._notify()
        if self._setup.mode is not PlayMode.HUMAN_VS_HUMAN or not self._human_to_move(self._game.outcome()):
            raise ChessError("A draw can only be offered during an active two-player game.")
        if self._draw_offer is not None:
            raise ChessError("A draw offer already awaits a response.")
        self._draw_offer = self._game.state.turn
        return self._draw_offer

    def respond_to_draw(self, player: Color, *, accept: bool) -> None:
        self._ensure_open()
        if self._check_timeout():
            self._notify()
        if self._draw_offer is None or player is not self._draw_offer.opposite:
            raise ChessError("Only the other player may respond to a pending draw offer.")
        self._draw_offer = None
        if accept:
            self._game.agree_draw()
            self._pause_clock()
            self._invalidate()
            self._notify()

    def resign(self) -> None:
        self._ensure_open()
        if self._check_timeout():
            self._notify()
        self._invalidate()
        color = self._game.state.turn
        if self._setup.mode is PlayMode.HUMAN_VS_BOT:
            color = self._setup.bot_color.opposite  # type: ignore[union-attr]
        if self._flagged is not None:
            raise ChessError("The game is awaiting a timeout result.")
        self._game.resign(color)
        self._pause_clock()
        self._notify()

    def clock_reading(self) -> ClockReading | None:
        return self._clock.reading() if self._clock else None

    def pause_for_close(self) -> None:
        self._check_timeout()
        self._pause_clock()

    def clock_timeline(self) -> ClockTimeline | None:
        if self._clock is None:
            return None
        now = self._clock.sample_time()
        return ClockTimeline(self._clock.reading(now), tuple(self._clock_positions), self._clock.active_time(now))

    def toggle_clock(self) -> None:
        self._ensure_open()
        if self._clock is None or self._flagged is not None or self._game.outcome().status is not GameStatus.ACTIVE:
            return
        if not self._check_timeout():
            if self._clock.running:
                self._pause_clock()
                self._invalidate()
            else:
                self._clock.resume()
                self._maybe_request_bot()
        self._notify()

    def adjudicate_timeout(self, *, draw: bool) -> None:
        self._ensure_open()
        if self._flagged is None or self._game.outcome().status is not GameStatus.ACTIVE:
            raise ChessError("No timeout awaits a result.")
        result = "1/2-1/2" if draw else ("0-1" if self._flagged is Color.WHITE else "1-0")
        self._game.record_result(result)
        self._notify()

    def _pause_clock(self) -> None:
        if self._clock is not None:
            self._clock.pause()

    def _check_timeout(self, at_ns: int | None = None) -> bool:
        if self._clock is None or not self._clock.running:
            return False
        at_ns = self._clock.sample_time() if at_ns is None else at_ns
        reading = self._clock.reading(at_ns)
        if reading.remaining_ns(reading.turn) > 0:
            return False
        self._clock.pause(at_ns)
        self._flagged = reading.turn
        self._invalidate()
        possibility = self._game.mate_possibility(reading.turn.opposite)
        if possibility is MatePossibility.IMPOSSIBLE:
            self._game.record_result("1/2-1/2")
        elif possibility is MatePossibility.POSSIBLE:
            self._game.record_result("0-1" if reading.turn is Color.WHITE else "1-0")
        return True

    def _play_move(self, move: Move) -> None:
        clock = self._clock
        at_ns = clock.sample_time() if clock else None
        if self._check_timeout(at_ns):
            raise ChessError("The time expired before the move.")
        self._game.play(move)
        self._draw_offer = None
        if clock is not None:
            assert at_ns is not None
            clock.complete_move(at_ns)
            del self._clock_positions[len(self._game.moves):]
            self._clock_positions.append(clock.reading(at_ns))
            if self._game.outcome().status is not GameStatus.ACTIVE:
                clock.pause(at_ns)

    def _restore_clock_after_edit(self) -> None:
        if self._clock is None:
            return
        self._flagged = None
        self._clock.restore_paused(self._clock_positions[len(self._game.moves)])

    def retry_bot(self) -> None:
        """Clear a bot error and request a move again (engine restarts if needed)."""
        self._ensure_open()
        self._bot_error = None
        self._maybe_request_bot()
        self._notify()

    def poll(self) -> bool:
        """Apply finished worker results on the owner thread. Returns True if state changed."""
        if self._check_timeout():
            self._notify()
            return True
        worker = self._worker
        if worker is None:
            return False
        changed = False
        while True:
            try:
                result = worker.results.get_nowait()
            except queue.Empty:
                break
            changed |= self._apply_result(result)
        if changed:
            self._notify()
        return changed

    def shutdown(self, timeout: float = 2.0) -> bool:
        if self._closed:
            return True
        self._invalidate()
        stopped = self._stop_worker(timeout)
        if self._worker is None and self._provider is not None:
            self._provider.close()
        self._closed = True
        return stopped

    # ----- internals ---------------------------------------------------
    def _apply_result(self, result: BotResult) -> bool:
        pending = self._pending
        if pending is None or (pending.generation, pending.ply) != (result.generation, result.ply):
            return False  # stale: game changed since the request was sent
        self._pending = None
        if result.error is not None:
            self._bot_error = result.error
            return True
        if self._game.outcome().status is not GameStatus.ACTIVE:
            return True
        if result.move is None:
            self._bot_error = "Engine returned no move in an active position."
            return True
        try:
            self._play_move(result.move)
        except ChessError as error:
            if self._flagged is None:
                self._bot_error = f"Engine move rejected: {error}"
            return True
        self._maybe_request_bot()
        return True

    def _maybe_request_bot(self) -> None:
        if self._setup.mode is not PlayMode.HUMAN_VS_BOT or self._provider is None:
            return
        if self._bot_error or self._pending is not None or (self._clock and not self._clock.running):
            return
        if self._game.state.turn is not self._setup.bot_color:
            return
        if self._game.outcome().status is not GameStatus.ACTIVE:
            return
        if self._worker is None or not self._worker.alive:
            self._worker = BotWorker(self._provider)
        ply = len(self._game.moves)
        timing = None
        if self._clock is not None:
            reading = self._clock.reading()
            timing = BotClock(
                reading.remaining_ms(Color.WHITE), reading.remaining_ms(Color.BLACK),
                self._clock.control.increment_ms, self._clock.control.increment_ms,
                reading.remaining_ms(reading.turn),
            )
        request = BotRequest(
            generation=self._generation,
            ply=ply,
            initial_fen=self._initial_fen,
            moves=tuple(self._game.moves),
            legal_moves=self._game.rules.legal_moves(self._game.state),
            game_id=self._game_id,
            clock=timing,
        )
        self._pending = request
        self._worker.submit(request)

    def _invalidate(self) -> None:
        self._draw_offer = None
        self._generation += 1
        if self._pending is not None:
            self._pending.cancelled.set()
            if self._provider is not None:
                self._provider.cancel()
        self._pending = None

    def _stop_worker(self, timeout: float = 2.0) -> bool:
        worker, self._worker = self._worker, None
        if worker is None:
            return True
        return worker.stop(timeout)

    def _human_to_move(self, outcome: MoveOutcome) -> bool:
        if outcome.status is not GameStatus.ACTIVE or (self._clock and not self._clock.running):
            return False
        if self._setup.mode is PlayMode.HUMAN_VS_HUMAN:
            return True
        return self._pending is None and self._game.state.turn is not self._setup.bot_color

    def _can_undo(self) -> bool:
        if not self._game.can_undo or self._flagged is not None:
            return False
        if self._clock is None and self._setup.mode is PlayMode.HUMAN_VS_BOT:
            # Bot opened the game: its first move alone is not undoable to a human turn.
            bot_first = self._game.initial_state.turn is self._setup.bot_color
            return len(self._game.moves) > (1 if bot_first else 0) or self._game.outcome().status in (
                GameStatus.RESIGNED, GameStatus.DRAW_CLAIMED, GameStatus.RECORDED_RESULT,
            )
        return True

    def _redo_available(self) -> bool:
        return self._game.can_redo

    def _can_redo(self) -> bool:
        return self._redo_available() and self._pending is None and self._flagged is None

    def _sync_san(self) -> list[str]:
        """Incrementally maintain SAN; avoids O(n) replay on every UI refresh."""
        moves = self._game.moves
        common = 0
        limit = min(len(moves), len(self._san_moves))
        while common < limit and moves[common] == self._san_moves[common]:
            common += 1
        if common < len(self._san_moves):
            del self._san[common:]
            del self._san_moves[common:]
        if common < len(moves):
            rules = self._game.rules
            advance = getattr(rules, "_apply_unchecked", rules.apply)  # moves were validated by play()
            state = self._game.initial_state
            if common:
                # Rebuild state at the common prefix from the game's own snapshots when possible.
                for move in moves[:common]:
                    state = advance(state, move)
            for move in moves[common:]:
                self._san.append(to_san(state, move, self._game.rules))
                self._san_moves.append(move)
                state = advance(state, move)
        return self._san

    def _notify(self) -> None:
        view = self.view()
        for listener in tuple(self._listeners):
            listener(view)

    def _ensure_open(self) -> None:
        if self._closed:
            raise ChessError("The game controller has been shut down.")
