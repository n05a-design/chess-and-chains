#!/usr/bin/env python3
"""Generate visual verification proof sheets for extracted chess piece sets.

Renders all 12 pieces for each set (V.03 Original, V.04 Top view, V.05 Classic)
on alternating light and dark chess squares for visual comparison with reference JPGs.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "src" / "chess_and_chains" / "ui" / "piece_assets"
OUT_DIR = ROOT / "assets" / "chess_pieces" / "proof_sheets"

PIECE_COLS = ["P", "R", "N", "B", "Q", "K"]
PIECE_LABELS_DE = ["Bauer", "Turm", "Springer", "Läufer", "Dame", "König"]

SETS = [
    ("original", "V.03", "Original – Vorderansicht"),
    ("top", "V.04", "Draufsicht – Orthogonal"),
    ("classic", "V.05", "Klassisch – Silhouette"),
]

# Colors matching the owner reference JPG overview sheets
LIGHT_SQUARE = "#E5D9C4"
DARK_SQUARE = "#8E7558"
BORDER_COLOR = "#000000"
SVG_NS = "http://www.w3.org/2000/svg"


def generate_svg_proof_sheet(set_id: str, version: str, title: str, out_path: Path) -> None:
    set_dir = ASSETS_DIR / set_id
    width = 828
    height = 437

    root = ET.Element("svg", {
        "xmlns": SVG_NS,
        "width": str(width),
        "height": str(height),
        "viewBox": f"0 0 {width} {height}",
    })

    # Background
    ET.SubElement(root, "rect", {
        "x": "0", "y": "0", "width": str(width), "height": str(height),
        "fill": "#FFFFFF",
    })

    # Title & subtitle
    title_text = ET.SubElement(root, "text", {
        "x": "25", "y": "45",
        "font-family": "Helvetica, Arial, sans-serif",
        "font-size": "24",
        "font-weight": "bold",
        "fill": "#000000",
    })
    title_text.text = f"Chess & Chains • Asset-Prüfung {version}"

    sub_text = ET.SubElement(root, "text", {
        "x": "25", "y": "72",
        "font-family": "Helvetica, Arial, sans-serif",
        "font-size": "13",
        "fill": "#333333",
    })
    sub_text.text = f"{title} · Extraktion auf 64×64 Einheitsfeld · Visuelle Referenz"

    sq_size = 112
    margin_x = 25
    gap_x = 21  # (828 - 2*25 - 6*112) / 5 = (778 - 672) / 5 = 106 / 5 = 21.2 -> 21
    y_row1 = 120
    y_row2 = 256

    # Column headers
    for col_idx, label in enumerate(PIECE_LABELS_DE):
        x = margin_x + col_idx * (sq_size + gap_x)
        lbl_elem = ET.SubElement(root, "text", {
            "x": str(x), "y": str(y_row1 - 12),
            "font-family": "Helvetica, Arial, sans-serif",
            "font-size": "14",
            "font-weight": "bold",
            "fill": "#000000",
        })
        lbl_elem.text = label

    # Rows: Row 1 = White, Row 2 = Black
    rows = [
        ("w", y_row1, [LIGHT_SQUARE, DARK_SQUARE, LIGHT_SQUARE, DARK_SQUARE, LIGHT_SQUARE, DARK_SQUARE]),
        ("b", y_row2, [DARK_SQUARE, LIGHT_SQUARE, DARK_SQUARE, LIGHT_SQUARE, DARK_SQUARE, LIGHT_SQUARE]),
    ]

    for color_prefix, y, square_colors in rows:
        for col_idx, piece_char in enumerate(PIECE_COLS):
            x = margin_x + col_idx * (sq_size + gap_x)
            fill_color = square_colors[col_idx]

            # Square background
            ET.SubElement(root, "rect", {
                "x": str(x), "y": str(y),
                "width": str(sq_size), "height": str(sq_size),
                "fill": fill_color,
                "stroke": BORDER_COLOR,
                "stroke-width": "1.5",
            })

            # Load piece SVG and embed
            piece_file = set_dir / f"{color_prefix}{piece_char}.svg"
            if piece_file.exists():
                tree = ET.parse(piece_file)
                piece_root = tree.getroot()
                scale = sq_size / 64.0
                g_wrap = ET.SubElement(root, "g", {
                    "transform": f"translate({x}, {y}) scale({scale})",
                })
                for child in piece_root:
                    g_wrap.append(child)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tree_out = ET.ElementTree(root)
    ET.indent(tree_out, space="  ")
    tree_out.write(out_path, encoding="utf-8", xml_declaration=True)


def generate_png_from_svg(svg_path: Path, png_path: Path) -> bool:
    """Render SVG to PNG via headless Chrome or fallback to Tk PhotoImage."""
    # Try Chrome first for full SVG standard support (fonts, text, nested transforms)
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome):
        try:
            abs_url = f"file://{svg_path.resolve()}"
            subprocess.run([
                chrome, "--headless", "--disable-gpu",
                "--hide-scrollbars",
                "--window-size=828,437",
                f"--screenshot={png_path}",
                abs_url,
            ], check=True, capture_output=True)
            if png_path.exists() and png_path.stat().st_size > 5000:
                return True
        except Exception:
            pass

    # Fallback to Tk 9
    try:
        root = tk.Tk()
        root.withdraw()
        img = tk.PhotoImage(file=str(svg_path), format="svg")
        ppm_path = png_path.with_suffix(".ppm")
        img.write(str(ppm_path), format="ppm")
        root.destroy()

        from PIL import Image
        with Image.open(ppm_path) as im:
            im.save(png_path, "PNG")
        ppm_path.unlink(missing_ok=True)
        return True
    except Exception:
        pass
    return False


def main() -> int:
    print(f"Generating visual proof sheets in: {OUT_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for set_id, version, title in SETS:
        svg_file = OUT_DIR / f"proof_sheet_{set_id}_{version.lower().replace('.', '')}.svg"
        png_file = OUT_DIR / f"proof_sheet_{set_id}_{version.lower().replace('.', '')}.png"

        generate_svg_proof_sheet(set_id, version, title, svg_file)
        print(f"  [SVG] {svg_file.name} generated ({svg_file.stat().st_size} bytes)")

        if generate_png_from_svg(svg_file, png_file):
            print(f"  [PNG] {png_file.name} generated ({png_file.stat().st_size} bytes)")
        else:
            print(f"  [PNG] Could not rasterize {png_file.name}")

    print("All proof sheets generated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
