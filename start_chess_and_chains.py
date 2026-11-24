#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Standalone launcher for Chess & Chains from the repository root."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_DIR = str(ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from chess_and_chains.start import main

if __name__ == "__main__":
    raise SystemExit(main())
