# SPDX-License-Identifier: MPL-2.0
"""Standalone launcher for Chess & Chains with OS bytecode-cache isolation.

Redirects Python's ``__pycache__`` output outside synced cloud folders (like
OneDrive) or read-only macOS app bundles into the system cache directory,
ensures ``src`` is on ``sys.path``, and launches the desktop application.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def cache_dir() -> str:
    """Return the platform-specific bytecode cache directory."""
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Caches/ChessAndChains")
    elif os.name == "nt":
        base = os.path.join(
            os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
            "ChessAndChains",
            "Cache",
        )
    else:
        base = os.path.join(
            os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"),
            "chess-and-chains",
        )
    return os.path.join(base, "bytecode")


def main(argv: list[str] | None = None) -> int:
    if not getattr(sys, "pycache_prefix", None):
        sys.pycache_prefix = cache_dir()
    src_dir = str(Path(__file__).resolve().parents[1])
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from chess_and_chains.__main__ import main as cli_main

    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
