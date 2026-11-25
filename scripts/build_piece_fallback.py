"""Build the Tk 8.6 PNG atlases from the editable piece SVGs using Tk 9."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chess_and_chains.ui.pieces import (  # noqa: E402
    PIECE_FALLBACK_SIZES,
    PIECE_FILE_NAMES,
    PIECE_SVG_SIZE,
    piece_atlas_box,
    validate_svg_piece_set,
)


def build_atlas(root: tk.Tk, assets: Path) -> None:
    report = validate_svg_piece_set(assets)
    if not report.ok:
        raise SystemExit(f"{assets.relative_to(ROOT)}:\n" + "\n".join(report.problems))

    _, _, width, height = piece_atlas_box(PIECE_FILE_NAMES[-1], len(PIECE_FALLBACK_SIZES) - 1)
    atlas = tk.PhotoImage(master=root, width=width, height=height)
    sources = {name: (assets / name).read_bytes() for name in PIECE_FILE_NAMES}
    for band, size in enumerate(PIECE_FALLBACK_SIZES):
        for name, source in sources.items():
            tile = tk.PhotoImage(master=root, data=source, format=("svg", "-scale", size / PIECE_SVG_SIZE))
            if (tile.width(), tile.height()) != (size, size):
                raise ValueError(f"Unexpected tile dimensions: {name} at {size} px")
            left, top, _, _ = piece_atlas_box(name, band)
            root.tk.call(atlas, "copy", tile, "-to", left, top)
    output = assets / "fallback.png"
    atlas.write(str(output), format="png")
    print(f"{output.relative_to(ROOT)}: {width} × {height}, {len(PIECE_FALLBACK_SIZES)} sizes")


def main() -> None:
    assets = ROOT / "src" / "chess_and_chains" / "ui" / "piece_assets"
    root = tk.Tk()
    root.withdraw()
    try:
        build_atlas(root, assets)
        build_atlas(root, assets / "original")
        build_atlas(root, assets / "top")
        build_atlas(root, assets / "classic")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
