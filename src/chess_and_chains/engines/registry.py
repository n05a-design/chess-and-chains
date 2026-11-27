"""Local engine profiles and explicit, worker-compatible readiness checks.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import hashlib
import os
import platform
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from .bot import EngineConfig, EngineConfigError
from .uci import EngineTimeoutError, UCIEngine, UCIEngineError, UCIOption


class EngineAvailability(StrEnum):
    UNTESTED = "untested"
    BUSY = "busy"
    READY = "ready"
    UNAVAILABLE = "unavailable"
    UNRESPONSIVE = "unresponsive"
    CHANGED = "changed"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class EngineProfile:
    engine_id: str
    display_name: str
    executable: Path
    arguments: tuple[str, ...] = ()
    origin: str = "user-selected"
    declared_version: str | None = None
    license_id: str | None = None
    is_mock: bool = False

    def __post_init__(self) -> None:
        path = Path(self.executable).expanduser()
        if not self.engine_id or not self.display_name.strip() or not path.is_absolute():
            raise EngineConfigError("An engine profile requires an ID, a name and an absolute executable path.")
        if isinstance(self.arguments, str) or any(
            not isinstance(argument, str) or not argument or "\0" in argument for argument in self.arguments
        ):
            raise EngineConfigError("An engine argument must be a nonempty string without NUL bytes.")
        object.__setattr__(self, "executable", path)
        object.__setattr__(self, "arguments", tuple(self.arguments))

    @classmethod
    def from_config(cls, config: EngineConfig) -> EngineProfile:
        """Adapt an already authorized runtime configuration for inspection."""
        if not config.command:
            raise EngineConfigError("An engine configuration requires an executable.")
        executable, *arguments = config.command
        return cls(
            str(uuid4()), config.display_name, Path(executable), tuple(arguments),
            origin=config.source, is_mock=config.is_mock,
        )

    def _configuration(self) -> EngineConfig:
        executable = self.executable.resolve(strict=True)
        if sys.platform == "win32" and executable.suffix.casefold() in {".bat", ".cmd"}:
            raise EngineConfigError("Select the engine executable instead of a Windows batch script.")
        config = EngineConfig.from_path(executable, self.arguments, source=self.origin)
        return EngineConfig(config.command, self.display_name, self.is_mock, config.source)


@dataclass(frozen=True, slots=True)
class EngineProbe:
    engine_id: str
    status: EngineAvailability
    checked_at: datetime
    host_platform: str
    host_architecture: str
    resolved_executable: Path | None = None
    binary_sha256: str | None = None
    advertised_name: str | None = None
    options: tuple[UCIOption, ...] = ()
    error: str | None = None

    def option(self, name: str) -> UCIOption | None:
        key = name.casefold()
        return next((option for option in self.options if option.name.casefold() == key), None)


def _fingerprint(executable: Path) -> str:
    with executable.open("rb") as binary:
        return hashlib.file_digest(binary, "sha256").hexdigest()


def inspect_engine(profile: EngineProfile, *, timeout: float = 5.0) -> EngineProbe:
    """Inspect a user-selected executable and close it after the UCI readiness check.

    This performs file I/O and launches the configured process. Call it on a
    worker thread when invoked from a desktop app.
    """
    executable = None
    name = None
    options = ()
    digest = None
    error = None
    try:
        config = profile._configuration()
        executable = Path(config.command[0])
        digest = _fingerprint(executable)
    except (OSError, ValueError) as exc:
        status = EngineAvailability.UNAVAILABLE
        error = str(exc)
    else:
        try:
            with UCIEngine(config.command, startup_timeout=timeout, command_timeout=timeout) as engine:
                engine.is_ready()
                name = engine.name
                options = tuple(sorted(engine.options.values(), key=lambda option: option.name.casefold()))
        except EngineTimeoutError as exc:
            status = EngineAvailability.UNRESPONSIVE
            error = str(exc)
        except UCIEngineError as exc:
            status = EngineAvailability.ERROR
            error = str(exc)
        else:
            try:
                current_executable = profile.executable.resolve(strict=True)
                unchanged = current_executable == executable and _fingerprint(executable) == digest
            except OSError:
                unchanged = False
            status = EngineAvailability.READY if unchanged else EngineAvailability.CHANGED
            if not unchanged:
                error = "The executable changed during the readiness check. Run the check again."
    return EngineProbe(
        profile.engine_id, status, datetime.now(timezone.utc), sys.platform, platform.machine(),
        executable, digest, name, options, error,
    )


class EngineRegistry:
    """Track multiple explicitly registered local engines.

    Keep profiles for the current app lifetime. A readiness check can run in a
    worker while the owning thread reads availability and previous results.
    """

    def __init__(self) -> None:
        self._profiles: dict[str, EngineProfile] = {}
        self._latest: dict[str, EngineProbe] = {}
        self._successful: dict[str, EngineProbe] = {}
        self._busy: set[str] = set()
        self._lock = threading.Lock()

    def register(
        self, executable: str | Path, *, arguments: tuple[str, ...] = (), display_name: str | None = None,
        origin: str = "user-selected", declared_version: str | None = None, license_id: str | None = None,
    ) -> EngineProfile:
        path = Path(executable).expanduser()
        profile = EngineProfile(
            str(uuid4()), display_name or path.stem, path, arguments, origin, declared_version, license_id,
        )
        with self._lock:
            self._profiles[profile.engine_id] = profile
        return profile

    def profiles(self) -> tuple[EngineProfile, ...]:
        with self._lock:
            return tuple(self._profiles.values())

    def availability(self, engine_id: str) -> EngineAvailability:
        with self._lock:
            self._profiles[engine_id]
            if engine_id in self._busy:
                return EngineAvailability.BUSY
            result = self._latest.get(engine_id)
            return result.status if result else EngineAvailability.UNTESTED

    def last_success(self, engine_id: str) -> EngineProbe | None:
        with self._lock:
            self._profiles[engine_id]
            return self._successful.get(engine_id)

    def probe(self, engine_id: str, *, timeout: float = 5.0) -> EngineProbe:
        with self._lock:
            profile = self._profiles[engine_id]
            if engine_id in self._busy:
                raise EngineConfigError("This engine already has a readiness check in progress.")
            self._busy.add(engine_id)
        try:
            result = inspect_engine(profile, timeout=timeout)
            with self._lock:
                self._latest[engine_id] = result
                if result.status is EngineAvailability.READY:
                    self._successful[engine_id] = result
            return result
        finally:
            with self._lock:
                self._busy.remove(engine_id)

    def verified_configuration(self, engine_id: str) -> EngineConfig:
        """Recheck the probed bytes before handing off a launch configuration."""
        with self._lock:
            profile = self._profiles[engine_id]
            result = self._latest.get(engine_id)
            if engine_id in self._busy or result is None or result.status is not EngineAvailability.READY:
                raise EngineConfigError("Test the registered engine before use.")
        try:
            config = profile._configuration()
            executable = Path(config.command[0])
            matches = executable == result.resolved_executable and _fingerprint(executable) == result.binary_sha256
        except OSError as error:
            raise EngineConfigError(f"Could not check the registered engine: {error}") from error
        if not matches:
            raise EngineConfigError("The registered executable has changed. Test it again before use.")
        return config
