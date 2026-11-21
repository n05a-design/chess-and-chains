"""Project the editable marble SVGs into portable Tk texture atlases."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chess_and_chains.ui.marble_board import (  # noqa: E402
    BORDER, PLATE_SIZE, PROJECTION, REFERENCE_PIXELS, board_frame, plate_frame,
)
from chess_and_chains.ui.piece_contract import PIECE_FILE_NAMES  # noqa: E402

ART = ROOT / "design/source/marmor-3d/spielsatz"
DEFAULT_OUTPUT = ROOT / "src/chess_and_chains/ui/marble_assets"

SCRIPT = """
const [board, ...pieces] = Array.from(document.images);
const render = (width, height) => Object.assign(document.createElement("canvas"), {width, height});
const [bw, bh, bx, by] = frames.board;
const [pw, ph, px, py] = frames.plate;
const white = render(bw, bh);
const black = render(bw, bh);
const plates = render(6 * pw, 2 * ph);
const p = plates.getContext("2d");
const drawBoard = (canvas, angle) => {
  const b = canvas.getContext("2d");
  b.setTransform(...matrix, bx, by);
  b.translate(4, 4);
  b.rotate(angle);
  const half = 4 + border;
  b.drawImage(board, -half, -half, 2 * half, 2 * half);
};
drawBoard(white, 0);
drawBoard(black, Math.PI);
pieces.forEach((piece, i) => {
  const half = diameter / 2;
  p.setTransform(...matrix, px + (i % 6) * pw, py + Math.floor(i / 6) * ph);
  p.drawImage(piece, -half, -half, diameter, diameter);
});
for (const [name, canvas] of Object.entries({white, black, plates})) {
  const result = document.createElement("pre");
  result.id = name;
  result.textContent = canvas.toDataURL("image/png").split(",")[1];
  document.body.append(result);
}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrome", required=True, type=Path, help="Path to Chrome or Chromium")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path)
    args = parser.parse_args()
    board = ET.parse(ART / "Brett.svg").getroot()
    coordinates = board.find("*[@id='koordinaten']")
    if coordinates is not None:
        board.remove(coordinates)  # Tk labels stay upright in either orientation.
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    sources = [ET.tostring(board), *((ART / "Figuren" / name).read_bytes() for name in PIECE_FILE_NAMES)]
    images = "\n".join(f'<img src="data:image/svg+xml;base64,{base64.b64encode(data).decode("ascii")}">'
                       for data in sources)
    frames = {"board": board_frame(), "plate": plate_frame()}
    matrix = [value * REFERENCE_PIXELS for value in PROJECTION]
    with tempfile.TemporaryDirectory(prefix="cc-marble-tk-") as directory:
        work = Path(directory)
        page = work / "export.html"
        page.write_text(
            f"<meta charset=utf-8>{images}<script>const frames={json.dumps(frames)},"
            f"matrix={json.dumps(matrix)},border={BORDER},diameter={PLATE_SIZE};"
            f"window.addEventListener('load',()=>{{{SCRIPT}}});</script>",
            encoding="utf-8",
        )
        result = subprocess.run(
            [str(args.chrome), "--headless", "--no-first-run", "--disable-background-networking",
             "--disable-gpu", f"--user-data-dir={work / 'profile'}", "--dump-dom", page.as_uri()],
            capture_output=True, check=True, timeout=90,
        )
        atlases = {}
        for name in ("white", "black", "plates"):
            png = re.search(rb'<pre id="' + name.encode("ascii") + rb'">([A-Za-z0-9+/=]+)</pre>', result.stdout)
            if png is None:
                parser.error(f"Chromium did not render {name}.")
            atlases[name] = base64.b64decode(png[1], validate=True)
        args.output.mkdir(parents=True, exist_ok=True)
        for name, png in atlases.items():
            (args.output / f"{name}.png").write_bytes(png)


if __name__ == "__main__":
    main()
