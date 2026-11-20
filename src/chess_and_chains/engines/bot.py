"""Move providers (bots) and explicit engine configuration.

No engine is discovered, downloaded or installed automatically. An engine is
used only when the user configured an executable path, or a developer set
``CHESS_AND_CHAINS_ENGINE`` explicitly. Otherwise the project-owned mock
engine is used and labelled as such.
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import os
import shlex
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Protocol, Sequence

from ..chess import Move
from .presets import BotPreset, OptionPlan, load_presets, plan_options
from .uci import UCIEngine, UCIEngineError

ENGINE_ENV = "CHESS_AND_CHAINS_ENGINE"


@dataclass(frozen=True, slots=True)
class BotRequest:
    """Everything a provider needs; immutable so a worker cannot touch live game state."""

    generation: int
    ply: int
    initial_fen: str
    moves: tuple[Move, ...]
    legal_moves: tuple[Move, ...]


class MoveProvider(Protocol):
    @property
    def display_name(self) -> str: ...

    @property
    def is_mock(self) -> bool: ...

    def choose_move(self, request: BotRequest) -> Move | None: ...

    def cancel(self) -> None: ...

    def kill(self) -> None: ...

    def close(self) -> None: ...


class EngineConfigError(ValueError):
    """The engine configuration cannot be used."""


@dataclass(frozen=True, slots=True)
class EngineConfig:
    command: tuple[str, ...]
    display_name: str
    is_mock: bool
    source: str  # "mock", "settings", "environment"

    @classmethod
    def mock(cls, mode: str = "normal", seed: int = 0, delay_ms: int | None = None) -> EngineConfig:
        # Run from this package's own source root so no PYTHONPATH setup is needed.
        src_root = str(Path(__file__).resolve().parents[2])
        bootstrap = (
            "import sys; sys.path.insert(0, sys.argv.pop(1)); "
            "from chess_and_chains.engines.mock_engine import main; "
            "raise SystemExit(main(sys.argv[1:]))"
        )
        command = [sys.executable, "-c", bootstrap, src_root, "--mode", mode, "--seed", str(seed)]
        if delay_ms is not None:
            command += ["--delay-ms", str(delay_ms)]
        return cls(tuple(command), "Mock bot (test engine, not a chess AI)", True, "mock")

    @classmethod
    def from_path(cls, path: str | Path, args: Sequence[str] = (), source: str = "settings") -> EngineConfig:
        executable = Path(path).expanduser()
        if not executable.is_file():
            raise EngineConfigError(f"Engine executable not found: {executable}")
        if not os.access(executable, os.X_OK):
            raise EngineConfigError(f"Engine file is not executable: {executable}")
        return cls((str(executable), *args), executable.stem, False, source)


def resolve_engine_config(
    engine_path: str | None,
    environ: Mapping[str, str] | None = None,
) -> tuple[EngineConfig, str | None]:
    """Return the engine to use plus an optional warning; falls back to the mock."""
    env = os.environ if environ is None else environ
    if engine_path:
        try:
            return EngineConfig.from_path(engine_path), None
        except EngineConfigError as error:
            return EngineConfig.mock(), f"{error}. Using mock bot instead."
    dev = env.get(ENGINE_ENV)
    if dev:
        parts = shlex.split(dev)
        try:
            return EngineConfig.from_path(parts[0], parts[1:], source="environment"), None
        except (EngineConfigError, IndexError) as error:
            return EngineConfig.mock(), f"{ENGINE_ENV}: {error}. Using mock bot instead."
    return EngineConfig.mock(), None


@dataclass
class UCIBot:
    """MoveProvider backed by a UCI process. Blocking; call only from a worker."""

    config: EngineConfig
    preset: BotPreset = field(default_factory=lambda: load_presets()[2])
    startup_timeout: float = 5.0
    search_margin: float = 5.0
    _engine: UCIEngine | None = field(default=None, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _applied_preset: str | None = field(default=None, init=False, repr=False)
    last_plan: OptionPlan | None = field(default=None, init=False)
    engine_name: str | None = field(default=None, init=False)

    @property
    def display_name(self) -> str:
        return self.config.display_name

    @property
    def is_mock(self) -> bool:
        return self.config.is_mock

    def set_preset(self, preset: BotPreset) -> None:
        self.preset = preset

    def ensure_started(self) -> UCIEngine:
        with self._lock:
            engine = self._engine
            if engine is None or not engine.running:
                if engine is not None:
                    engine.close()
                engine = UCIEngine(
                    self.config.command,
                    startup_timeout=self.startup_timeout,
                    command_timeout=self.startup_timeout,
                    shutdown_timeout=1.0,
                )
                self._engine = engine
                self._applied_preset = None
                engine.start()
            if self._applied_preset != self.preset.id:
                plan = plan_options(self.preset, engine.options)
                for name, value in plan.apply:
                    engine.set_option(name, value)
                engine.is_ready()
                self.last_plan = plan
                self._applied_preset = self.preset.id
            return engine

    def choose_move(self, request: BotRequest) -> Move | None:
        engine = self.ensure_started()
        engine.set_position(request.initial_fen, request.moves)
        timeout = self.preset.movetime_ms / 1000 + self.search_margin
        return engine.go_movetime(self.preset.movetime_ms, request.legal_moves, timeout=timeout)

    def cancel(self) -> None:
        engine = self._engine
        if engine is not None:
            try:
                engine.stop_search()
            except UCIEngineError:
                pass

    def kill(self) -> None:
        engine = self._engine
        if engine is not None:
            engine.kill()

    def close(self) -> None:
        self.cancel()
        with self._lock:
            engine, self._engine = self._engine, None
        if engine is not None:
            engine.close()
