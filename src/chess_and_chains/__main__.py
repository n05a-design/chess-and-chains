"""CLI entry point for the local desktop prototype."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    _SRC_DIR = str(Path(__file__).resolve().parents[1])
    if _SRC_DIR not in sys.path:
        sys.path.insert(0, _SRC_DIR)

from chess_and_chains import DISPLAY_VERSION


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chess & Chains local chess prototype")
    parser.add_argument("--version", action="version", version=f"Chess & Chains {DISPLAY_VERSION}")
    parser.add_argument(
        "--headless-check",
        action="store_true",
        help="report the installed version without opening the desktop window",
    )
    parser.add_argument(
        "--board-design",
        type=Path,
        metavar="SVG_OR_DIRECTORY",
        help="preview a local SVG board or a directory of square SVGs for this session",
    )
    parser.add_argument(
        "--piece-set",
        choices=("original", "top", "classic"),
        default=None,
        help="choose the chess piece set (original, top, or classic) for this session",
    )
    parser.add_argument(
        "--piece-view",
        choices=("front", "top"),
        default="front",
        help="choose the front or top view of the pieces for this session (legacy option)",
    )
    args = parser.parse_args(argv)
    design = None
    if args.board_design is not None:
        from chess_and_chains.ui.board_artwork import BoardArtworkError, load_board_design

        try:
            design = load_board_design(args.board_design)
        except (OSError, BoardArtworkError) as error:
            parser.error(str(error))
    if args.headless_check:
        print(
            f"Chess & Chains {DISPLAY_VERSION} — local GUI prototype available "
            "(two players, mock bot, demo puzzles); no engine bundled."
        )
        return 0

    from chess_and_chains.ui import launch
    from chess_and_chains.ui.board_artwork import BoardArtworkError

    launch_kwargs: dict[str, object] = {
        "board_design": design,
        "top_pieces": (args.piece_view == "top" if args.piece_set is None else args.piece_set == "top"),
    }
    if args.piece_set is not None:
        launch_kwargs["piece_set"] = args.piece_set

    try:
        launch(**launch_kwargs)
    except BoardArtworkError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
