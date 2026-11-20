"""SQLite user database: saved games, puzzle progress, statistics.

Safety rules
------------
* Schema version lives in ``PRAGMA user_version``; migrations are ordered,
  each runs in one transaction, and an existing database is backed up
  (``*.pre-vN.bak``) before it is migrated.
* A database written by a *newer* app version is never modified.
* A corrupt file is renamed to ``*.corrupt-<timestamp>`` (never deleted) and
  a fresh database is created; the caller is told via ``recovered_from``.
* Every stored game is re-validated through the rules domain on load.
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import sqlite3
import tempfile
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..chess import ChessError, ChessGame, Move, export_pgn, parse_fen, parse_pgn, to_fen

MIGRATIONS: tuple[tuple[int, str], ...] = (
    (1, """
        CREATE TABLE games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_utc TEXT NOT NULL,
            initial_fen TEXT NOT NULL,
            moves_uci TEXT NOT NULL,
            pgn TEXT NOT NULL,
            result TEXT NOT NULL CHECK (result IN ('1-0', '0-1', '1/2-1/2', '*')),
            mode TEXT NOT NULL,
            bot_color TEXT,
            bot_name TEXT,
            bot_preset TEXT
        );
        CREATE TABLE puzzle_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id TEXT NOT NULL,
            puzzle_id TEXT NOT NULL,
            attempted_utc TEXT NOT NULL,
            solved INTEGER NOT NULL CHECK (solved IN (0, 1)),
            mistakes INTEGER NOT NULL CHECK (mistakes >= 0),
            hints_used INTEGER NOT NULL CHECK (hints_used >= 0),
            duration_ms INTEGER
        );
    """),
    (2, """
        CREATE INDEX idx_attempts_puzzle ON puzzle_attempts (pack_id, puzzle_id);
        CREATE VIEW puzzle_progress AS
            SELECT pack_id, puzzle_id,
                   COUNT(*) AS attempts,
                   MAX(solved) AS solved,
                   SUM(CASE WHEN solved = 1 AND mistakes = 0 AND hints_used = 0 THEN 1 ELSE 0 END) AS clean_solves,
                   MIN(CASE WHEN solved = 1 THEN duration_ms END) AS best_duration_ms,
                   MAX(attempted_utc) AS last_attempt_utc
            FROM puzzle_attempts GROUP BY pack_id, puzzle_id;
    """),
)
SCHEMA_VERSION = MIGRATIONS[-1][0]


class StorageError(RuntimeError):
    """The database cannot be used safely."""


class _CorruptDatabase(sqlite3.DatabaseError):
    """An integrity check found damaged database data."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


@dataclass(frozen=True, slots=True)
class SavedGame:
    id: int
    created_utc: str
    initial_fen: str
    moves: tuple[Move, ...]
    pgn: str
    result: str
    mode: str
    bot_color: str | None
    bot_name: str | None
    bot_preset: str | None
    pgn_tags: tuple[tuple[str, str], ...] = ()

    def to_game(self) -> ChessGame:
        game = ChessGame(parse_fen(self.initial_fen))
        for move in self.moves:
            game.play(move)
        game.record_result(self.result)
        return game


@dataclass(frozen=True, slots=True)
class PuzzleProgress:
    pack_id: str
    puzzle_id: str
    attempts: int
    solved: bool
    clean_solves: int
    best_duration_ms: int | None
    last_attempt_utc: str


@dataclass(frozen=True, slots=True)
class Statistics:
    games_saved: int
    puzzles_attempted: int
    puzzles_solved: int
    puzzles_clean: int


