"""Compare optional Tk/CairoSVG and QtSvg render paths using a local fixture."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import argparse
import base64
import json
import statistics
import sys
import time
import tkinter as tk
from pathlib import Path
from typing import Callable


SVG_FIXTURE = b"""<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
<path d="M32 5c-5 0-9 4-9 9 0 3 1 5 3 7l-4 9H17v6h30v-6h-5l-4-9c2-2 3-4 3-7 0-5-4-9-9-9zm-9 36-4 10h26l-4-10H23zm-7 13h32v5H16z"
fill="#e9b91d" stroke="#181818" stroke-width="2" stroke-linejoin="round"/>
</svg>"""
RENDER_SIZES = (48, 72, 96)


def _measure(function: Callable[[], object], repeats: int) -> dict[str, float]:
    for _ in range(8):
        function()
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        function()
        samples.append((time.perf_counter() - started) * 1000)
    samples.sort()
    return {
        "median_ms": round(statistics.median(samples), 3),
        "p95_ms": round(samples[int(0.95 * (len(samples) - 1))], 3),
        "max_ms": round(samples[-1], 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=100)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/cc-svg-backend-results"),
        help="directory for rendered PNGs and benchmark.json",
    )
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be a positive integer")

    import cairosvg
    from PIL import Image, ImageChops, ImageStat
    from PySide6 import __version__ as pyside_version
    from PySide6.QtCore import QByteArray, Qt
    from PySide6.QtGui import QImage, QPainter, QPixmap
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication, QLabel

    args.output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    root = tk.Tk()
    root.withdraw()
    canvas = tk.Canvas(root, width=100, height=100, highlightthickness=0)
    canvas.pack()
    label = QLabel()
    label.resize(100, 100)
    tk_image: tk.PhotoImage | None = None

    def cairo_display(size: int) -> tuple[bytes, tk.PhotoImage]:
        nonlocal tk_image
        png = cairosvg.svg2png(
            bytestring=SVG_FIXTURE,
            output_width=size,
            output_height=size,
        )
        tk_image = tk.PhotoImage(
            master=root,
            data=base64.b64encode(png).decode("ascii"),
            format="png",
        )
        canvas.delete("all")
        canvas.create_image(0, 0, image=tk_image, anchor="nw")
        root.update_idletasks()
        return png, tk_image

    def qt_display(size: int, renderer: QSvgRenderer) -> QImage:
        image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        label.setPixmap(QPixmap.fromImage(image))
        app.processEvents()
        return image

    results: dict[str, object] = {
        "python": sys.version.split()[0],
        "cairosvg": cairosvg.__version__,
        "pyside_qt": pyside_version,
        "repeats_per_case": args.repeats,
        "fixture": "self-authored geometric pawn SVG; no project assets",
        "sizes_px": list(RENDER_SIZES),
        "measurements": {},
    }
    measurements = results["measurements"]
    assert isinstance(measurements, dict)

    try:
        for size in RENDER_SIZES:
            renderer = QSvgRenderer(QByteArray(SVG_FIXTURE))
            measurements[str(size)] = {
                "cairosvg_parse_rasterize_tk_photoimage": _measure(
                    lambda: cairo_display(size), args.repeats
                ),
                "qt_fresh_renderer_rasterize_pixmap": _measure(
                    lambda: qt_display(size, QSvgRenderer(QByteArray(SVG_FIXTURE))),
                    args.repeats,
                ),
                "qt_reused_renderer_rasterize_pixmap": _measure(
                    lambda: qt_display(size, renderer), args.repeats
                ),
            }
            cairo_png, _ = cairo_display(size)
            cairo_path = args.output / f"cairosvg-{size}.png"
            qt_path = args.output / f"qt-svg-{size}.png"
            cairo_path.write_bytes(cairo_png)
            qt_display(size, renderer).save(str(qt_path), "PNG")

            cached_qt = QPixmap.fromImage(qt_display(size, renderer))
            current_tk_image = tk_image
            assert current_tk_image is not None
            measurements[str(size)]["cached_tk_canvas_attach"] = _measure(
                lambda: (
                    canvas.delete("all"),
                    canvas.create_image(0, 0, image=current_tk_image, anchor="nw"),
                    root.update_idletasks(),
                ),
                args.repeats,
            )
            measurements[str(size)]["cached_qt_label_attach"] = _measure(
                lambda: (label.setPixmap(cached_qt), app.processEvents()),
                args.repeats,
            )

            left = Image.open(cairo_path).convert("RGBA")
            right = Image.open(qt_path).convert("RGBA")
            difference = ImageChops.difference(left, right).convert("RGB")
            image_stats = ImageStat.Stat(difference)
            measurements[str(size)]["pixel_difference"] = {
                "mean_channel_delta": [round(value, 4) for value in image_stats.mean],
                "max_channel_delta": max(
                    difference.getextrema()[channel][1] for channel in range(3)
                ),
            }
    finally:
        root.destroy()

    output_path = args.output / "benchmark.json"
    output_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(output_path.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
