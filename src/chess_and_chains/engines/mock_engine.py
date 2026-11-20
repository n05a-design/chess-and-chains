"""Project-owned mock UCI engine for tests and the bot-mode vertical slice.

This is NOT a chess AI. It answers ``go`` with a legal move chosen by a
trivial, deterministic heuristic (mate in one > capture > seeded random),
computed with the project's own MPL-2.0 rules domain. It exists so the full
UCI -> controller -> UI path can be exercised without any third-party engine.

Run: ``python -m chess_and_chains.engines.mock_engine [--mode MODE]``.
Modes ``crash``, ``stall``, ``illegal`` and ``garbage`` simulate faults.
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import argparse
import random
import sys
import threading
import time

from ..chess import INITIAL_FEN, ChessRules, Move, parse_fen

ENGINE_NAME = "Chess & Chains Mock Engine (test only, not a chess AI)"
MODES = ("normal", "crash", "stall", "illegal", "garbage", "crash-on-start", "crash-on-ready")

OPTIONS = (
    "option name Threads type spin default 1 min 1 max 8",
    "option name Hash type spin default 16 min 1 max 256",
    "option name Skill Level type spin default 20 min 0 max 20",
    "option name UCI_LimitStrength type check default false",
    "option name UCI_Elo type spin default 1500 min 1320 max 3190",
    "option name Move Overhead type spin default 10 min 0 max 5000",
)


def choose_move(rules: ChessRules, fen: str, moves: list[str], rng: random.Random) -> Move | None:
    state = parse_fen(fen)
    for text in moves:
        state = rules.apply(state, Move.from_uci(text))
    legal = rules.legal_moves(state)
    if not legal:
        return None
    for move in legal:
        child = rules.apply(state, move)
        if not rules.legal_moves(child) and rules.is_in_check(child):
            return move
    captures = [m for m in legal if state.board[m.to_square] is not None]
    pool = captures or list(legal)
    return rng.choice(pool)


def run(mode: str, seed: int, delay_ms: int, stdin=sys.stdin, stdout=sys.stdout) -> int:
    rules = ChessRules()
    rng = random.Random(seed)
    fen, moves = INITIAL_FEN, []
    stop = threading.Event()
    out_lock = threading.Lock()

    def say(line: str) -> None:
        with out_lock:
            stdout.write(line + "\n")
            stdout.flush()

    def search(snapshot_fen: str, snapshot_moves: list[str], movetime: int) -> None:
        wait = min(delay_ms if delay_ms >= 0 else movetime, movetime)
        stop.wait(wait / 1000)
        move = choose_move(rules, snapshot_fen, snapshot_moves, rng)
        say(f"bestmove {move.to_uci() if move else '(none)'}")

    worker: threading.Thread | None = None
    if mode == "crash-on-start":
        return 3
    for raw in stdin:
        command = raw.strip()
        if command == "uci":
            say(f"id name {ENGINE_NAME}")
            say("id author Chess & Chains project (MPL-2.0)")
            for line in OPTIONS:
                say(line)
            say("uciok")
        elif command == "isready":
            if mode == "crash-on-ready":
                return 5
            say("readyok")
        elif command == "ucinewgame":
            fen, moves = INITIAL_FEN, []
        elif command.startswith("setoption "):
            pass
        elif command.startswith("position "):
            tokens = command.split()
            if len(tokens) >= 2 and tokens[1] == "startpos":
                fen, rest = INITIAL_FEN, tokens[2:]
            elif len(tokens) >= 8 and tokens[1] == "fen":
                fen, rest = " ".join(tokens[2:8]), tokens[8:]
            else:
                continue
            moves = rest[1:] if rest[:1] == ["moves"] else []
        elif command.startswith("go"):
            if mode == "crash":
                return 7
            if mode == "stall":
                continue
            if mode == "illegal":
                say("bestmove a1a1")
                continue
            if mode == "garbage":
                say("bestmove zz")
                continue
            tokens = command.split()
            movetime = 50
            if "movetime" in tokens:
                try:
                    movetime = max(1, int(tokens[tokens.index("movetime") + 1]))
                except (IndexError, ValueError):
                    pass
            stop.clear()
            worker = threading.Thread(target=search, args=(fen, list(moves), movetime), daemon=True)
            worker.start()
        elif command == "stop":
            stop.set()
            if worker is not None:
                worker.join(timeout=2)
        elif command == "quit":
            stop.set()
            break
    if worker is not None:
        worker.join(timeout=2)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=ENGINE_NAME)
    parser.add_argument("--mode", choices=MODES, default="normal")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--delay-ms", type=int, default=-1,
        help="artificial think time; default uses the requested movetime",
    )
    args = parser.parse_args(argv)
    return run(args.mode, args.seed, args.delay_ms)


if __name__ == "__main__":
    raise SystemExit(main())
