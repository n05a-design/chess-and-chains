"""CLI entry point for the local desktop prototype."""
import argparse

from . import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chess & Chains local chess prototype")
    parser.add_argument(
        "--headless-check",
        action="store_true",
        help="report the installed version without opening the desktop window",
    )
    args = parser.parse_args(argv)
    if args.headless_check:
        print(
            f"Chess & Chains {__version__} — local two-player GUI prototype available."
        )
        return 0

    from .ui import launch

    launch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
