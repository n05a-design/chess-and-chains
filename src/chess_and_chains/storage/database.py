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
import unicodedata
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..chess import ChessError, ChessGame, Color, DrawClaim, Move, export_pgn, parse_fen, parse_pgn, to_fen
from ..chess.notation import read_pgn_headers
from ..engines.analysis import AnalysisProgress
from ..engines.analysis_report import MAX_REPORT_BYTES, decode_report, encode_report
from ..game.clock import TimeControl
from ..game.session import GameSessionSnapshot, MAX_SNAPSHOT_BYTES, SessionLifecycle
from ..puzzles import load_demo_pack
from ..puzzles.training import (
    DEMO_MATE_CHAIN, MAX_TRAINING_CHECKPOINT_BYTES, AttemptStatus, TrainingAttempt, TrainingCandidate,
    TrainingCheckpoint, demo_chain_catalog, summarize_attempts,
)
from .analysis_candidate import AnalysisTrainingCandidate, MAX_CANDIDATE_BYTES
from .exchange import write_atomic_export

MAX_PGN_FILE_BYTES = 256 * 1024
MAX_PGN_FILE_PLIES = 512

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
    (3, """
        ALTER TABLE games ADD COLUMN resigned_by TEXT CHECK (resigned_by IN ('w', 'b'));
        ALTER TABLE games ADD COLUMN draw_claim TEXT CHECK (
            draw_claim IS NULL OR (resigned_by IS NULL AND draw_claim IN ('THREEFOLD_REPETITION', 'FIFTY_MOVE_RULE'))
        );
        ALTER TABLE games ADD COLUMN declared_move TEXT CHECK (declared_move IS NULL OR draw_claim IS NOT NULL);
    """),
    (4, """
        ALTER TABLE games ADD COLUMN engine_ref TEXT;
        ALTER TABLE games ADD COLUMN profile_id TEXT NOT NULL DEFAULT 'local' CHECK (profile_id = 'local');
        ALTER TABLE puzzle_attempts ADD COLUMN profile_id TEXT NOT NULL DEFAULT 'local' CHECK (profile_id = 'local');
        CREATE TABLE training_candidates (
            source_game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
            ply INTEGER NOT NULL CHECK (ply >= 0),
            fen TEXT NOT NULL,
            PRIMARY KEY (source_game_id, ply)
        );
        CREATE TABLE active_session (
            slot INTEGER PRIMARY KEY CHECK (slot = 1),
            snapshot TEXT NOT NULL CHECK (length(CAST(snapshot AS BLOB)) <= 262144)
        );
    """),
    (5, """
        CREATE TABLE analysis_reports (
            run_id TEXT PRIMARY KEY NOT NULL,
            source_game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
            created_utc TEXT NOT NULL,
            engine_name TEXT NOT NULL,
            position_count INTEGER NOT NULL CHECK (position_count BETWEEN 1 AND 513),
            report TEXT NOT NULL CHECK (length(CAST(report AS BLOB)) <= 4194304)
        );
        CREATE INDEX analysis_reports_game ON analysis_reports(source_game_id);
        ALTER TABLE puzzle_attempts ADD COLUMN attempt_uid TEXT;
        CREATE UNIQUE INDEX puzzle_attempt_uid ON puzzle_attempts(attempt_uid);
        CREATE TABLE training_checkpoints (
            chain_id TEXT PRIMARY KEY NOT NULL,
            revision INTEGER NOT NULL CHECK (revision > 0),
            hint_stage INTEGER NOT NULL CHECK (hint_stage BETWEEN 0 AND 2),
            payload TEXT NOT NULL CHECK (length(CAST(payload AS BLOB)) <= 65536)
        );
    """),
    (6, """
        ALTER TABLE games ADD COLUMN session_snapshot TEXT
            CHECK (session_snapshot IS NULL OR length(CAST(session_snapshot AS BLOB)) <= 262144);
    """),
    (7, """
        ALTER TABLE games ADD COLUMN favorite INTEGER NOT NULL DEFAULT 0 CHECK (favorite IN (0, 1));
        CREATE TABLE game_tags (
            game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
            tag TEXT NOT NULL CHECK (length(tag) BETWEEN 1 AND 64),
            PRIMARY KEY (game_id, tag)
        ) WITHOUT ROWID;
        CREATE INDEX game_tags_tag ON game_tags(tag, game_id);
    """),
    (8, """
        CREATE TABLE analysis_training_candidates (
            candidate_id TEXT PRIMARY KEY,
            source_game_id INTEGER REFERENCES games(id) ON DELETE SET NULL,
            source_report_id TEXT REFERENCES analysis_reports(run_id) ON DELETE SET NULL,
            payload TEXT NOT NULL CHECK (length(CAST(payload AS BLOB)) <= 262144)
        );
        CREATE INDEX training_from_game ON analysis_training_candidates(source_game_id);
        CREATE INDEX training_from_report ON analysis_training_candidates(source_report_id);
    """),
)
SCHEMA_VERSION = MIGRATIONS[-1][0]


