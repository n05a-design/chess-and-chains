"""Local engine profiles and explicit, worker-compatible readiness checks.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
import os
import platform
import sqlite3
import sys
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from .bot import EngineConfig, EngineConfigError, EngineProvenance
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
    configured_options: tuple[tuple[str, str | int | bool], ...] = ()
    resources: tuple[Path, ...] = ()

    def __post_init__(self) -> None:
        path = Path(self.executable).expanduser()
        if not self.engine_id or not self.display_name.strip() or not path.is_absolute():
            raise EngineConfigError("An engine profile requires an ID, a name and an absolute executable path.")
        if isinstance(self.arguments, str) or any(
            not isinstance(argument, str) or not argument or any(char in argument for char in "\0\r\n") for argument in self.arguments
        ):
            raise EngineConfigError("An engine argument must be a nonempty string without NUL bytes.")
        options = tuple(sorted((tuple(entry) for entry in self.configured_options), key=lambda entry: entry[0].casefold()))
        names = [name.casefold() for name, _ in options]
        if len(names) != len(set(names)) or any(
            not name or any(char in name for char in "\0\r\n") or type(value) not in (str, int, bool)
            or (isinstance(value, str) and any(char in value for char in "\0\r\n"))
            for name, value in options
        ):
            raise EngineConfigError("Invalid configured UCI options.")
        resources = tuple(sorted({Path(item).expanduser() for item in self.resources}))
        if any(not item.is_absolute() for item in resources):
            raise EngineConfigError("Engine resource paths must be absolute.")
        object.__setattr__(self, "configured_options", options)
        object.__setattr__(self, "resources", resources)
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
        if sys.platform == "win32" and any(path.suffix.casefold() in {".bat", ".cmd"}
                                            for path in (self.executable, executable)):
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
    advertised_author: str | None = None
    advertised_version: str | None = None
    resource_hashes: tuple[tuple[str, str], ...] = ()
    configuration_fingerprint: str | None = None

    def reference(self) -> str:
        if self.configuration_fingerprint is None:
            raise EngineConfigError("An unverified configuration has no engine reference.")
        return f"uci1:{self.engine_id}:{self.configuration_fingerprint}"

    def option(self, name: str) -> UCIOption | None:
        key = name.casefold()
        return next((option for option in self.options if option.name.casefold() == key), None)


def _fingerprint(executable: Path) -> str:
    if not executable.is_file():
        raise OSError(f"Engine file is unavailable: {executable}")
    with executable.open("rb") as binary:
        return hashlib.file_digest(binary, "sha256").hexdigest()


def _resource_hashes(profile: EngineProfile) -> tuple[tuple[str, str], ...]:
    return tuple((str(path.resolve(strict=True)), _fingerprint(path)) for path in profile.resources)


def _configuration_fingerprint(
    profile: EngineProfile, digest: str, resources: tuple[tuple[str, str], ...],
) -> str:
    canonical = json.dumps(
        {"schema": 1, "binary": digest, "args": profile.arguments,
         "options": [(name.casefold(), value) for name, value in profile.configured_options], "resources": resources},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def inspect_engine(profile: EngineProfile, *, timeout: float = 5.0) -> EngineProbe:
    """Inspect a user-selected executable and close it after the UCI readiness check.

    This performs file I/O and launches the configured process. Call it on a
    worker thread when invoked from a desktop app.
    """
    executable = None
    name = author = version = None
    options = ()
    resources = ()
    fingerprint = None
    digest = None
    error = None
    try:
        config = profile._configuration()
        executable = Path(config.command[0])
        digest = _fingerprint(executable)
        resources = _resource_hashes(profile)
    except (OSError, ValueError) as exc:
        status = EngineAvailability.UNAVAILABLE
        error = str(exc)
    else:
        try:
            def verify_probe_target() -> None:
                if (profile.executable.resolve(strict=True) != executable or _fingerprint(executable) != digest
                        or _resource_hashes(profile) != resources):
                    raise EngineConfigError("The selected engine changed before the readiness check.")

            with UCIEngine(
                config.command, startup_timeout=timeout, command_timeout=timeout, before_launch=verify_probe_target,
            ) as engine:
                for option, value in profile.configured_options:
                    engine.set_option(option, value)
                engine.is_ready()
                name = engine.name[:512] if isinstance(engine.name, str) else None
                author = engine.author[:512] if isinstance(engine.author, str) else None
                version = engine.version[:512] if isinstance(engine.version, str) else None
                options = tuple(sorted(engine.options.values(), key=lambda option: option.name.casefold()))
        except EngineTimeoutError as exc:
            status = EngineAvailability.UNRESPONSIVE
            error = str(exc)
        except (UCIEngineError, ValueError) as exc:
            status = EngineAvailability.ERROR
            error = str(exc)
        else:
            try:
                current_executable = profile.executable.resolve(strict=True)
                unchanged = (current_executable == executable and _fingerprint(executable) == digest
                             and _resource_hashes(profile) == resources)
            except OSError:
                unchanged = False
            status = EngineAvailability.READY if unchanged else EngineAvailability.CHANGED
            if unchanged:
                fingerprint = _configuration_fingerprint(profile, digest, resources)
            else:
                error = "The executable changed during the readiness check. Run the check again."
    return EngineProbe(
        profile.engine_id, status, datetime.now(timezone.utc), sys.platform, platform.machine(),
        executable, digest, name, options, error, author, version, resources, fingerprint,
    )


class EngineRegistry:
    """Track multiple explicitly registered local engines.

    Registrations are local to a profile. Workers open short-lived SQLite
    connections so approval updates do not share a thread-bound connection.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._profiles: dict[str, EngineProfile] = {}
        self._latest: dict[str, EngineProbe] = {}
        self._successful: dict[str, EngineProbe] = {}
        self._busy: set[str] = set()
        self._lock = threading.Lock()
        self._path = path
        if path is not None:
            try:
                with closing(sqlite3.connect(path)) as connection, connection:
                    schema = connection.execute("PRAGMA user_version").fetchone()[0]
                    if schema not in (0, 1):
                        raise EngineConfigError("Unsupported local engine registry schema.")
                    connection.execute("""
                        CREATE TABLE IF NOT EXISTS engine_profiles (
                            id TEXT PRIMARY KEY, payload TEXT NOT NULL CHECK (length(payload) <= 262144)
                        )
                    """)
                    connection.execute("PRAGMA user_version = 1")
                    for engine_id, payload in connection.execute("SELECT id, payload FROM engine_profiles ORDER BY rowid"):
                        try:
                            profile, latest, successful = self._decode(engine_id, payload)
                        except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
                            # Preserve the record for inspection and keep it inactive.
                            continue
                        self._profiles[engine_id] = profile
                        if latest is not None:
                            self._latest[engine_id] = latest
                        if successful is not None:
                            self._successful[engine_id] = successful
            except sqlite3.Error as error:
                raise EngineConfigError(f"Cannot open local engine registry: {error}") from error

    @staticmethod
    def _decode(engine_id: str, payload: str) -> tuple[EngineProfile, EngineProbe | None, EngineProbe | None]:
        if str(UUID(engine_id)) != engine_id or len(payload) > 262144:
            raise ValueError("Invalid engine registry record.")
        record = json.loads(payload)
        profile = EngineProfile(**record["profile"])
        if profile.engine_id != engine_id:
            raise ValueError("Engine registry identifiers do not match.")

        def probe(value: dict | None) -> EngineProbe | None:
            if value is None:
                return None
            value["status"] = EngineAvailability(value["status"])
            value["checked_at"] = datetime.fromisoformat(value["checked_at"])
            executable = value["resolved_executable"]
            value["resolved_executable"] = Path(executable) if executable else None
            value["options"] = tuple(UCIOption(**(option | {"choices": tuple(option["choices"])}))
                                     for option in value["options"])
            value["resource_hashes"] = tuple(tuple(item) for item in value["resource_hashes"])
            result = EngineProbe(**value)
            if result.engine_id != engine_id or result.checked_at.tzinfo is None:
                raise ValueError("Invalid engine check identity.")
            if result.status is EngineAvailability.READY:
                digest = result.binary_sha256
                if (digest is None or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest)
                        or result.configuration_fingerprint != _configuration_fingerprint(
                            profile, digest, result.resource_hashes,
                        )):
                    raise ValueError("Engine verification fingerprint does not match.")
            return result

        return profile, probe(record["latest"]), probe(record["successful"])

    def _persist(self, profile: EngineProfile, latest: EngineProbe | None, successful: EngineProbe | None) -> None:
        if self._path is None:
            return
        payload = json.dumps(
            {"profile": asdict(profile), "latest": asdict(latest) if latest else None,
             "successful": asdict(successful) if successful else None},
            default=str, ensure_ascii=True, separators=(",", ":"),
        )
        try:
            with closing(sqlite3.connect(self._path)) as connection, connection:
                if latest is None:
                    connection.execute("INSERT INTO engine_profiles(id, payload) VALUES (?, ?)", (profile.engine_id, payload))
                else:
                    changed = connection.execute("UPDATE engine_profiles SET payload = ? WHERE id = ?",
                                                 (payload, profile.engine_id))
                    if changed.rowcount != 1:
                        raise EngineConfigError("The engine registration was removed during the test.")
        except sqlite3.Error as error:
            raise EngineConfigError(f"Cannot save local engine registry: {error}") from error

    def register(
        self, executable: str | Path, *, arguments: tuple[str, ...] = (), display_name: str | None = None,
        origin: str = "user-selected", declared_version: str | None = None, license_id: str | None = None,
        options: tuple[tuple[str, str | int | bool], ...] = (), resources: tuple[Path, ...] = (),
    ) -> EngineProfile:
        path = Path(executable).expanduser()
        profile = EngineProfile(
            str(uuid4()), display_name or path.stem, path, arguments, origin, declared_version, license_id,
            configured_options=options, resources=resources,
        )
        with self._lock:
            self._persist(profile, None, None)
            self._profiles[profile.engine_id] = profile
        return profile

    def profile_for_command(self, executable: Path, arguments: tuple[str, ...] = ()) -> EngineProfile | None:
        with self._lock:
            return next((item for item in self._profiles.values()
                         if item.executable == executable and item.arguments == arguments), None)

    def remove(self, engine_id: str) -> None:
        with self._lock:
            if engine_id in self._busy:
                raise EngineConfigError("Wait for the readiness check to finish.")
            if self._path is not None:
                try:
                    with closing(sqlite3.connect(self._path)) as connection, connection:
                        connection.execute("DELETE FROM engine_profiles WHERE id = ?", (engine_id,))
                except sqlite3.Error as error:
                    raise EngineConfigError(f"Cannot remove engine registration: {error}") from error
            self._profiles.pop(engine_id)
            self._latest.pop(engine_id, None)
            self._successful.pop(engine_id, None)

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
                previous = self._successful.get(engine_id)
                self._persist(profile, result, result if result.status is EngineAvailability.READY else previous)
                self._latest[engine_id] = result
                if result.status is EngineAvailability.READY:
                    self._successful[engine_id] = result
            return result
        finally:
            with self._lock:
                self._busy.remove(engine_id)

    def launch_configuration(self, engine_id: str) -> EngineConfig:
        """Prepare a guarded configuration without hashing on the owner thread."""
        with self._lock:
            profile = self._profiles[engine_id]
            result = self._latest.get(engine_id)
            if engine_id in self._busy or result is None or result.status is not EngineAvailability.READY:
                raise EngineConfigError("Test the registered engine before use.")
        executable = result.resolved_executable

        def recheck() -> None:
            try:
                if self._path is None:
                    with self._lock:
                        current = self._latest.get(engine_id)
                else:
                    with closing(sqlite3.connect(self._path)) as connection:
                        row = connection.execute("SELECT payload FROM engine_profiles WHERE id = ?", (engine_id,)).fetchone()
                    current = self._decode(engine_id, row[0])[1] if row else None
                if (current is None or current.status is not EngineAvailability.READY
                        or current.reference() != result.reference() or current.resolved_executable != executable):
                    raise EngineConfigError("The engine approval changed or was revoked. Test it again before use.")
                resolved = profile._configuration()
                actual = Path(resolved.command[0])
                matches = (actual == executable and _fingerprint(actual) == result.binary_sha256
                           and _resource_hashes(profile) == result.resource_hashes)
            except (OSError, sqlite3.Error, TypeError, KeyError, RecursionError) as error:
                raise EngineConfigError(f"Could not check the registered engine: {error}") from error
            if not matches:
                raise EngineConfigError("The registered executable or its resources changed. Test it again before use.")

        assert result.binary_sha256 is not None
        return EngineConfig(
            (str(executable), *profile.arguments), profile.display_name, profile.is_mock, profile.origin,
            registry_reference=result.reference(), verified_version=result.advertised_version,
            provenance=EngineProvenance(
                result.reference(), result.binary_sha256, result.advertised_name,
                result.advertised_author, result.advertised_version,
            ),
            approved_options=profile.configured_options, before_launch=recheck,
        )

    def verified_configuration(self, engine_id: str) -> EngineConfig:
        """Recheck identity now as well as before any subsequent process launch."""
        config = self.launch_configuration(engine_id)
        assert config.before_launch is not None
        config.before_launch()
        return config
