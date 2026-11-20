"""UI-independent game controller with an asynchronous bot worker.

Threading contract
------------------
* Every public method except ``BotWorker`` internals must be called from one
  owner thread (the Tk main thread in the app).
* The worker thread only receives an immutable ``BotRequest`` and calls the
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
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from ..chess import (
    ChessError,
    ChessGame,
    Color,
    GameState,
    GameStatus,
    IllegalMoveError,
    Move,
    MoveOutcome,
    parse_fen,
    to_fen,
    to_san,
)
from ..engines.bot import BotRequest, MoveProvider


class PlayMode(str, Enum):
    HUMAN_VS_HUMAN = "human-vs-human"
    HUMAN_VS_BOT = "human-vs-bot"


@dataclass(frozen=True, slots=True)
class GameSetup:
    mode: PlayMode = PlayMode.HUMAN_VS_HUMAN
    bot_color: Color | None = None
    initial_fen: str | None = None

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
    def __init__(self, provider: MoveProvider | None = None) -> None:
        self._provider = provider
        self._worker: BotWorker | None = None
        self._listeners: list[Listener] = []
        self._generation = 0
        self._pending: tuple[int, int] | None = None
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
        self._invalidate()
        self._setup = setup
        self._game = ChessGame(initial)
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
            self._setup = GameSetup.two_players()
        self._maybe_request_bot()
        self._notify()

    def play_human(self, move: Move) -> None:
        self._ensure_open()
        outcome = self._game.outcome()
        if not self._human_to_move(outcome):
            raise IllegalMoveError("It is not a human player's turn.")
        self._game.play(move)
        self._maybe_request_bot()
        self._notify()

    def undo(self) -> None:
        """Undo one ply (two players) or back to the human's last decision (bot)."""
        self._ensure_open()
        if not self._can_undo():
            raise ChessError("There is no move to undo.")
        self._invalidate()
        self._bot_error = None
        self._game.undo()
        if self._setup.mode is PlayMode.HUMAN_VS_BOT:
            while self._game.state.turn is self._setup.bot_color and self._game.moves:
                self._game.undo()
        self._maybe_request_bot()
        self._notify()

    def redo(self) -> None:
        self._ensure_open()
        if not self._can_redo():
            raise ChessError("There is no move to redo.")
        self._invalidate()
        self._game.redo()
        if self._setup.mode is PlayMode.HUMAN_VS_BOT:
            while self._game.state.turn is self._setup.bot_color and self._redo_available():
                self._game.redo()
        self._maybe_request_bot()
        self._notify()

    def resign(self) -> None:
        self._ensure_open()
        self._invalidate()
        color = self._game.state.turn
        if self._setup.mode is PlayMode.HUMAN_VS_BOT:
            color = self._setup.bot_color.opposite  # type: ignore[union-attr]
        self._game.resign(color)
        self._notify()

    def retry_bot(self) -> None:
        """Clear a bot error and request a move again (engine restarts if needed)."""
        self._ensure_open()
        self._bot_error = None
        self._maybe_request_bot()
        self._notify()

    def poll(self) -> bool:
        """Apply finished worker results on the owner thread. Returns True if state changed."""
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
        if self._pending != (result.generation, result.ply):
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
            self._game.play(result.move)
        except ChessError as error:
            self._bot_error = f"Engine move rejected: {error}"
            return True
        self._maybe_request_bot()
        return True

    def _maybe_request_bot(self) -> None:
        if self._setup.mode is not PlayMode.HUMAN_VS_BOT or self._provider is None:
            return
        if self._bot_error or self._pending is not None:
            return
        if self._game.state.turn is not self._setup.bot_color:
            return
        if self._game.outcome().status is not GameStatus.ACTIVE:
            return
        if self._worker is None or not self._worker.alive:
            self._worker = BotWorker(self._provider)
        ply = len(self._game.moves)
        request = BotRequest(
            generation=self._generation,
            ply=ply,
            initial_fen=self._initial_fen,
            moves=tuple(self._game.moves),
            legal_moves=self._game.rules.legal_moves(self._game.state),
        )
        self._pending = (self._generation, ply)
        self._worker.submit(request)

    def _invalidate(self) -> None:
        self._generation += 1
        if self._pending is not None and self._provider is not None:
            self._provider.cancel()
        self._pending = None

    def _stop_worker(self, timeout: float = 2.0) -> bool:
        worker, self._worker = self._worker, None
        if worker is None:
            return True
        return worker.stop(timeout)

    def _human_to_move(self, outcome: MoveOutcome) -> bool:
        if outcome.status is not GameStatus.ACTIVE:
            return False
        if self._setup.mode is PlayMode.HUMAN_VS_HUMAN:
            return True
        return self._pending is None and self._game.state.turn is not self._setup.bot_color

    def _can_undo(self) -> bool:
        if not self._game.moves and self._game.outcome().status is GameStatus.ACTIVE:
            return False
        if self._setup.mode is PlayMode.HUMAN_VS_BOT:
            # Bot opened the game: its first move alone is not undoable to a human turn.
            bot_first = self._game.initial_state.turn is self._setup.bot_color
            return len(self._game.moves) > (1 if bot_first else 0) or self._game.outcome().status is GameStatus.RESIGNED
        return True

    def _redo_available(self) -> bool:
        return self._game.can_redo

    def _can_redo(self) -> bool:
        return self._redo_available() and self._pending is None

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
