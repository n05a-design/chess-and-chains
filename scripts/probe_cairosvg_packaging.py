"""Render a self-authored SVG fixture for optional packaging smoke tests."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import argparse
from pathlib import Path


SVG_FIXTURE = b"""<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
<path d="M32 5c-5 0-9 4-9 9 0 3 1 5 3 7l-4 9H17v6h30v-6h-5l-4-9c2-2 3-4 3-7 0-5-4-9-9-9zm-9 36-4 10h26l-4-10H23zm-7 13h32v5H16z"
fill="#e9b91d" stroke="#181818" stroke-width="2" stroke-linejoin="round"/>
</svg>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="PNG path to write")
    args = parser.parse_args()

    import cairosvg

    png = cairosvg.svg2png(
        bytestring=SVG_FIXTURE,
        output_width=96,
        output_height=96,
    )
    args.output.write_bytes(png)
    print(f"Rendered 96x96 local SVG fixture with CairoSVG {cairosvg.__version__}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
