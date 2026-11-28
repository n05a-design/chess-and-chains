"""Portable copies and staged restoration of the local data profile.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
import os
import re
import sqlite3
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from uuid import uuid4
from zipfile import BadZipFile, ZIP_DEFLATED, ZIP_STORED, ZipFile
from zlib import error as CompressionError

from ..puzzles import DEMO_PACK_ID, PackError, PackLibrary
from .database import Database, StorageError
from .exchange import write_atomic_export
from .paths import DataLayout
from .profile_lock import acquire_profile_lock
from .settings import Settings, decode_settings, save_settings

BUNDLE_SCHEMA = 1
MANIFEST = "manifest.json"
DATABASE = "games.sqlite3"
SETTINGS = "settings.json"
LIMITS = {MANIFEST: 128 * 1024, DATABASE: 1024 * 1024 * 1024, SETTINGS: 128 * 1024}
RESTORE_JOURNAL = ".profile-restore.json"
RESTORE_SCHEMA = 1
_RESTORE_PHASES = ("BACKUP_DURABLE", "APPLYING", "DATABASE_APPLIED", "SETTINGS_APPLIED", "COMMITTED", "ROLLING_BACK")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_TRANSACTION_ID = re.compile(r"[0-9a-f]{32}")
PACK_REFERENCE = re.compile(r"[a-z0-9][a-z0-9-]{1,63}")


@dataclass(frozen=True, slots=True)
class BackupRestoration:
    recovery_bundle: Path
    missing_packs: tuple[str, ...]


def _read_settings(path: Path) -> Settings:
    try:
        with path.open("rb") as handle:
            data = handle.read(LIMITS[SETTINGS] + 1)
    except FileNotFoundError:
        return Settings()
    if len(data) > LIMITS[SETTINGS]:
        raise StorageError("Settings exceed the backup size limit.")
    return decode_settings(data.decode("utf-8"))


def _pack_ids(layout: DataLayout, settings: Settings) -> tuple[str, ...]:
    references = set(PackLibrary(layout.packs).ids())
    selected = settings.last_pack_id
    if selected not in (None, DEMO_PACK_ID):
        references.add(selected)
    return tuple(sorted(_validate_packs(list(references))))


def _validate_packs(values: object) -> tuple[str, ...]:
    if (not isinstance(values, list) or len(values) > 1000
            or any(not isinstance(item, str) or not PACK_REFERENCE.fullmatch(item) for item in values)
            or len(set(values)) != len(values)):
        raise StorageError("Invalid backup puzzle pack references.")
    return tuple(values)


def _write_bundle(database: Database, layout: DataLayout, settings: Settings, destination: Path) -> Path:
    reserved = (layout.database, layout.settings, layout.engine_registry, layout.analysis_cache,
                layout.root / RESTORE_JOURNAL, layout.root / ".profile-lock.sqlite3")
    if destination.resolve() in {path.resolve() for path in reserved}:
        raise StorageError("A backup cannot replace the active database or settings.")
    protected = (layout.packs.resolve(), layout.root / "puzzle_packs-catalogs")
    if any(destination.resolve().is_relative_to(path) for path in protected):
        raise StorageError("A backup cannot replace an installed puzzle pack.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".chess-backup-", dir=destination.parent) as temporary:
        directory = Path(temporary)
        paths = {DATABASE: database.backup(directory / DATABASE), SETTINGS: directory / SETTINGS}
        save_settings(paths[SETTINGS], settings)
        checksums = {}
        for name, path in paths.items():
            if path.stat().st_size > LIMITS[name]:
                raise StorageError(f"{name} exceeds the backup size limit.")
            with path.open("rb") as handle:
                checksums[name] = hashlib.file_digest(handle, "sha256").hexdigest()
        manifest = {"schema": BUNDLE_SCHEMA, "profile": "local", "sha256": checksums,
                    "puzzle_packs": list(_pack_ids(layout, settings))}
        archive = directory / "profile.zip"
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
            bundle.writestr(MANIFEST, json.dumps(manifest, sort_keys=True))
            for name, path in paths.items():
                bundle.write(path, name)
        archive.chmod(0o600)
        with archive.open("r+b") as handle:
            os.fsync(handle.fileno())
        archive.replace(destination)
    return destination


def write_backup(layout: DataLayout, destination: Path) -> Path:
    """Write a versioned offline copy. Close the desktop app before using the CLI."""
    try:
        with closing(acquire_profile_lock(layout.root, exclusive=True)):
            _recover_pending_locked(layout)
            settings = _read_settings(layout.settings)
            with Database.open(layout.database) as db:
                return _write_bundle(db, layout, settings, destination)
    except (OSError, ValueError, TypeError, RecursionError, PackError) as error:
        raise StorageError(f"Cannot create profile backup: {error}") from error


def _read_bundle(source: Path, directory: Path) -> tuple[Settings, tuple[str, ...]]:
    if not source.is_file() or source.stat().st_size > sum(LIMITS.values()) + 1024 * 1024:
        raise StorageError("Choose a regular profile backup within the size limit.")
    with ZipFile(source) as bundle:
        entries = bundle.infolist()
        if len(entries) != len(LIMITS) or {entry.filename for entry in entries} != LIMITS.keys():
            raise StorageError("Profile backup contains unexpected or missing files.")
        for entry in entries:
            if (entry.file_size > LIMITS[entry.filename] or entry.flag_bits & 1
                    or entry.compress_type not in (ZIP_STORED, ZIP_DEFLATED)):
                raise StorageError(f"Invalid backup member: {entry.filename}.")
        manifest = json.loads(bundle.read(MANIFEST))
        if (not isinstance(manifest, dict) or type(manifest.get("schema")) is not int
                or manifest["schema"] != BUNDLE_SCHEMA or manifest.get("profile") != "local"):
            raise StorageError("Unsupported profile backup schema.")
        references = _validate_packs(manifest.get("puzzle_packs"))
        hashes = manifest.get("sha256")
        if not isinstance(hashes, dict) or hashes.keys() != {DATABASE, SETTINGS}:
            raise StorageError("Missing backup checksums.")
        for name in (DATABASE, SETTINGS):
            digest = hashlib.sha256()
            total = 0
            with bundle.open(name) as incoming, (directory / name).open("wb") as outgoing:
                while chunk := incoming.read(1024 * 1024):
                    total += len(chunk)
                    if total > LIMITS[name]:
                        raise StorageError(f"{name} exceeds the backup size limit.")
                    outgoing.write(chunk)
                    digest.update(chunk)
            if digest.hexdigest() != hashes[name]:
                raise StorageError(f"Backup integrity check failed for {name}.")
    return _read_settings(directory / SETTINGS), references


def _file_hash(path: Path) -> str | None:
    try:
        with path.open("rb") as handle:
            return hashlib.file_digest(handle, "sha256").hexdigest()
    except FileNotFoundError:
        return None


def _profile_hashes(layout: DataLayout) -> dict[str, str | None]:
    return {DATABASE: _file_hash(layout.database), SETTINGS: _file_hash(layout.settings)}


def _sync_directory(path: Path) -> None:
    if os.name != "nt":
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _record_phase(journal: Path, record: dict, phase: str, *, decision: str) -> None:
    record["phase"] = phase
    record["decision"] = decision
    write_atomic_export(journal, json.dumps(record, sort_keys=True).encode("utf-8"))
    _sync_directory(journal.parent)


def _read_journal(journal: Path) -> dict:
    if journal.is_symlink():
        raise StorageError("Restore journal must be a local file.")
    with journal.open("rb") as handle:
        data = handle.read(16385)
    if len(data) > 16384:
        raise StorageError("Restore journal exceeds its size limit.")
    record = json.loads(data)
    if (not isinstance(record, dict) or type(record.get("schema")) is not int
            or record["schema"] != RESTORE_SCHEMA or record.get("phase") not in _RESTORE_PHASES
            or not isinstance(record.get("id"), str) or not _TRANSACTION_ID.fullmatch(record["id"])):
        raise StorageError("Unsupported or invalid restore journal.")
    for key in ("incoming", "recovery_sha256"):
        value = record.get(key)
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise StorageError("Invalid restore journal checksum.")
    for key in ("before", "after"):
        hashes = record.get(key)
        if hashes is None and key == "after" and record["phase"] != "COMMITTED":
            continue
        if (not isinstance(hashes, dict) or hashes.keys() != {DATABASE, SETTINGS}
                or any(value is not None and (not isinstance(value, str) or not _SHA256.fullmatch(value))
                       for value in hashes.values())):
            raise StorageError("Invalid restore journal file identities.")
    return record


def _recover_pending_locked(layout: DataLayout) -> bool:
    journal = layout.root / RESTORE_JOURNAL
    if not journal.exists() and not journal.is_symlink():
        return False
    try:
        record = _read_journal(journal)
        before = record["before"]
        actual = _profile_hashes(layout)
        if record["phase"] == "COMMITTED":
            if actual != record["after"]:
                raise StorageError("The committed profile differs from its restore journal.")
        else:
            recovery = layout.backups / f"pre-profile-restore-{record['id']}.zip"
            if (recovery.is_symlink() or not recovery.is_file()
                    or _file_hash(recovery) != record["recovery_sha256"]):
                raise StorageError("The pre-restore safety bundle is missing or changed.")
            if actual != before:
                _record_phase(journal, record, "ROLLING_BACK", decision="restore-previous-profile")
                with tempfile.TemporaryDirectory(prefix=".chess-recover-", dir=layout.root) as temporary:
                    saved = Path(temporary)
                    _read_bundle(recovery, saved)
                    with Database.open(layout.database) as db:
                        db.restore(saved / DATABASE)
                    if before[SETTINGS] is None:
                        layout.settings.unlink(missing_ok=True)
                    else:
                        settings_bytes = (saved / SETTINGS).read_bytes()
                        write_atomic_export(layout.settings, settings_bytes)
                    _sync_directory(layout.root)
                    with Database.open(layout.database) as db:
                        if db.schema_version < 1:
                            raise StorageError("Restored SQLite data has no supported schema.")
            # A committed recovery is also restart-safe if cleanup is interrupted.
            record["after"] = _profile_hashes(layout)
            _record_phase(journal, record, "COMMITTED", decision="previous-profile-retained")
        journal.unlink()
        _sync_directory(layout.root)
        return True
    except (OSError, ValueError, TypeError, KeyError, BadZipFile, CompressionError, PackError, StorageError) as error:
        raise StorageError(f"Profile recovery stopped. Preserve {journal.name} and the recovery bundle. {error}") from error


def open_profile(layout: DataLayout) -> sqlite3.Connection:
    """Finish recovery before handing a shared profile lease to the desktop app."""
    journal = layout.root / RESTORE_JOURNAL
    while True:
        lock = acquire_profile_lock(layout.root)
        if not journal.exists() and not journal.is_symlink():
            return lock
        lock.close()
        with closing(acquire_profile_lock(layout.root, exclusive=True)):
            _recover_pending_locked(layout)


def restore_backup(layout: DataLayout, source: Path) -> BackupRestoration:
    """Validate, journal and install one complete local profile."""
    try:
        with closing(acquire_profile_lock(layout.root, exclusive=True)):
            _recover_pending_locked(layout)
            return _restore_locked(layout, source)
    except (OSError, ValueError, TypeError, RecursionError, BadZipFile, CompressionError, PackError) as error:
        raise StorageError(f"Cannot restore profile backup: {error}") from error


def _restore_locked(layout: DataLayout, source: Path) -> BackupRestoration:
    with tempfile.TemporaryDirectory(prefix=".chess-restore-", dir=layout.root) as temporary:
        directory = Path(temporary)
        if not source.is_file():
            raise StorageError("Choose a regular profile backup file.")
        if source.resolve() == layout.database.resolve():
            raise StorageError("The active database cannot be its own backup.")
        with source.open("rb") as handle:
            legacy = handle.read(16) == b"SQLite format 3\0"
        current = _read_settings(layout.settings)
        if legacy:
            if source.stat().st_size > LIMITS[DATABASE]:
                raise StorageError("The database backup exceeds the size limit.")
            candidate = source
            restored = current
            missing = ()
        else:
            incoming, pack_refs = _read_bundle(source, directory)
            candidate = directory / DATABASE
            restored = replace(incoming, engine_path=current.engine_path, engine_profile_id=current.engine_profile_id,
                               registered_engine_paths=current.registered_engine_paths, development_mock=current.development_mock)
            missing = tuple(sorted(set(pack_refs) - set(PackLibrary(layout.packs).ids())))
        transaction_id = uuid4().hex
        recovery = layout.backups / f"pre-profile-restore-{transaction_id}.zip"
        journal = layout.root / RESTORE_JOURNAL
        with Database.open(layout.database) as db:
            _write_bundle(db, layout, current, recovery)
        _sync_directory(recovery.parent)
        _sync_directory(layout.root)
        record = {"schema": RESTORE_SCHEMA, "id": transaction_id, "incoming": _file_hash(source),
                  "recovery_sha256": _file_hash(recovery), "before": _profile_hashes(layout), "after": None}
        _record_phase(journal, record, "BACKUP_DURABLE", decision="apply")
        try:
            _record_phase(journal, record, "APPLYING", decision="apply")
            with Database.open(layout.database) as db:
                db.restore(candidate)
            _record_phase(journal, record, "DATABASE_APPLIED", decision="apply")
            if not legacy:
                save_settings(layout.settings, restored)
            _record_phase(journal, record, "SETTINGS_APPLIED", decision="apply")
            record["after"] = _profile_hashes(layout)
            _record_phase(journal, record, "COMMITTED", decision="incoming-profile-installed")
        except (OSError, ValueError, StorageError) as error:
            _recover_pending_locked(layout)
            raise StorageError(f"Restore failed; database rolled back. Recovery bundle: {recovery}. {error}") from error
        journal.unlink()
        _sync_directory(layout.root)
        return BackupRestoration(recovery, missing)