class StorageError(RuntimeError):
    """The database cannot be used safely."""


class SessionConflict(StorageError):
    """The active checkpoint changed since this instance last read it."""


class _CorruptDatabase(sqlite3.DatabaseError):
    """An integrity check found damaged database data."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


@dataclass(frozen=True, slots=True)
class AnalysisReportSummary:
    run_id: str
    source_game_id: int
    created_utc: str
    engine_name: str
    position_count: int


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
    resigned_by: Color | None = None
    draw_claim: DrawClaim | None = None
    declared_move: Move | None = None
    engine_ref: str | None = None
    session_snapshot: GameSessionSnapshot | None = None
    clock_annotations: tuple[int | None, ...] = ()

    @property
    def started_utc(self) -> datetime | None:
        return datetime.fromisoformat(self.session_snapshot.created_utc) if self.session_snapshot else None

    @property
    def ended_utc(self) -> datetime | None:
        snapshot = self.session_snapshot
        if snapshot is None or snapshot.lifecycle is not SessionLifecycle.FINISHED:
            return None
        return datetime.fromisoformat(snapshot.updated_utc)

    @property
    def wall_duration(self) -> timedelta | None:
        start, end = self.started_utc, self.ended_utc
        return end - start if start is not None and end is not None else None

    @property
    def timed_play_duration(self) -> timedelta | None:
        clock = self.session_snapshot.clock if self.session_snapshot else None
        return timedelta(microseconds=clock.active_ns // 1000) if clock and clock.active_ns is not None else None

    @property
    def explicit_pause_duration(self) -> timedelta | None:
        clock = self.session_snapshot.clock if self.session_snapshot else None
        return timedelta(microseconds=clock.paused_ns // 1000) if clock and clock.paused_ns is not None else None

    def to_game(self) -> ChessGame:
        game = ChessGame(parse_fen(self.initial_fen))
        with game.replay_record():
            for move in self.moves:
                game.play(move)
            if self.resigned_by is not None:
                game.resign(self.resigned_by)
            elif self.draw_claim is not None:
                game.claim_draw(self.draw_claim, self.declared_move)
        if self.session_snapshot is not None and self.result == "1/2-1/2":
            timeline = self.session_snapshot.timeline
            if timeline.agreed_draw and timeline.cursor > len(timeline.moves):
                game.agree_draw()
        game.record_result(self.result, historical=True)
        return game


@dataclass(frozen=True, slots=True)
class GameSummary:
    id: int
    created_utc: str
    result: str
    white: str
    black: str
    event: str
    favorite: bool = False


@dataclass(frozen=True, slots=True)
class ArchiveLabels:
    favorite: bool
    tags: tuple[str, ...]


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
class PuzzleAttempt:
    solved: bool
    mistakes: int
    hints_used: int
    duration_ms: int | None


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
                if conn.execute("PRAGMA user_version").fetchone()[0] < version:
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
        """Validate and migrate a backup, including its game records, before replacing live data."""
        source = Path(source)
        try:
            with closing(self._connect_checked(source, read_only=True)) as candidate:
                version = candidate.execute("PRAGMA user_version").fetchone()[0]
                if not 1 <= version <= SCHEMA_VERSION:
                    raise StorageError(f"Backup {source} has unsupported schema v{version}.")
                with tempfile.TemporaryDirectory(prefix=".restore-", dir=self.path.parent) as directory:
                    staged_path = Path(directory) / "staged.sqlite3"
                    with closing(sqlite3.connect(staged_path, isolation_level=None)) as staged:
                        candidate.backup(staged)
                        self._migrate(staged, version)
                        staged.execute("SELECT id, created_utc, initial_fen, moves_uci, pgn, result, mode, "
                                       "bot_color, bot_name, bot_preset, resigned_by, draw_claim, declared_move, engine_ref, profile_id, session_snapshot, favorite FROM games LIMIT 0")
                        staged.execute("SELECT id, pack_id, puzzle_id, attempted_utc, solved, mistakes, "
                                       "hints_used, duration_ms FROM puzzle_attempts LIMIT 0")
                        staged.execute("SELECT pack_id, puzzle_id, attempts, solved, clean_solves, "
                                       "best_duration_ms, last_attempt_utc FROM puzzle_progress LIMIT 0")
                        staged_db = Database(staged, staged_path, recovered_from=None, migration_backup=None)
                        for (game_id,) in staged.execute("SELECT id FROM games"):
                            staged_db.load_game(game_id)
                        staged_db.load_session()
                        staged.execute("SELECT game_id, tag FROM game_tags LIMIT 0")
                        staged_db._validate_archive_labels()
                        if staged.execute("PRAGMA foreign_key_check").fetchone():
                            raise StorageError("Backup contains invalid references.")
                        for candidate in staged_db.training_candidates():
                            staged_db._validate_training_candidate(candidate)
                        for (chain_id,) in staged.execute("SELECT chain_id FROM training_checkpoints"):
                            saved = staged_db.load_training_checkpoint(chain_id)
                            if saved is None:
                                raise StorageError("Missing training checkpoint.")
                            checkpoint, _, _ = saved
                            try:
                                staged_db._validate_training_checkpoint(checkpoint)
                                for attempt in checkpoint.attempts:
                                    if attempt.counted:
                                        staged_db._verify_chain_attempt(attempt)
                            except ValueError as error:
                                raise StorageError(f"Invalid saved training chain: {error}") from error
                        for report in staged_db.analysis_reports():
                            staged_db.load_analysis_report(report.run_id)
                        staged_db.analysis_training_candidates()
                        safety = self.path.with_name(f"{self.path.name}.pre-restore-{_stamp()}.bak")
                        self._copy(self._conn, safety)
                        staged.backup(self._conn)
        except (OSError, sqlite3.Error, StorageError) as error:
            raise StorageError(f"Cannot restore backup {source}: {error}") from error
        return safety

    def save_session(self, snapshot: GameSessionSnapshot) -> None:
        payload = snapshot.encode()
        self._conn.execute(
            "INSERT INTO active_session(slot, snapshot) VALUES (1, ?) "
            "ON CONFLICT(slot) DO UPDATE SET snapshot = excluded.snapshot",
            (payload,),
        )

    def compare_and_save_session(self, snapshot: GameSessionSnapshot, expected: str | None) -> str:
        """Replace only the exact checkpoint this instance last observed."""
        payload = snapshot.encode()
        if expected is None:
            changed = self._conn.execute(
                "INSERT INTO active_session(slot, snapshot) VALUES (1, ?) ON CONFLICT(slot) DO NOTHING",
                (payload,),
            )
        else:
            changed = self._conn.execute(
                "UPDATE active_session SET snapshot = ? WHERE slot = 1 AND snapshot = ?", (payload, expected),
            )
        if changed.rowcount != 1:
            raise SessionConflict("The active game was changed by another window.")
        return payload

    def session_payload(self) -> str | None:
        row = self._conn.execute(
            "SELECT CASE WHEN length(CAST(snapshot AS BLOB)) <= ? THEN snapshot END "
            "FROM active_session WHERE slot = 1", (MAX_SNAPSHOT_BYTES,),
        ).fetchone()
        if row is None:
            return None
        if not isinstance(row[0], str):
            raise StorageError("Invalid session snapshot size or storage type.")
        return row[0]

    def load_session(self) -> tuple[GameSessionSnapshot, ChessGame] | None:
        payload = self.session_payload()
        return self.decode_session(payload) if payload is not None else None

    @staticmethod
    def decode_session(payload: str) -> tuple[GameSessionSnapshot, ChessGame]:
        try:
            snapshot = GameSessionSnapshot.decode(payload)
            return snapshot, snapshot.restore_game()
        except (ValueError, RecursionError) as error:
            raise StorageError(f"Cannot read game session: {error}") from error

    # ----- games -------------------------------------------------------
    @staticmethod
    def _validate_archive_snapshot(
        snapshot: GameSessionSnapshot, game: ChessGame, result: str, *,
        mode: str, bot_color: str | None, bot_preset: str | None, engine_ref: str | None,
    ) -> None:
        restored = snapshot.restore_game()
        bot = snapshot.setup.bot_color
        archive_mode = snapshot.setup.mode.value if bot is None else f"{snapshot.setup.mode.value}-{bot.opposite.name.lower()}"
        if (mode, bot_color, bot_preset, engine_ref) != (
            archive_mode, bot.value if bot else None, snapshot.bot_preset, snapshot.engine_ref,
        ):
            raise ValueError("Archive session differs from the recorded game setup.")
        if (restored.initial_state != game.initial_state or restored.state != game.state
                or restored.moves != game.moves or restored.outcome() != game.outcome()
                or export_pgn(restored).rsplit(maxsplit=1)[-1] != result):
            raise ValueError("Archive session differs from the recorded game.")

    def save_game(
        self,
        game: ChessGame,
        *,
        mode: str,
        bot_color: str | None = None,
        bot_name: str | None = None,
        bot_preset: str | None = None,
        engine_ref: str | None = None,
        headers: dict[str, str] | None = None,
        result: str | None = None,
        session_snapshot: GameSessionSnapshot | None = None,
        clock_annotations: tuple[int | None, ...] = (),
    ) -> int:
        outcome = game.outcome()
        has_termination = outcome.resigned_by is not None or outcome.claimed_draw is not None
        if has_termination and result is not None:
            if result == "*":
                raise ChessError("An explicit termination requires a final PGN result.")
            game.record_result(result)
        if session_snapshot is not None and session_snapshot.clock is not None:
            clock_annotations = session_snapshot.clock.move_annotations(len(game.moves))
        pgn = export_pgn(game, headers, result, clock_annotations=clock_annotations)
        result = pgn.rsplit(maxsplit=1)[-1]
        payload = None
        if session_snapshot is not None:
            payload = session_snapshot.encode()
            self._validate_archive_snapshot(
                GameSessionSnapshot.decode(payload), game, result,
                mode=mode, bot_color=bot_color, bot_preset=bot_preset, engine_ref=engine_ref,
            )
        statement = (
            "INSERT INTO games (created_utc, initial_fen, moves_uci, pgn, result, mode, bot_color, bot_name, bot_preset,"
            " resigned_by, draw_claim, declared_move, engine_ref, session_snapshot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        fields = (
            _now(), to_fen(game.initial_state), " ".join(m.to_uci() for m in game.moves), pgn, result,
            mode, bot_color, bot_name, bot_preset, outcome.resigned_by.value if outcome.resigned_by else None,
            outcome.claimed_draw.name if outcome.claimed_draw else None,
            outcome.declared_move.to_uci() if outcome.declared_move else None, engine_ref, payload,
        )
        if session_snapshot is None or session_snapshot.lifecycle is not SessionLifecycle.FINISHED:
            return int(self._conn.execute(statement, fields).lastrowid)

        # One writer at a time checks for and archives this exact finished session.
        with self._conn:
            self._conn.execute("BEGIN IMMEDIATE")
            prior = self._conn.execute(
                "SELECT id FROM games WHERE session_snapshot = ? ORDER BY id LIMIT 1", (payload,),
            ).fetchone()
            if prior is not None:
                return int(prior[0])
            return int(self._conn.execute(statement, fields).lastrowid)

    def load_game(self, game_id: int) -> SavedGame:
        row = self._conn.execute(
            "SELECT id, created_utc, initial_fen, moves_uci, pgn, result, mode, bot_color, bot_name, bot_preset,"
            " resigned_by, draw_claim, declared_move, engine_ref, session_snapshot FROM games WHERE id = ?", (game_id,)
        ).fetchone()
        if row is None:
            raise StorageError(f"No saved game with id {game_id}.")
        try:
            moves = tuple(Move.from_uci(token) for token in row[3].split())
            pgn = parse_pgn(row[4])
            resigned_by, draw_claim, declared_move, engine_ref, payload = row[10:]
            saved = SavedGame(
                row[0], row[1], row[2], moves, *row[4:10], pgn_tags=pgn.tags,
                resigned_by=Color(resigned_by) if resigned_by is not None else None,
                draw_claim=DrawClaim[draw_claim] if draw_claim is not None else None,
                declared_move=Move.from_uci(declared_move) if declared_move is not None else None,
                engine_ref=engine_ref,
                session_snapshot=GameSessionSnapshot.decode(payload) if payload is not None else None,
                clock_annotations=pgn.clock_annotations,
            )
            if (pgn.moves != saved.moves or pgn.initial_state != parse_fen(saved.initial_fen)
                    or pgn.result != saved.result):
                raise StorageError(f"Saved game {game_id}: PGN and stored game data disagree.")
            if (saved.resigned_by and saved.draw_claim) or (saved.declared_move and saved.draw_claim is None):
                raise StorageError(f"Saved game {game_id}: invalid termination metadata.")
            if saved.resigned_by or saved.draw_claim:
                if saved.result == "*":
                    raise StorageError(f"Saved game {game_id}: termination requires a final result.")
                saved.to_game()
            if saved.session_snapshot is not None:
                clock = saved.session_snapshot.clock
                if saved.clock_annotations and (clock is None
                        or clock.move_annotations(len(saved.moves)) != saved.clock_annotations):
                    raise StorageError(f"Saved game {game_id}: PGN and stored clock data disagree.")
                self._validate_archive_snapshot(
                    saved.session_snapshot, saved.to_game(), saved.result, mode=saved.mode,
                    bot_color=saved.bot_color, bot_preset=saved.bot_preset, engine_ref=saved.engine_ref,
                )
        except (ValueError, KeyError, AttributeError, TypeError, RecursionError) as error:
            raise StorageError(f"Saved game {game_id} failed validation: {error}") from error
        return saved

    def list_games(self) -> list[tuple[int, str, str, str]]:
        return [tuple(r) for r in self._conn.execute(
            "SELECT id, created_utc, result, mode FROM games ORDER BY id DESC"
        )]

    def game_summaries(
        self, *, archived_from: str | None = None, archived_before: str | None = None,
        mode: str | None = None, result: str | None = None, engine_ref: str | None = None,
        bot_preset: str | None = None, time_control: TimeControl | None = None,
        has_analysis: bool | None = None, has_training: bool | None = None,
        favorite: bool | None = None, tag: str | None = None,
    ) -> list[GameSummary]:
        query = "SELECT id, created_utc, result, pgn, favorite"
        if time_control is not None:
            query += ", session_snapshot"
        clauses = []
        parameters = []
        for field, operator, value in (
            ("created_utc", ">=", archived_from), ("created_utc", "<", archived_before),
            ("mode", "=", mode), ("result", "=", result), ("engine_ref", "=", engine_ref),
            ("bot_preset", "=", bot_preset), ("favorite", "=", favorite),
        ):
            if value is not None:
                clauses.append(f"g.{field} {operator} ?")
                parameters.append(value)
        for table, required in (("analysis_reports", has_analysis), ("training_candidates", has_training)):
            if required is not None:
                condition = f"EXISTS (SELECT 1 FROM {table} WHERE source_game_id = g.id)"
                if table == "training_candidates":
                    condition = (
                        f"({condition} OR EXISTS (SELECT 1 FROM analysis_training_candidates WHERE source_game_id = g.id))"
                    )
                clauses.append(condition if required else f"NOT {condition}")
        if tag is not None:
            clauses.append("EXISTS (SELECT 1 FROM game_tags WHERE game_id = g.id AND tag = ?)")
            parameters.append(unicodedata.normalize("NFC", tag))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        query += f" FROM games AS g{where} ORDER BY id DESC"
        summaries = []
        for game_id, created, game_result, pgn, is_favorite, *snapshot in self._conn.execute(query, parameters):
            try:
                tags = read_pgn_headers(pgn)
            except (ChessError, AttributeError, TypeError):
                tags = {}
            if time_control is not None:
                if snapshot[0] is None:
                    base, initial_ms = divmod(time_control.initial_ms, 1000)
                    increment, increment_ms = divmod(time_control.increment_ms, 1000)
                    tags_matching = {f"{base}+{increment}"}
                    if increment == 0:
                        tags_matching.add(str(base))
                    if initial_ms or increment_ms or tags.get("TimeControl") not in tags_matching:
                        continue
                else:
                    try:
                        if GameSessionSnapshot.decode(snapshot[0]).setup.time_control != time_control:
                            continue
                    except (TypeError, ValueError, RecursionError):
                        continue
            summaries.append(GameSummary(
                game_id, created, game_result, tags.get("White", ""), tags.get("Black", ""), tags.get("Event", ""),
                bool(is_favorite),
            ))
        return summaries

    def archive_tags(self) -> tuple[str, ...]:
        return tuple(row[0] for row in self._conn.execute("SELECT DISTINCT tag FROM game_tags ORDER BY tag"))

    def archive_labels(self, game_id: int) -> ArchiveLabels:
        fields = self._conn.execute(
            "SELECT g.favorite, t.tag FROM games g LEFT JOIN game_tags t ON t.game_id = g.id "
            "WHERE g.id = ? ORDER BY t.tag", (game_id,),
        ).fetchall()
        if not fields:
            raise StorageError(f"No saved game with id {game_id}.")
        return ArchiveLabels(bool(fields[0][0]), tuple(tag for _, tag in fields if tag is not None))

    @staticmethod
    def _check_archive_labels(favorite: bool, tags: tuple[str, ...]) -> None:
        if (type(favorite) is not bool or len(tags) > 20
                or any(not isinstance(tag, str) or not 1 <= len(tag) <= 64 or tag != tag.strip()
                       or any(ord(char) < 32 for char in tag) for tag in tags)):
            raise ValueError("Invalid archive favorite or tags.")

    def _validate_archive_labels(self) -> None:
        for (game_id,) in self._conn.execute("SELECT DISTINCT game_id FROM game_tags"):
            labels = self.archive_labels(game_id)
            try:
                self._check_archive_labels(labels.favorite, labels.tags)
            except ValueError as error:
                raise StorageError(f"Invalid archive labels for game {game_id}.") from error

    def set_archive_labels(self, game_id: int, *, favorite: bool, tags: tuple[str, ...] = ()) -> None:
        self._check_archive_labels(favorite, tags)
        tags = tuple(sorted({unicodedata.normalize("NFC", tag) for tag in tags}))
        with self._conn:
            self._conn.execute("BEGIN IMMEDIATE")
            cursor = self._conn.execute("UPDATE games SET favorite = ? WHERE id = ?", (favorite, game_id))
            if cursor.rowcount != 1:
                raise StorageError(f"No saved game with id {game_id}.")
            self._conn.execute("DELETE FROM game_tags WHERE game_id = ?", (game_id,))
            self._conn.executemany("INSERT INTO game_tags (game_id, tag) VALUES (?, ?)",
                                   ((game_id, tag) for tag in tags))

    def delete_game(self, game_id: int) -> None:
        self._conn.execute("DELETE FROM games WHERE id = ?", (game_id,))

    def import_pgn(self, text: str, *, mode: str = "imported", max_plies: int | None = None) -> int:
        document = parse_pgn(text, max_plies=max_plies)
        tags = {k: v for k, v in document.tags if k not in ("SetUp", "FEN", "Result")}
        return self.save_game(
            document.new_game(), mode=mode, headers=tags, result=document.result,
            clock_annotations=document.clock_annotations,
        )

    def import_pgn_file(self, source: Path) -> int:
        """Import one UTF-8 PGN game after size, text and move validation."""
        if not source.is_file():
            raise StorageError("Choose a regular PGN file.")
        with source.open("rb") as handle:
            data = handle.read(MAX_PGN_FILE_BYTES + 1)
        if len(data) > MAX_PGN_FILE_BYTES:
            raise StorageError(f"PGN file exceeds {MAX_PGN_FILE_BYTES // 1024} KiB.")
        text = data.decode("utf-8-sig")
        if not text.strip() or any(ord(char) < 32 and char not in "\t\n\r" for char in text):
            raise StorageError("PGN file is empty or contains invalid control characters.")
        return self.import_pgn(text, max_plies=MAX_PGN_FILE_PLIES)

    def export_pgn_file(self, game_id: int, destination: Path) -> None:
        """Export one validated game and replace the destination atomically."""
        if destination.suffix.lower() != ".pgn":
            raise StorageError("Choose a destination with the .pgn extension.")
        if destination.exists() and destination.samefile(self.path):
            raise StorageError("The active database cannot be overwritten.")
        write_atomic_export(destination, self.export_pgn([game_id]).encode("utf-8"))

    def export_pgn(self, game_ids: list[int] | None = None) -> str:
        ids = game_ids if game_ids is not None else [r[0] for r in reversed(self.list_games())]
        return "\n\n".join(self.load_game(i).pgn for i in ids) + ("\n" if ids else "")

    def save_analysis_report(self, game_id: int, progress: AnalysisProgress) -> None:
        source = self.load_game(game_id).to_game()
        payload = encode_report(progress, source)
        name = progress.results[0].configuration.engine_name
        values = progress.job_id, game_id, _now(), name, progress.total, payload
        cursor = self._conn.execute(
            "INSERT INTO analysis_reports(run_id, source_game_id, created_utc, engine_name, position_count, report) "
            "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(run_id) DO NOTHING", values,
        )
        if not cursor.rowcount:
            existing = self._conn.execute(
                "SELECT source_game_id, report FROM analysis_reports WHERE run_id = ?", (progress.job_id,),
            ).fetchone()
            if existing != (game_id, payload):
                raise StorageError("Analysis run identifier already refers to a different report.")

    def analysis_reports(self) -> tuple[AnalysisReportSummary, ...]:
        rows = self._conn.execute(
            "SELECT run_id, source_game_id, created_utc, engine_name, position_count "
            "FROM analysis_reports ORDER BY created_utc DESC, rowid DESC"
        )
        return tuple(AnalysisReportSummary(*row) for row in rows)

    def load_analysis_report(self, run_id: str) -> tuple[int, AnalysisProgress]:
        row = self._conn.execute(
            "SELECT source_game_id, engine_name, position_count, "
            "CASE WHEN length(CAST(report AS BLOB)) <= ? THEN report END "
            "FROM analysis_reports WHERE run_id = ?", (MAX_REPORT_BYTES, run_id),
        ).fetchone()
        if row is None:
            raise StorageError("Analysis report is no longer available.")
        game_id, engine_name, count, payload = row
        try:
            report = decode_report(payload, self.load_game(game_id).to_game())
            if (report.job_id, report.results[0].configuration.engine_name, report.total) != (run_id, engine_name, count):
                raise ValueError("Analysis index differs from the saved report.")
        except ValueError as error:
            raise StorageError(f"Invalid saved analysis: {error}") from error
        return game_id, report

    def save_analysis_training_candidate(self, report_id: str, ply: int) -> AnalysisTrainingCandidate:
        game_id, report = self.load_analysis_report(report_id)
        candidate = AnalysisTrainingCandidate.from_report(game_id, report, ply)
        payload = candidate.encode()
        AnalysisTrainingCandidate.decode(payload)
        inserted = self._conn.execute(
            "INSERT INTO analysis_training_candidates VALUES (?, ?, ?, ?) ON CONFLICT(candidate_id) DO NOTHING",
            (candidate.candidate_id, game_id, report_id, payload),
        )
        if inserted.rowcount:
            return candidate
        stored = self._conn.execute(
            "SELECT payload FROM analysis_training_candidates WHERE candidate_id = ?", (candidate.candidate_id,),
        ).fetchone()
        if stored is None:
            raise StorageError("The duplicate training candidate is no longer available.")
        try:
            return AnalysisTrainingCandidate.decode(stored[0])
        except (TypeError, ValueError) as error:
            raise StorageError(f"Invalid analysis training candidate: {error}") from error

    def analysis_training_candidates(self) -> tuple[AnalysisTrainingCandidate, ...]:
        rows = self._conn.execute(
            "SELECT candidate_id, source_game_id, source_report_id, "
            "CASE WHEN length(CAST(payload AS BLOB)) <= ? THEN payload END "
            "FROM analysis_training_candidates ORDER BY rowid DESC", (MAX_CANDIDATE_BYTES,),
        )
        candidates = []
        try:
            for identity, game_id, report_id, payload in rows:
                candidate = AnalysisTrainingCandidate.decode(payload)
                if (identity != candidate.candidate_id
                        or (game_id is not None and game_id != candidate.source_game_id)
                        or (report_id is not None and report_id != candidate.report_id)):
                    raise ValueError("Training candidate index differs from its provenance.")
                candidates.append(candidate)
        except (ValueError, TypeError) as error:
            raise StorageError(f"Invalid analysis training candidate: {error}") from error
        return tuple(candidates)

    def _validate_training_candidate(self, candidate: TrainingCandidate) -> None:
        positions = self.load_game(candidate.source_game_id).to_game().played_positions()
        if candidate.ply >= len(positions) or to_fen(positions[candidate.ply]) != candidate.fen:
            raise StorageError("Training position does not match the saved game.")

    def save_training_candidate(self, candidate: TrainingCandidate) -> None:
        self._validate_training_candidate(candidate)
        self._conn.execute(
            "INSERT INTO training_candidates(source_game_id, ply, fen) VALUES (?, ?, ?) "
            "ON CONFLICT(source_game_id, ply) DO NOTHING",
            (candidate.source_game_id, candidate.ply, candidate.fen),
        )

    def training_candidates(self) -> tuple[TrainingCandidate, ...]:
        rows = self._conn.execute(
            "SELECT source_game_id, ply, fen FROM training_candidates ORDER BY source_game_id DESC, ply"
        )
        try:
            return tuple(TrainingCandidate(*row) for row in rows)
        except (ValueError, TypeError) as error:
            raise StorageError(f"Invalid training candidate: {error}") from error

    @staticmethod
    def _validate_training_checkpoint(checkpoint: TrainingCheckpoint) -> None:
        if checkpoint.chain_id != DEMO_MATE_CHAIN.chain_id:
            raise ValueError("Unknown saved training chain.")
        DEMO_MATE_CHAIN.resume(demo_chain_catalog(load_demo_pack()), checkpoint)

    @staticmethod
    def _chain_attempt_values(attempt: TrainingAttempt) -> tuple:
        return (attempt.key.pack_id, attempt.key.puzzle_id, attempt.recorded_at.isoformat(),
                int(attempt.status is AttemptStatus.SOLVED), attempt.mistakes, attempt.hints_used,
                attempt.duration_ms)

    def _verify_chain_attempt(self, attempt: TrainingAttempt) -> None:
        row = self._conn.execute(
            "SELECT pack_id, puzzle_id, attempted_utc, solved, mistakes, hints_used, duration_ms "
            "FROM puzzle_attempts WHERE attempt_uid = ?", (attempt.attempt_id,),
        ).fetchone()
        if row != self._chain_attempt_values(attempt):
            raise StorageError("Training attempt differs from its checkpoint.")

    def save_training_checkpoint(
        self, checkpoint: TrainingCheckpoint, *, expected_revision: int, hint_stage: int,
    ) -> int:
        """Save the session and grade each completed attempt exactly once."""
        self._validate_training_checkpoint(checkpoint)
        payload = checkpoint.encode()
        revision = expected_revision + 1
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            previous = self.load_training_checkpoint(checkpoint.chain_id)
            if (previous[1] if previous else 0) != expected_revision:
                raise StorageError("The training chain was changed by another window.")
            self._conn.execute(
                "INSERT INTO training_checkpoints(chain_id, revision, hint_stage, payload) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(chain_id) DO UPDATE SET revision = excluded.revision, "
                "hint_stage = excluded.hint_stage, payload = excluded.payload",
                (checkpoint.chain_id, revision, hint_stage, payload),
            )
            for attempt in checkpoint.attempts:
                if attempt.counted:
                    result = self._conn.execute(
                        "INSERT INTO puzzle_attempts(pack_id, puzzle_id, attempted_utc, solved, mistakes, hints_used, "
                        "duration_ms, attempt_uid) VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                        "ON CONFLICT(attempt_uid) DO NOTHING",
                        (*self._chain_attempt_values(attempt), attempt.attempt_id),
                    )
                    if not result.rowcount:
                        self._verify_chain_attempt(attempt)
            self._conn.execute("COMMIT")
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise
        return revision

    def load_training_checkpoint(self, chain_id: str) -> tuple[TrainingCheckpoint, int, int] | None:
        row = self._conn.execute(
            "SELECT revision, hint_stage, CASE WHEN length(CAST(payload AS BLOB)) <= ? THEN payload END "
            "FROM training_checkpoints WHERE chain_id = ?", (MAX_TRAINING_CHECKPOINT_BYTES, chain_id),
        ).fetchone()
        if row is None:
            return None
        revision, hint_stage, payload = row
        try:
            checkpoint = TrainingCheckpoint.decode(payload)
            if (checkpoint.chain_id != chain_id or type(revision) is not int or revision < 1
                    or type(hint_stage) is not int or not 0 <= hint_stage <= 2):
                raise ValueError("Invalid training checkpoint index.")
        except (TypeError, ValueError) as error:
            raise StorageError(f"Invalid saved training chain: {error}") from error
        return checkpoint, revision, hint_stage

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

    def puzzle_training_ids(self, pack_id: str) -> tuple[set[str], set[str]]:
        """Return solved ids and attempted ids still missing a clean solve."""
        solved: set[str] = set()
        review: set[str] = set()
        for puzzle_id, was_solved, clean_solves in self._conn.execute(
            "SELECT puzzle_id, solved, clean_solves FROM puzzle_progress WHERE pack_id = ?", (pack_id,),
        ):
            if was_solved:
                solved.add(puzzle_id)
            if not clean_solves:
                review.add(puzzle_id)
        return solved, review

    def due_puzzle_ids(self, pack_id: str, *, now: datetime) -> set[str]:
        """Project due reviews from the attempts of the selected pack."""
        if now.utcoffset() is None:
            raise ValueError("Review time must include a timezone.")
        rows = self._conn.execute(
            "SELECT id, pack_id, puzzle_id, attempted_utc, solved, mistakes, hints_used, duration_ms "
            "FROM puzzle_attempts WHERE pack_id = ? ORDER BY id", (pack_id,),
        )
        try:
            progress = summarize_attempts(TrainingAttempt.from_legacy(*row) for row in rows)
        except (ValueError, OverflowError, TypeError) as error:
            raise StorageError(f"Invalid training history for {pack_id}: {error}") from error
        return {key.puzzle_id for key, item in progress.items() if item.due_at <= now}

    def latest_puzzle_attempt(self, pack_id: str, puzzle_id: str) -> PuzzleAttempt | None:
        row = self._conn.execute(
            "SELECT solved, mistakes, hints_used, duration_ms FROM puzzle_attempts"
            " WHERE pack_id = ? AND puzzle_id = ? ORDER BY id DESC LIMIT 1", (pack_id, puzzle_id),
        ).fetchone()
        return PuzzleAttempt(bool(row[0]), row[1], row[2], row[3]) if row is not None else None

    def statistics(self) -> Statistics:
        games = self._conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
        attempted, solved, clean = self._conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(solved), 0), COALESCE(SUM(clean_solves > 0), 0) FROM puzzle_progress"
        ).fetchone()
        return Statistics(games, attempted, solved, clean)
