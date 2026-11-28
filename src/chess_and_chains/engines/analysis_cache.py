"""Bounded rebuildable storage for individual completed analysis results.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING

from ..chess import ChessGame

if TYPE_CHECKING:
    from .analysis import AnalysisConfiguration, AnalysisResult

CACHE_SCHEMA = 1
MAX_ROWS = 256
MAX_BYTES = 128 * 1024


class PersistentAnalysisCache:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _open(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=0.25)
        try:
            schema = connection.execute("PRAGMA user_version").fetchone()[0]
            if schema not in (0, CACHE_SCHEMA):
                raise ValueError("Unsupported analysis-cache schema.")
            if schema == 0:
                with connection:
                    connection.execute("""
                        CREATE TABLE IF NOT EXISTS results (
                            key TEXT PRIMARY KEY, payload TEXT NOT NULL, sha256 TEXT NOT NULL,
                            touched INTEGER NOT NULL
                        )
                    """)
                    connection.execute(f"PRAGMA user_version = {CACHE_SCHEMA}")
        except BaseException:
            connection.close()
            raise
        return connection

    @staticmethod
    def key(fen: str, history: tuple[str, ...], configuration: AnalysisConfiguration, **extra) -> str:
        payload = json.dumps(
            [CACHE_SCHEMA, fen, history, asdict(configuration), extra],
            sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        )
        return hashlib.sha256(payload.encode("ascii")).hexdigest()

    def load(
        self, key: str, game: ChessGame, configuration: AnalysisConfiguration,
    ) -> AnalysisResult | None:
        from .analysis_report import decode_position

        try:
            with closing(self._open()) as connection, connection:
                row = connection.execute(
                    "SELECT payload, sha256 FROM results WHERE key = ? AND length(payload) <= ?", (key, MAX_BYTES),
                ).fetchone()
                if row is None:
                    return None
                try:
                    payload, digest = row
                    encoded = payload.encode("utf-8")
                    if len(encoded) > MAX_BYTES or hashlib.sha256(encoded).hexdigest() != digest:
                        raise ValueError("Incorrect cached analysis checksum.")
                    result = decode_position(json.loads(payload), game)
                    if result.configuration != configuration or not result.lines or result.best_move is None:
                        raise ValueError("Incomplete or incompatible cached analysis.")
                except (ValueError, TypeError, AttributeError, KeyError, RecursionError):
                    connection.execute("DELETE FROM results WHERE key = ?", (key,))
                    return None
                connection.execute("UPDATE results SET touched = CAST(strftime('%s','now') AS INTEGER) WHERE key = ?", (key,))
                return result
        except (sqlite3.Error, ValueError):
            return None

    def store(self, key: str, result: AnalysisResult) -> None:
        from .analysis_report import encode_position

        payload = json.dumps(encode_position(result), ensure_ascii=True, separators=(",", ":"))
        data = payload.encode("ascii")
        if len(data) > MAX_BYTES:
            return
        try:
            with closing(self._open()) as connection, connection:
                connection.execute(
                    "INSERT OR REPLACE INTO results(key, payload, sha256, touched) VALUES (?, ?, ?, CAST(strftime('%s','now') AS INTEGER))",
                    (key, payload, hashlib.sha256(data).hexdigest()),
                )
                connection.execute(
                    "DELETE FROM results WHERE key IN (SELECT key FROM results ORDER BY touched DESC, rowid DESC "
                    "LIMIT -1 OFFSET ?)", (MAX_ROWS,),
                )
        except (sqlite3.Error, ValueError):
            pass  # A rebuildable cache must not prevent a completed analysis.
