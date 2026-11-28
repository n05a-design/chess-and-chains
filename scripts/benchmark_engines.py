"""Run a bounded, color-paired benchmark with approved local UCI engines.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
import tempfile
from time import monotonic

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chess_and_chains.chess import ChessGame, ChessError, Color, GameStatus, export_pgn, parse_fen, to_fen
from chess_and_chains.engines.bot import EngineConfig, UCIBot
from chess_and_chains.engines.presets import load_presets
from chess_and_chains.engines.registry import EngineRegistry
from chess_and_chains.storage.exchange import write_atomic_export


def competitors(args: argparse.Namespace, temporary: Path) -> tuple[EngineConfig, EngineConfig]:
    if args.smoke:
        registry = EngineRegistry(temporary / "fixture-registry.sqlite3")
        configs = []
        for seed in (args.seed, args.seed + 1):
            fixture = EngineConfig.mock(seed=seed)
            profile = registry.register(fixture.command[0], arguments=fixture.command[1:], origin="fixture")
            registry.probe(profile.engine_id)
            configs.append(registry.launch_configuration(profile.engine_id))
        return configs[0], configs[1]
    registry = EngineRegistry(args.registry)
    return registry.launch_configuration(args.first), registry.launch_configuration(args.second)


def play_game(initial: str, bots: tuple[UCIBot, UCIBot], args: argparse.Namespace) -> tuple[dict, str]:
    game = ChessGame(parse_fen(initial))
    colors = {Color.WHITE: bots[0], Color.BLACK: bots[1]}
    started = monotonic()
    kind, result, detail = "ply-limit", "*", None
    try:
        for bot in bots:
            bot.ensure_started().new_game()
        for _ in range(args.max_plies):
            outcome = game.outcome()
            if outcome.status is not GameStatus.ACTIVE:
                break
            remaining = args.game_seconds - (monotonic() - started)
            if remaining <= 0:
                kind = "aborted"
                detail = "game-time-limit"
                break
            current = colors[game.state.turn]
            try:
                engine = current.ensure_started()
                engine.set_position(initial, game.moves)
                legal = game.rules.legal_moves(game.state)
                if args.nodes is not None:
                    move = engine.go_nodes(args.nodes, legal, timeout=remaining)
                else:
                    move = engine.go_movetime(args.move_ms, legal, timeout=min(remaining, args.move_ms / 1000 + 2))
                if move is None:
                    raise ChessError("The engine returned no move for an active position.")
                game.play(move)
            except (RuntimeError, OSError, ValueError) as error:
                kind = "technical-loss"
                result = "0-1" if game.state.turn is Color.WHITE else "1-0"
                detail = str(error)
                current.close()
                break
    except KeyboardInterrupt:
        kind, detail = "aborted", "keyboard-interrupt"
    except (RuntimeError, OSError, ValueError) as error:
        kind, detail = "unrated", str(error)
    outcome = game.outcome()
    if outcome.status is not GameStatus.ACTIVE:
        if outcome.winner is None:
            kind, result = "draw", "1/2-1/2"
        else:
            kind = "win"
            result = "1-0" if outcome.winner is Color.WHITE else "0-1"
        detail = outcome.status.name.lower()
    row = {"kind": kind, "result": result, "detail": detail, "plies": len(game.moves),
           "start_fen": initial, "seconds": round(monotonic() - started, 3)}
    pgn = export_pgn(game, {"White": bots[0].display_name, "Black": bots[1].display_name}, result)
    return row, pgn


def run(args: argparse.Namespace) -> dict:
    presets = {preset.id: preset for preset in load_presets()}
    openings = [to_fen(parse_fen(fen)) for fen in (args.fen or [to_fen(ChessGame().initial_state)])]
    planned = openings * args.pairs
    random.Random(args.seed).shuffle(planned)
    rows, records = [], []
    with tempfile.TemporaryDirectory(prefix="chess-engine-benchmark-") as directory:
        first, second = competitors(args, Path(directory))
        pair = (UCIBot(first, presets[args.first_preset]), UCIBot(second, presets[args.second_preset]))
        try:
            for start in planned:
                for indices in ((0, 1), (1, 0)):
                    row, record = play_game(start, (pair[indices[0]], pair[indices[1]]), args)
                    row["white"], row["black"] = indices
                    rows.append(row)
                    records.append(record)
                    if row["detail"] == "keyboard-interrupt":
                        break
                if rows[-1]["detail"] == "keyboard-interrupt":
                    break
        finally:
            for bot in pair:
                bot.close()
        identities = [
            {"reference": bot.config.session_reference(), "origin": bot.config.source,
             "binary_sha256": bot.config.provenance.binary_sha256 if bot.config.provenance else None,
             "version": bot.config.verified_version, "preset": bot.preset.id,
             "effective_options": bot.last_plan.apply if bot.last_plan else None}
            for bot in pair
        ]
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False)
    result = {
        "schema": 1, "fixture": args.smoke, "commit": revision.stdout.strip() if revision.returncode == 0 else None,
        "python": platform.python_version(), "platform": platform.platform(), "architecture": platform.machine(),
        "processor": platform.processor(), "seed": args.seed, "games": rows, "competitors": identities,
        "limits": {"pairs": args.pairs, "half_moves": args.max_plies, "game_seconds": args.game_seconds,
                   "move_ms": args.move_ms if args.nodes is None else None, "nodes": args.nodes},
        "uncertainty": {"elo": None, "confidence_interval": None, "reason": "No rating inference from this run."},
    }
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_atomic_export(args.output, (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode())
        write_atomic_export(args.output.with_suffix(".pgn"), ("\n\n".join(records) + "\n").encode())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true", help="use project-owned UCI fixtures")
    parser.add_argument("--registry", type=Path, help="existing local engine registry")
    parser.add_argument("--first", help="first approved engine UUID")
    parser.add_argument("--second", help="second approved engine UUID")
    presets = tuple(preset.id for preset in load_presets())
    parser.add_argument("--first-preset", choices=presets, default=presets[0])
    parser.add_argument("--second-preset", choices=presets, default=presets[1])
    parser.add_argument("--fen", action="append", help="repeat for a set of start positions")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--pairs", type=int, default=1)
    parser.add_argument("--max-plies", type=int, default=12)
    parser.add_argument("--game-seconds", type=int, default=30)
    budget = parser.add_mutually_exclusive_group()
    budget.add_argument("--move-ms", type=int, default=50)
    budget.add_argument("--nodes", type=int)
    parser.add_argument("--output", type=Path, help="JSON result path; writes a PGN alongside it")
    args = parser.parse_args()
    if not args.smoke and not (args.registry and args.registry.is_file() and args.first and args.second):
        parser.error("Use --smoke or select two approved engines from an existing --registry.")
    if not (1 <= args.pairs <= 200 and 1 <= args.max_plies <= 512 and 1 <= args.game_seconds <= 3600
            and 1 <= args.move_ms <= 60_000 and (args.nodes is None or 1 <= args.nodes <= 100_000_000)):
        parser.error("Benchmark limits are outside the supported range.")
    if args.output is not None and args.output.suffix.casefold() != ".json":
        parser.error("Benchmark output must be a .json file.")
    try:
        result = run(args)
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False))
    return 1 if any(game["kind"] in ("technical-loss", "unrated", "aborted") for game in result["games"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
