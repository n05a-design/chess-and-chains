"""CLI entry point for validating starter installation without a GUI."""
from . import __version__

def main() -> int:
    print(f"Chess & Chains {__version__} — foundation scaffold, not yet playable.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
