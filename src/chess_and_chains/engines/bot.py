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
import re
import hashlib
import shlex
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Protocol, Sequence

from ..chess import Move
from .presets import BotPreset, OptionPlan, load_presets, plan_options
from .uci import UCIEngine, UCIEngineError

ENGINE_ENV = "CHESS_AND_CHAINS_ENGINE"


@dataclass(frozen=True, slots=True)
class BotClock:
    white_ms: int
    black_ms: int
    white_increment_ms: int
    black_increment_ms: int
    remaining_ms: int


@dataclass(frozen=True, slots=True)
class BotRequest:
    """Game data plus a thread-safe cancellation signal owned by the controller."""

    generation: int
    ply: int
    initial_fen: str
    moves: tuple[Move, ...]
    legal_moves: tuple[Move, ...]
    game_id: int = 0
    cancelled: threading.Event = field(default_factory=threading.Event, compare=False, repr=False)
    clock: BotClock | None = None


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
class EngineProvenance:
    reference: str
    binary_sha256: str
    name: str | None = None
    author: str | None = None
    version: str | None = None
    effective_options: tuple[tuple[str, str | int | bool], ...] | None = None

    def __post_init__(self) -> None:
        if (not re.fullmatch(r"uci1:[0-9a-f-]{36}:[0-9a-f]{64}", self.reference)
                or not re.fullmatch(r"[0-9a-f]{64}", self.binary_sha256)
                or any(value is not None and (not isinstance(value, str) or len(value) > 512)
                       for value in (self.name, self.author, self.version))):
            raise ValueError("Invalid historical engine identity.")
        if self.effective_options is not None:
            options = tuple(tuple(entry) for entry in self.effective_options)
            if len(options) > 128 or any(
                not isinstance(name, str) or not name or len(name) > 256 or type(value) not in (str, int, bool)
                for name, value in options
            ):
                raise ValueError("Invalid historical UCI options.")
            object.__setattr__(self, "effective_options", options)

    @property
    def engine_id(self) -> str:
        return self.reference.split(":")[1]

    @property
    def configuration_fingerprint(self) -> str:
        return self.reference.split(":")[2]


@dataclass(frozen=True, slots=True)
class EngineConfig:
    command: tuple[str, ...]
    display_name: str
    is_mock: bool
    source: str  # "mock", "settings", "environment"

    registry_reference: str | None = None
    provenance: EngineProvenance | None = None
    verified_version: str | None = None
    approved_options: tuple[tuple[str, str | int | bool], ...] = ()
    before_launch: Callable[[], None] | None = field(default=None, repr=False, compare=False)

    def session_reference(self) -> str:
        """Identify a configuration without persisting executable commands."""
        if self.is_mock:
            return "mock"
        return self.registry_reference or self.legacy_reference()

    def legacy_reference(self) -> str:
        path = Path(self.command[0]).resolve(strict=True)
        stat = path.stat()
        identity = (str(path), stat.st_size, stat.st_mtime_ns, *self.command[1:])
        return hashlib.sha256(repr(identity).encode("utf-8")).hexdigest()

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


def split_engine_command(text: str, *, windows: bool | None = None) -> list[str]:
    """Split ``CHESS_AND_CHAINS_ENGINE`` into argv without a shell.

    POSIX ``shlex`` treats backslashes as escapes and would mangle Windows
    paths (``C:\\Engines\\x.exe`` -> ``C:Enginesx.exe``), so Windows uses
    non-POSIX splitting and strips surrounding quotes.
    """
    is_windows = os.name == "nt" if windows is None else windows
    if not is_windows:
        return shlex.split(text)
    parts = shlex.split(text, posix=False)
    return [part[1:-1] if len(part) >= 2 and part[0] == part[-1] == '"' else part for part in parts]


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
        try:
            parts = split_engine_command(dev)
            return EngineConfig.from_path(parts[0], parts[1:], source="environment"), None
        except (ValueError, IndexError) as error:
            return EngineConfig.mock(), f"{ENGINE_ENV}: {error}. Using mock bot instead."
    return EngineConfig.mock(), None


def probe_engine(config: EngineConfig, *, timeout: float = 5.0) -> tuple[str, int]:
    """Verify a local executable answers both UCI handshakes, then close it."""
    with UCIEngine(config.command, startup_timeout=timeout, command_timeout=timeout) as engine:
        engine.is_ready()
        return engine.name or config.display_name, len(engine.options)


@dataclass
class UCIBot:
    """MoveProvider backed by a UCI process. Blocking; call only from a worker."""

    config: EngineConfig
    preset: BotPreset = field(default_factory=lambda: load_presets()[2])
    startup_timeout: float = 5.0
    search_margin: float = 5.0
    _engine: UCIEngine | None = field(default=None, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _game_id: int | None = field(default=None, init=False, repr=False)
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

    def ensure_started(self, preset: BotPreset | None = None) -> UCIEngine:
        preset = preset or self.preset
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
                    before_launch=self.config.before_launch,
                )
                self._engine = engine
                self._applied_preset = None
                self._game_id = None
                engine.start()
                for name, value in self.config.approved_options:
                    engine.set_option(name, value)
            if self._applied_preset != preset.id:
                plan = plan_options(preset, engine.options)
                for name, value in plan.apply:
                    engine.set_option(name, value)
                engine.is_ready()
                self.last_plan = plan
                self._applied_preset = preset.id
            return engine

    def choose_move(self, request: BotRequest) -> Move | None:
        if request.cancelled.is_set():
            return None
        preset = self.preset
        try:
            engine = self.ensure_started(preset)
            if request.cancelled.is_set():
                return None
            if self._game_id != request.game_id:
                engine.new_game()
                self._game_id = request.game_id
            engine.set_position(request.initial_fen, request.moves)
            if request.clock is not None:
                timing = request.clock
                return engine.go_clock(
                    timing.white_ms, timing.black_ms, timing.white_increment_ms, timing.black_increment_ms,
                    request.legal_moves, timeout=timing.remaining_ms / 1000 + self.search_margin,
                    cancelled=request.cancelled,
                )
            timeout = preset.movetime_ms / 1000 + self.search_margin
            return engine.go_movetime(
                preset.movetime_ms, request.legal_moves, timeout=timeout, cancelled=request.cancelled,
            )
        except UCIEngineError:
            self.close()
            raise

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