class Database:
    def __init__(self, connection: sqlite3.Connection, path: Path, recovered_from: Path | None,
                 migration_backup: Path | None) -> None:
        self._conn = connection
        self.path = path
        self.recovered_from = recovered_from
        self.migration_backup = migration_backup

    # ----- lifecycle ---------------------------------------------------
    @classmethod
    def open(cls, path: Path) -> Database:
        try:
            return cls._open(Path(path))
        except (OSError, sqlite3.Error) as error:
            raise StorageError(f"Cannot open database {path}: {error}") from error

    @classmethod
    def _open(cls, path: Path) -> Database:
        path.parent.mkdir(parents=True, exist_ok=True)
        recovered_from: Path | None = None
        existed = path.exists() and path.stat().st_size > 0
        try:
            conn = cls._connect_checked(path)
        except sqlite3.DatabaseError as error:
            code = getattr(error, "sqlite_errorcode", 0)
            if not isinstance(error, _CorruptDatabase) and (code & 0xFF) not in (
                sqlite3.SQLITE_CORRUPT, sqlite3.SQLITE_NOTADB,
            ):
                raise
            recovered_from = path.with_name(f"{path.name}.corrupt-{_stamp()}")
            path.rename(recovered_from)
            for suffix in ("-journal", "-wal", "-shm"):
                side = path.with_name(path.name + suffix)
                if side.exists():
                    side.rename(recovered_from.with_name(recovered_from.name + suffix))
            existed = False
            conn = cls._connect_checked(path)
        try:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version > SCHEMA_VERSION:
                raise StorageError(
                    f"Database schema v{version} is newer than this app supports (v{SCHEMA_VERSION})."
                )
            backup_path = None
            if existed and version < SCHEMA_VERSION:
                backup_path = path.with_name(f"{path.name}.pre-v{SCHEMA_VERSION}-{_stamp()}.bak")
                cls._copy(conn, backup_path)
            cls._migrate(conn, version)
        except BaseException:
            conn.close()
            raise
        return cls(conn, path, recovered_from, backup_path)

    @staticmethod
    def _connect_checked(path: Path, *, read_only: bool = False) -> sqlite3.Connection:
        target = f"{path.resolve().as_uri()}?mode=ro" if read_only else path
        conn = sqlite3.connect(target, uri=read_only, isolation_level=None)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            status = conn.execute("PRAGMA quick_check").fetchone()[0]
            if status != "ok":
                raise _CorruptDatabase(f"quick_check failed: {status}")
        except sqlite3.DatabaseError:
            conn.close()
            raise
        return conn

    @staticmethod
    def _migrate(conn: sqlite3.Connection, current: int) -> None:
        for version, script in MIGRATIONS:
            if version <= current:
                continue
            statements = [s.strip() for s in script.split(";") if s.strip()]
            conn.execute("BEGIN IMMEDIATE")
            try:
                for statement in statements:
                    conn.execute(statement)
                conn.execute(f"PRAGMA user_version = {int(version)}")
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise

    @staticmethod
    def _copy(conn: sqlite3.Connection, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=f".{destination.name}.", delete=False) as handle:
            tmp = Path(handle.name)
        try:
            with closing(sqlite3.connect(tmp)) as target:
                conn.backup(target)
            tmp.replace(destination)
        finally:
            tmp.unlink(missing_ok=True)

    @property
    def schema_version(self) -> int:
        return self._conn.execute("PRAGMA user_version").fetchone()[0]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Database:
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def backup(self, destination: Path) -> Path:
        """Consistent online copy via the SQLite backup API (atomic rename)."""
        destination = Path(destination)
        if destination.exists() and destination.samefile(self.path):
            raise StorageError("The active database cannot be its own backup.")
        self._copy(self._conn, destination)
        return destination

    def restore(self, source: Path) -> Path:
        """Validate and migrate a backup before replacing live data."""
        source = Path(source)
        try:
            with closing(self._connect_checked(source, read_only=True)) as candidate:
                version = candidate.execute("PRAGMA user_version").fetchone()[0]
                if not 1 <= version <= SCHEMA_VERSION:
                    raise StorageError(f"Backup {source} has unsupported schema v{version}.")
                with tempfile.TemporaryDirectory(prefix=".restore-", dir=self.path.parent) as directory:
                    with closing(sqlite3.connect(Path(directory) / "staged.sqlite3", isolation_level=None)) as staged:
                        candidate.backup(staged)
                        self._migrate(staged, version)
                        staged.execute("SELECT id, created_utc, initial_fen, moves_uci, pgn, result, mode, "
                                       "bot_color, bot_name, bot_preset FROM games LIMIT 0")
                        staged.execute("SELECT id, pack_id, puzzle_id, attempted_utc, solved, mistakes, "
                                       "hints_used, duration_ms FROM puzzle_attempts LIMIT 0")
                        staged.execute("SELECT pack_id, puzzle_id, attempts, solved, clean_solves, "
                                       "best_duration_ms, last_attempt_utc FROM puzzle_progress LIMIT 0")
                        safety = self.path.with_name(f"{self.path.name}.pre-restore-{_stamp()}.bak")
                        self._copy(self._conn, safety)
                        staged.backup(self._conn)
        except (OSError, sqlite3.Error) as error:
            raise StorageError(f"Cannot restore backup {source}: {error}") from error
        return safety

    # ----- games -------------------------------------------------------
    def save_game(
        self,
        game: ChessGame,
        *,
        mode: str,
        bot_color: str | None = None,
        bot_name: str | None = None,
        bot_preset: str | None = None,
        headers: dict[str, str] | None = None,
        result: str | None = None,
    ) -> int:
        pgn = export_pgn(game, headers, result)
        result = pgn.rsplit(" ", 1)[-1]
        cursor = self._conn.execute(
            "INSERT INTO games (created_utc, initial_fen, moves_uci, pgn, result, mode, bot_color, bot_name, bot_preset)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (_now(), to_fen(game.initial_state), " ".join(m.to_uci() for m in game.moves), pgn, result,
             mode, bot_color, bot_name, bot_preset),
        )
        return int(cursor.lastrowid)

    def load_game(self, game_id: int) -> SavedGame:
        row = self._conn.execute(
            "SELECT id, created_utc, initial_fen, moves_uci, pgn, result, mode, bot_color, bot_name, bot_preset"
            " FROM games WHERE id = ?", (game_id,)
        ).fetchone()
        if row is None:
            raise StorageError(f"No saved game with id {game_id}.")
        try:
            moves = tuple(Move.from_uci(token) for token in row[3].split())
            pgn = parse_pgn(row[4])
            saved = SavedGame(row[0], row[1], row[2], moves, *row[4:], pgn_tags=pgn.tags)
            if (pgn.moves != saved.moves or pgn.initial_state != parse_fen(saved.initial_fen)
                    or pgn.result != saved.result):
                raise StorageError(f"Saved game {game_id}: PGN and stored game data disagree.")
        except (ChessError, AttributeError, TypeError) as error:
            raise StorageError(f"Saved game {game_id} failed validation: {error}") from error
        return saved

    def list_games(self) -> list[tuple[int, str, str, str]]:
        return [tuple(r) for r in self._conn.execute(
            "SELECT id, created_utc, result, mode FROM games ORDER BY id DESC"
        )]

    def delete_game(self, game_id: int) -> None:
        self._conn.execute("DELETE FROM games WHERE id = ?", (game_id,))

    def import_pgn(self, text: str, *, mode: str = "imported") -> int:
        document = parse_pgn(text)  # validates every move
        tags = {k: v for k, v in document.tags if k not in ("SetUp", "FEN", "Result")}
        return self.save_game(document.new_game(), mode=mode, headers=tags, result=document.result)

    def export_pgn(self, game_ids: list[int] | None = None) -> str:
        ids = game_ids if game_ids is not None else [r[0] for r in reversed(self.list_games())]
        return "\n\n".join(self.load_game(i).pgn for i in ids) + ("\n" if ids else "")

    # ----- puzzles -----------------------------------------------------
    def record_puzzle_attempt(
        self, pack_id: str, puzzle_id: str, *, solved: bool, mistakes: int, hints_used: int,
        duration_ms: int | None,
    ) -> None:
        self._conn.execute(
            "INSERT INTO puzzle_attempts (pack_id, puzzle_id, attempted_utc, solved, mistakes, hints_used, duration_ms)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (pack_id, puzzle_id, _now(), int(solved), mistakes, hints_used, duration_ms),
        )

    def puzzle_progress(self, pack_id: str, puzzle_id: str) -> PuzzleProgress | None:
        row = self._conn.execute(
            "SELECT pack_id, puzzle_id, attempts, solved, clean_solves, best_duration_ms, last_attempt_utc"
            " FROM puzzle_progress WHERE pack_id = ? AND puzzle_id = ?", (pack_id, puzzle_id)
        ).fetchone()
        if row is None:
            return None
        return PuzzleProgress(row[0], row[1], row[2], bool(row[3]), row[4], row[5], row[6])

    def solved_puzzle_ids(self, pack_id: str) -> set[str]:
        return {r[0] for r in self._conn.execute(
            "SELECT puzzle_id FROM puzzle_progress WHERE pack_id = ? AND solved = 1", (pack_id,)
        )}

    def statistics(self) -> Statistics:
        games = self._conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
        attempted, solved, clean = self._conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(solved), 0), COALESCE(SUM(clean_solves > 0), 0) FROM puzzle_progress"
        ).fetchone()
        return Statistics(games, attempted, solved, clean)
