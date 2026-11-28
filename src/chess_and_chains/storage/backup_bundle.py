"""Portable copies and staged restoration of the local data profile.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from uuid import uuid4
from zipfile import BadZipFile, ZIP_DEFLATED, ZIP_STORED, ZipFile
from zlib import error as CompressionError

from ..puzzles import DEMO_PACK_ID, PackError, PackLibrary
from .database import Database, StorageError
from .paths import DataLayout
from .settings import Settings, decode_settings, save_settings

BUNDLE_SCHEMA = 1
MANIFEST = "manifest.json"
DATABASE = "games.sqlite3"
SETTINGS = "settings.json"
LIMITS = {MANIFEST: 128 * 1024, DATABASE: 1024 * 1024 * 1024, SETTINGS: 128 * 1024}
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
    if destination.resolve() in (layout.database.resolve(), layout.settings.resolve()):
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


def restore_backup(layout: DataLayout, source: Path) -> BackupRestoration:
    """Validate an archive before installing it and keep a complete recovery copy."""
    try:
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
                                   registered_engine_paths=current.registered_engine_paths)
                missing = tuple(sorted(set(pack_refs) - set(PackLibrary(layout.packs).ids())))
            recovery = layout.backups / f"pre-profile-restore-{uuid4().hex}.zip"
            with Database.open(layout.database) as db:
                _write_bundle(db, layout, current, recovery)
                previous_database = db.restore(candidate)
                if legacy:
                    return BackupRestoration(recovery, missing)
                try:
                    save_settings(layout.settings, restored)
                except (OSError, ValueError) as error:
                    try:
                        db.restore(previous_database)
                    except StorageError as rollback_error:
                        raise StorageError(f"Rollback failed. Recovery bundle: {recovery}. {rollback_error}") from error
                    raise StorageError(f"Settings were not restored; database rolled back. Recovery bundle: {recovery}.") from error
            return BackupRestoration(recovery, missing)
    except (OSError, ValueError, TypeError, RecursionError, BadZipFile, CompressionError, PackError) as error:
        raise StorageError(f"Cannot restore profile backup: {error}") from error
