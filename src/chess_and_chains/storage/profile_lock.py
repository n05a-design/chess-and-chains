"""OS-backed shared desktop leases and exclusive profile maintenance.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .database import StorageError


def acquire_profile_lock(root: Path, *, exclusive: bool = False) -> sqlite3.Connection:
    """Hold a rollback-mode SQLite transaction for the lifetime of the lease."""
    connection = None
    try:
        connection = sqlite3.connect(root / ".profile-lock.sqlite3", timeout=0.25, isolation_level=None)
        if connection.execute("PRAGMA journal_mode").fetchone()[0].lower() != "delete":
            raise StorageError("The profile lock is not in rollback journal mode.")
        if connection.execute("PRAGMA user_version").fetchone()[0] == 0:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("PRAGMA user_version = 1")
            connection.execute("COMMIT")
        connection.execute("BEGIN EXCLUSIVE" if exclusive else "BEGIN")
        connection.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
    except (sqlite3.Error, StorageError) as error:
        if connection is not None:
            connection.close()
        raise StorageError("Profile locked or unavailable. Close other Chess & Chains windows and try again.") from error
    return connection
