"""Versioned snapshot of a game session, independent of storage and Tk.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
import json
from uuid import UUID

from ..chess import ChessGame, Color, DrawClaim, GameStatus, Move, parse_fen
from ..chess.game import GameTimeline
from .clock import ClockReading, ClockTimeline, TimeControl
from .controller import GameSetup, PlayMode

SESSION_SCHEMA = 1
MAX_SNAPSHOT_BYTES = 256 * 1024
MAX_SESSION_PLIES = 4096


class SessionLifecycle(StrEnum):
    ACTIVE = "active"
    FINISHED = "finished"


@dataclass(frozen=True, slots=True)
class GameSessionSnapshot:
    session_id: str
    created_utc: str
    updated_utc: str
    setup: GameSetup
    initial_fen: str
    timeline: GameTimeline
    lifecycle: SessionLifecycle
    engine_ref: str | None = None
    bot_preset: str | None = None
    headers: tuple[tuple[str, str], ...] = ()
    profile_id: str = "local"
    clock: ClockTimeline | None = None

    def restore_game(self) -> ChessGame:
        game = ChessGame.from_timeline(parse_fen(self.initial_fen), self.timeline)
        finished = game.outcome().status is not GameStatus.ACTIVE
        if finished != (self.lifecycle is SessionLifecycle.FINISHED):
            raise ValueError("Session lifecycle contradicts the game outcome.")
        if (self.clock is None) != (self.setup.time_control is None):
            raise ValueError("Session clock and time control disagree.")
        if self.clock is not None:
            if self.clock.current.turn is not game.state.turn or len(self.clock.positions) != len(self.timeline.moves) + 1:
                raise ValueError("Session clock does not match the move history.")
            turn = game.initial_state.turn
            for reading in self.clock.positions:
                if reading.turn is not turn or min(reading.white_ns, reading.black_ns) == 0:
                    raise ValueError("Invalid historical clock reading.")
                turn = turn.opposite
        return game

    def encode(self) -> str:
        data = {
            "schema": SESSION_SCHEMA, "id": self.session_id, "profile": self.profile_id,
            "created": self.created_utc, "updated": self.updated_utc, "status": self.lifecycle,
            "mode": self.setup.mode, "bot": self.setup.bot_color, "engine": self.engine_ref,
            "preset": self.bot_preset, "fen": self.initial_fen, "headers": dict(self.headers),
            "moves": [move.to_uci() for move in self.timeline.moves], "cursor": self.timeline.cursor,
            "result": self.timeline.result, "resigned": self.timeline.resigned_by,
            "claim": self.timeline.claim.name if self.timeline.claim else None,
            "declared": self.timeline.declared_move.to_uci() if self.timeline.declared_move else None,
        }
        if self.clock is not None and self.setup.time_control is not None:
            control = self.setup.time_control
            data["time_control"] = [control.initial_ms, control.increment_ms]
            data["clock"] = {
                "current": _encode_reading(self.clock.current),
                "positions": [_encode_reading(reading) for reading in self.clock.positions],
            }
        return json.dumps(data, ensure_ascii=True, separators=(",", ":"))

    @classmethod
    def decode(cls, payload: str) -> GameSessionSnapshot:
        if len(payload) > MAX_SNAPSHOT_BYTES or len(payload.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
            raise ValueError("Session snapshot exceeds its size limit.")
        data = json.loads(payload)
        if not isinstance(data, dict) or type(data.get("schema")) is not int or data["schema"] != SESSION_SCHEMA:
            raise ValueError("Unsupported session schema.")
        try:
            UUID(data["id"])
            created = datetime.fromisoformat(data["created"])
            updated = datetime.fromisoformat(data["updated"])
            if created.tzinfo is None or updated.tzinfo is None or updated < created or data["profile"] != "local":
                raise ValueError("Invalid session timestamps or profile.")
            control = TimeControl(*data["time_control"]) if data.get("time_control") is not None else None
            setup = GameSetup(
                PlayMode(data["mode"]), Color(data["bot"]) if data["bot"] is not None else None, time_control=control,
            )
            engine, preset = data["engine"], data["preset"]
            if setup.mode is PlayMode.HUMAN_VS_BOT:
                if not all(isinstance(value, str) and value for value in (engine, preset)):
                    raise ValueError("Bot sessions require an engine reference and preset.")
            elif engine is not None or preset is not None:
                raise ValueError("Unexpected bot configuration for a two-player session.")
            moves = data["moves"]
            if not isinstance(moves, list) or len(moves) > MAX_SESSION_PLIES or type(data["cursor"]) is not int:
                raise ValueError("Invalid session move line or cursor.")
            headers = data["headers"]
            if not isinstance(headers, dict) or any(not isinstance(value, str) for value in headers.values()):
                raise ValueError("Invalid session headers.")
            if not isinstance(data["fen"], str) or len(data["fen"]) > 4096:
                raise ValueError("Invalid session FEN.")
            if data["result"] not in (None, "1-0", "0-1", "1/2-1/2"):
                raise ValueError("Invalid session result.")
            timeline = GameTimeline(
                tuple(Move.from_uci(text) for text in moves), data["cursor"], data["result"],
                Color(data["resigned"]) if data["resigned"] is not None else None,
                DrawClaim[data["claim"]] if data["claim"] is not None else None,
                Move.from_uci(data["declared"]) if data["declared"] is not None else None,
            )
            clock = None
            if data.get("clock") is not None:
                payload = data["clock"]
                if not isinstance(payload["positions"], list) or len(payload["positions"]) != len(moves) + 1:
                    raise ValueError("Invalid clock history length.")
                clock = ClockTimeline(
                    _decode_reading(payload["current"]),
                    tuple(_decode_reading(reading) for reading in payload["positions"]),
                )
            return cls(data["id"], data["created"], data["updated"], setup, data["fen"], timeline,
                       SessionLifecycle(data["status"]), engine, preset, tuple(sorted(headers.items())), clock=clock)
        except (AttributeError, KeyError, TypeError) as error:
            raise ValueError("Invalid session data.") from error


def _encode_reading(reading: ClockReading) -> list[int | str]:
    return [reading.white_ns, reading.black_ns, reading.turn.value]


def _decode_reading(data: list[int | str]) -> ClockReading:
    white, black, turn = data
    return ClockReading(white, black, Color(turn))
