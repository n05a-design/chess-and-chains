"""Bounded FEN file exchange and atomic writes for user-selected exports."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from ..chess import FenError, GameState, parse_fen, to_fen

MAX_FEN_FILE_BYTES = 4096


def parse_fen_text(text: str) -> GameState:
    """Accept one FEN line with optional surrounding whitespace."""
    if len(text) > MAX_FEN_FILE_BYTES:
        raise FenError("FEN exceeds 4 KiB.")
    line = text.strip(" \t\r\n")
    if not line.isascii() or any(char != "\t" and not " " <= char <= "~" for char in line):
        raise FenError("Enter exactly one FEN line using ASCII characters.")
    return parse_fen(line)


def read_fen_file(source: Path) -> GameState:
    if not source.is_file():
        raise FenError("Choose a regular FEN file.")
    with source.open("rb") as handle:
        data = handle.read(MAX_FEN_FILE_BYTES + 1)
    if len(data) > MAX_FEN_FILE_BYTES:
        raise FenError("FEN file exceeds 4 KiB.")
    return parse_fen_text(data.decode("utf-8-sig"))


def write_fen_file(position: GameState, destination: Path) -> None:
    if destination.suffix.lower() != ".fen":
        raise FenError("Choose a destination with the .fen extension.")
    write_atomic_export(destination, (to_fen(position) + "\n").encode("ascii"))


def write_atomic_export(destination: Path, data: bytes) -> None:
    fd, name = tempfile.mkstemp(dir=destination.parent, prefix=f"{destination.suffix.lower()}-")
    pending = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        pending.replace(destination)
    finally:
        pending.unlink(missing_ok=True)
