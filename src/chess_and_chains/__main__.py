"""CLI entry point for the local desktop prototype."""
import argparse
from pathlib import Path

from . import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chess & Chains local chess prototype")
    parser.add_argument(
        "--headless-check",
        action="store_true",
        help="report the installed version without opening the desktop window",
    )
    parser.add_argument("--board-design", type=Path, metavar="SVG_OR_DIRECTORY",
                        help="preview a local SVG board or a directory of square SVGs for this session")
    parser.add_argument("--piece-view", choices=("front", "top"), default="front",
                        help="choose the front or top view of the pieces for this session")
    args = parser.parse_args(argv)
    design = None
    if args.board_design is not None:
        from .ui.board_artwork import BoardArtworkError, load_board_design

        try:
            design = load_board_design(args.board_design)
        except (OSError, BoardArtworkError) as error:
            parser.error(str(error))
    if args.headless_check:
        print(
            f"Chess & Chains {__version__} — local GUI prototype available "
            "(two players, mock bot, demo puzzles); no engine bundled."
        )
        return 0

    from .ui import launch

    from .ui.board_artwork import BoardArtworkError

    try:
        launch(board_design=design, top_pieces=args.piece_view == "top")
    except BoardArtworkError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
