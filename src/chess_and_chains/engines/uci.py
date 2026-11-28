"""UCI subprocess adapter; engine binaries are supplied and configured by users."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import math
import queue
import re
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from ..chess import Move, parse_fen

_EOF = object()
_OPTION = re.compile(
    r"^option name (.+?) type (check|spin|combo|button|string)(?:\s|$)"
)


class UCIEngineError(RuntimeError):
    """Base error for engine process and protocol failures."""


class EngineLaunchError(UCIEngineError):
    """The configured engine process could not be started."""


class EngineStateError(UCIEngineError):
    """An operation is invalid for the current engine state."""


class EngineProtocolError(UCIEngineError):
    """The engine produced an invalid or unexpected UCI response."""


class EngineTimeoutError(UCIEngineError):
    """The engine did not answer before the configured deadline."""


@dataclass(frozen=True, slots=True)
class UCIOption:
    name: str
    kind: str
    declaration: str
    default: str | None = None
    minimum: int | None = None
    maximum: int | None = None
    choices: tuple[str, ...] = ()


class UCIEngine:
    """Run a configured executable without a shell or network access.

    All blocking methods must be called from a worker, not a Tk event handler.
    The rules domain supplies legal moves and validates the returned bestmove.
    """

    def __init__(
        self,
        command: Sequence[str | Path],
        *,
        startup_timeout: float = 5.0,
        command_timeout: float = 5.0,
        shutdown_timeout: float = 1.0,
        before_launch: Callable[[], None] | None = None,
    ) -> None:
        if isinstance(command, (str, bytes)) or not command:
            raise ValueError("Engine command must be a non-empty argument sequence.")
        if any(not isinstance(part, (str, Path)) or not str(part) for part in command):
            raise ValueError("Every engine command argument must be a non-empty string.")
        for timeout in (startup_timeout, command_timeout, shutdown_timeout):
            if (
                isinstance(timeout, bool)
                or not isinstance(timeout, (int, float))
                or not math.isfinite(timeout)
                or timeout <= 0
            ):
                raise ValueError("Engine timeouts must be positive.")

        self._command = tuple(str(part) for part in command)
        self._before_launch = before_launch
        self._startup_timeout = startup_timeout
        self._command_timeout = command_timeout
        self._shutdown_timeout = shutdown_timeout
        self._process: subprocess.Popen[str] | None = None
        self._output: queue.Queue[str | object] = queue.Queue()
        self._name: str | None = None
        self.author: str | None = None
        self.version: str | None = None
        self._options: dict[str, UCIOption] = {}
        self._reader: threading.Thread | None = None
        self._transaction_lock = threading.RLock()
        self._write_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._searching = False

    @property
    def running(self) -> bool:
        process = self._process
        return process is not None and process.poll() is None

    @property
    def searching(self) -> bool:
        with self._state_lock:
            return self._searching

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def options(self) -> dict[str, UCIOption]:
        return dict(self._options)

    def start(self) -> None:
        with self._transaction_lock:
            if self.running:
                raise EngineStateError("The engine is already running.")
            if self._process is not None:
                self._release_process(self._process)
            self._process = None
            self._name = None
            self.author = self.version = None
            self._options.clear()
            self._output = queue.Queue()
            try:
                if self._before_launch is not None:
                    self._before_launch()
                process = subprocess.Popen(
                    self._command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    shell=False,
                )
            except (OSError, ValueError) as error:
                raise EngineLaunchError(
                    f"Could not start configured engine {self._command[0]!r}: {error}"
                ) from error

            self._process = process
            reader = threading.Thread(
                target=self._read_output,
                args=(process,),
                name="uci-engine-output",
                daemon=True,
            )
            self._reader = reader
            reader.start()
            try:
                self._send("uci")
                self._read_until("uciok", self._startup_timeout)
            except UCIEngineError:
                self._terminate()
                raise

    def is_ready(self, timeout: float | None = None) -> None:
        with self._transaction_lock:
            response_timeout = self._effective_timeout(timeout)
            self._ensure_running()
            self._send("isready")
            self._read_until("readyok", response_timeout)

    def new_game(self, timeout: float | None = None) -> None:
        with self._transaction_lock:
            response_timeout = self._effective_timeout(timeout)
            self._ensure_running()
            self._send("ucinewgame")
            self.is_ready(response_timeout)

    def set_option(self, name: str, value: str | int | bool | None = None) -> None:
        with self._transaction_lock:
            self._ensure_running()
            option = self._options.get(name)
            if option is None:
                raise ValueError(f"Engine did not advertise UCI option {name!r}.")
            if any(character in name for character in "\r\n"):
                raise ValueError("UCI option names cannot contain line breaks.")
            if option.kind == "button":
                if value is not None:
                    raise ValueError("Button options do not accept a value.")
                command = f"setoption name {name}"
            elif option.kind == "check":
                if not (
                    type(value) is bool
                    or (isinstance(value, str) and value in ("true", "false"))
                ):
                    raise ValueError(f"UCI option {name!r} requires a boolean value.")
                command = f"setoption name {name} value {str(value).lower()}"
            elif option.kind == "spin":
                if not isinstance(value, int) or isinstance(value, bool):
                    raise ValueError(f"UCI option {name!r} requires an integer value.")
                if (
                    option.minimum is not None and value < option.minimum
                ) or (
                    option.maximum is not None and value > option.maximum
                ):
                    raise ValueError(f"UCI option {name!r} is outside its advertised range.")
                command = f"setoption name {name} value {value}"
            elif option.kind == "combo":
                if not isinstance(value, str) or value not in option.choices:
                    raise ValueError(f"UCI option {name!r} requires one advertised choice.")
                if any(character in value for character in "\r\n"):
                    raise ValueError("UCI option values cannot contain line breaks.")
                command = f"setoption name {name} value {value}"
            elif option.kind == "string":
                if not isinstance(value, str):
                    raise ValueError("This UCI option requires a string value.")
                text = value
                if any(character in text for character in "\r\n"):
                    raise ValueError("UCI option values cannot contain line breaks.")
                command = f"setoption name {name} value {text}"
            else:
                raise EngineProtocolError(f"Unsupported option type {option.kind!r}.")
            self._send(command)

    def set_position(
        self,
        fen: str | None = None,
        moves: Sequence[Move] = (),
    ) -> None:
        with self._transaction_lock:
            self._ensure_running()
            if fen is None:
                command = "position startpos"
            else:
                parse_fen(fen)
                command = f"position fen {' '.join(fen.split())}"
            if moves:
                if any(not isinstance(move, Move) for move in moves):
                    raise TypeError("UCI position moves must be chess Move values.")
                command += " moves " + " ".join(move.to_uci() for move in moves)
            self._send(command)

    def go_movetime(
        self,
        milliseconds: int,
        legal_moves: Sequence[Move],
        timeout: float | None = None,
        *,
        cancelled: threading.Event | None = None,
        on_info: Callable[[str], None] | None = None,
    ) -> Move | None:
        """Search for one move; analysis callbacks also poll for cancellation.

        The callback runs on the search owner thread. Without it, the move
        provider can cancel an in-flight search with ``stop_search()`` as before.
        """
        if (
            not isinstance(milliseconds, int)
            or isinstance(milliseconds, bool)
            or milliseconds <= 0
        ):
            raise ValueError("Move time must be a positive integer in milliseconds.")
        return self._search(f"go movetime {milliseconds}", legal_moves, timeout, cancelled, on_info)

    def go_clock(
        self,
        white_ms: int,
        black_ms: int,
        white_increment_ms: int,
        black_increment_ms: int,
        legal_moves: Sequence[Move],
        *,
        timeout: float | None = None,
        cancelled: threading.Event | None = None,
    ) -> Move | None:
        """Search with Fischer time controls. Values are UCI milliseconds."""
        times = (white_ms, black_ms, white_increment_ms, black_increment_ms)
        if any(type(value) is not int or value < 0 for value in times):
            raise ValueError("UCI clock values must be non-negative integers in milliseconds.")
        command = f"go wtime {white_ms} btime {black_ms} winc {white_increment_ms} binc {black_increment_ms}"
        return self._search(command, legal_moves, timeout, cancelled, None)

    def _search(
        self, command: str, legal_moves: Sequence[Move], timeout: float | None,
        cancelled: threading.Event | None, on_info: Callable[[str], None] | None,
    ) -> Move | None:
        response_timeout = self._effective_timeout(timeout)
        legal = tuple(legal_moves)
        if any(not isinstance(move, Move) for move in legal):
            raise TypeError("Legal moves must be chess Move values.")
        with self._transaction_lock:
            self._ensure_running()
            try:
                with self._state_lock:
                    if cancelled is not None and cancelled.is_set():
                        return None
                    self._send(command)
                    self._searching = True
                response = self._read_until_matching(
                    lambda line: line.startswith("bestmove "), response_timeout,
                    on_info=on_info, cancelled=cancelled if on_info is not None else None,
                )
                if on_info is not None and cancelled is not None and cancelled.is_set():
                    return None
                move = self._parse_bestmove(response)
                if move is None:
                    if legal:
                        raise EngineProtocolError(
                            "Engine returned no move while legal moves are available."
                        )
                elif move not in legal:
                    raise EngineProtocolError(
                        f"Engine returned illegal move {move.to_uci()!r}."
                    )
                return move
            except EngineTimeoutError:
                self._terminate()
                raise
            finally:
                with self._state_lock:
                    self._searching = False

    def stop_search(self) -> bool:
        with self._state_lock:
            if not self._searching:
                return False
            self._send("stop")
            return True

    def kill(self) -> None:
        """Force-terminate the process without waiting for an active transaction.

        Safe to call from any thread. A blocked search then fails with
        EngineProtocolError; call close() afterwards to release resources.
        """
        process = self._process
        if process is not None and process.poll() is None:
            try:
                process.kill()
            except (ProcessLookupError, OSError):
                pass

    def close(self) -> None:
        with self._transaction_lock:
            process = self._process
            if process is None:
                return
            if process.poll() is None:
                try:
                    self._send("quit")
                    process.wait(timeout=self._shutdown_timeout)
                except (OSError, subprocess.TimeoutExpired, UCIEngineError):
                    self._terminate()
                    return
            self._release_process(process)
            self._process = None

    def __enter__(self) -> UCIEngine:
        self.start()
        return self

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        self.close()

    def _read_output(self, process: subprocess.Popen[str]) -> None:
        try:
            assert process.stdout is not None
            for line in process.stdout:
                self._output.put(line.rstrip("\r\n"))
        except (OSError, ValueError):
            pass
        finally:
            self._output.put(_EOF)

    def _read_until(self, expected: str, timeout: float) -> str:
        return self._read_until_matching(lambda line: line == expected, timeout)

    def _read_until_matching(
        self, predicate: Callable[[str], bool], timeout: float, *,
        on_info: Callable[[str], None] | None = None,
        cancelled: threading.Event | None = None,
    ) -> str:
        deadline = time.monotonic() + timeout
        stopping = False
        while True:
            if cancelled is not None and cancelled.is_set() and not stopping:
                self.stop_search()
                stopping = True
                deadline = min(deadline, time.monotonic() + self._shutdown_timeout)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EngineTimeoutError("Engine response timed out.")
            try:
                output = self._output.get(timeout=min(remaining, 0.05) if cancelled is not None else remaining)
            except queue.Empty:
                continue
            if output is _EOF:
                process = self._process
                code = process.poll() if process is not None else None
                raise EngineProtocolError(
                    f"Engine closed its output unexpectedly (exit code {code})."
                )
            assert isinstance(output, str)
            if predicate(output):
                return output
            if on_info is not None and not stopping and output.startswith("info "):
                on_info(output)
            elif output.startswith("id name "):
                self._name = output.removeprefix("id name ").strip() or None
            elif output.startswith("id author "):
                self.author = output.removeprefix("id author ").strip() or None
            elif output.startswith("id version "):
                self.version = output.removeprefix("id version ").strip() or None
            elif output.startswith("option "):
                self._record_option(output)

    def _record_option(self, line: str) -> None:
        match = _OPTION.match(line)
        if match is None:
            raise EngineProtocolError(f"Malformed UCI option declaration: {line!r}.")
        name, kind = match.groups()
        remainder = line[match.end() :].split()
        fields: dict[str, list[list[str]]] = {}
        current: list[str] | None = None
        for token in remainder:
            if token in ("default", "min", "max", "var"):
                current = []
                fields.setdefault(token, []).append(current)
            elif current is None:
                raise EngineProtocolError(
                    f"Malformed UCI option declaration: {line!r}."
                )
            else:
                current.append(token)

        def field(name: str) -> str | None:
            values = fields.get(name, [])
            return " ".join(values[0]) if values and values[0] else None

        try:
            minimum = int(field("min")) if field("min") is not None else None
            maximum = int(field("max")) if field("max") is not None else None
        except ValueError as error:
            raise EngineProtocolError(
                f"Malformed UCI option bounds: {line!r}."
            ) from error
        choices = tuple(" ".join(parts) for parts in fields.get("var", []))
        self._options[name] = UCIOption(
            name=name,
            kind=kind,
            declaration=line,
            default=field("default"),
            minimum=minimum,
            maximum=maximum,
            choices=choices,
        )

    @staticmethod
    def _parse_bestmove(line: str) -> Move | None:
        parts = line.split()
        if len(parts) == 2 and parts[1] in ("(none)", "0000"):
            return None
        if len(parts) not in (2, 4) or (len(parts) == 4 and parts[2] != "ponder"):
            raise EngineProtocolError(f"Malformed bestmove response: {line!r}.")
        try:
            move = Move.from_uci(parts[1])
            if len(parts) == 4:
                Move.from_uci(parts[3])
        except ValueError as error:
            raise EngineProtocolError(f"Malformed bestmove response: {line!r}.") from error
        return move

    def _send(self, command: str) -> None:
        if any(character in command for character in "\r\n"):
            raise ValueError("UCI commands must be a single line.")
        process = self._process
        if process is None or process.poll() is not None:
            raise EngineStateError("The engine process is not running.")
        try:
            with self._write_lock:
                assert process.stdin is not None
                process.stdin.write(command + "\n")
                process.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            raise EngineProtocolError("Could not write to the engine process.") from error

    def _ensure_running(self) -> None:
        if not self.running:
            raise EngineStateError("Start the engine before sending UCI commands.")

    def _terminate(self) -> None:
        process = self._process
        if process is None:
            return
        if process.poll() is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=self._shutdown_timeout)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                process.wait()
        self._release_process(process)
        self._process = None

    def _release_process(self, process: subprocess.Popen[str]) -> None:
        reader = self._reader
        if reader is not None and reader is not threading.current_thread():
            reader.join(timeout=self._shutdown_timeout)
        for stream in (process.stdin, process.stdout):
            if stream is not None and not stream.closed:
                try:
                    stream.close()
                except OSError:
                    pass
        if reader is not None and reader is not threading.current_thread():
            reader.join(timeout=self._shutdown_timeout)
        self._reader = None

    def _effective_timeout(self, timeout: float | None) -> float:
        value = self._command_timeout if timeout is None else timeout
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0
        ):
            raise ValueError("Engine response timeouts must be positive numbers.")
        return float(value)
