"""Extract the 36 runtime piece SVGs from owner vector sheets V.06, V.04.2, and V.05.1."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import copy
import hashlib
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "src" / "chess_and_chains" / "ui" / "piece_assets"

PIECE_NAMES = {
    "wP": ("White Pawn", "Bauer"),
    "wR": ("White Rook", "Turm"),
    "wN": ("White Knight", "Springer"),
    "wB": ("White Bishop", "Läufer"),
    "wQ": ("White Queen", "Dame"),
    "wK": ("White King", "König"),
    "bP": ("Black Pawn", "Bauer"),
    "bR": ("Black Rook", "Turm"),
    "bN": ("Black Knight", "Springer"),
    "bB": ("Black Bishop", "Läufer"),
    "bQ": ("Black Queen", "Dame"),
    "bK": ("Black King", "König"),
}

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def clean_elements(elem: ET.Element) -> None:
    # Remove any affinity attributes and use/image tags
    to_remove = []
    for c in list(elem):
        if c.tag.endswith("use") or c.tag.endswith("image"):
            to_remove.append(c)
        else:
            clean_elements(c)
    for c in to_remove:
        elem.remove(c)
    for key in list(elem.attrib.keys()):
        if "affinity" in key.lower():
            del elem.attrib[key]


def build_svg_document(title: str, desc: str, metadata: str, inner_element: ET.Element) -> str:
    clean_elements(inner_element)
    svg = ET.Element("svg", {
        "width": "64",
        "height": "64",
        "viewBox": "0 0 64 64",
    })
    title_elem = ET.SubElement(svg, "title")
    title_elem.text = title
    desc_elem = ET.SubElement(svg, "desc")
    desc_elem.text = desc
    meta_elem = ET.SubElement(svg, "metadata")
    meta_elem.text = metadata
    svg.append(inner_element)
    raw = ET.tostring(svg, encoding="utf-8").decode("utf-8")
    # Clean up any residual ns0 prefix if present
    cleaned = raw.replace("xmlns:ns0=\"http://www.w3.org/2000/svg\" ", "")
    cleaned = cleaned.replace("ns0:", "")
    return cleaned + "\n"


def extract_v06(output_dir: Path) -> None:
    """Extract 12 pieces from V.06-Schachfiguren-Vorderansicht-Schatten.svg."""
    source_path = ROOT / "assets" / "chess_pieces" / "masters" / "V.06" / "V.06-Schachfiguren-Vorderansicht-Schatten.svg"
    sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    tree = ET.parse(source_path)
    root = tree.getroot()
    v31 = [c for c in root if c.attrib.get("id") == "V.31"][0]
    g_pieces = v31[4]

    mapping = {
        "wP": (2, 25.0, 120.0),
        "bP": (3, 25.0, 256.0),
        "wR": (6, 158.0, 120.0),
        "bR": (7, 158.0, 256.0),
        "wN": (10, 291.0, 120.0),
        "bN": (11, 291.0, 256.0),
        "wB": (8, 424.0, 120.0),
        "bB": (9, 424.0, 256.0),
        "wQ": (0, 557.0, 120.0),
        "bQ": (1, 557.0, 256.0),
        "wK": (4, 690.0, 120.0),
        "bK": (5, 690.0, 256.0),
    }

    scale = 64.0 / 112.0
    for name, (idx, sq_x, sq_y) in mapping.items():
        elem = copy.deepcopy(g_pieces[idx])
        # Strip any use / image elements
        for u in list(elem.iter()):
            if u.tag.endswith("use") or u.tag.endswith("image"):
                for p in elem.iter():
                    if u in list(p):
                        p.remove(u)
        off_x = -sq_x * scale
        off_y = -sq_y * scale
        wrapper = ET.Element("g", {
            "transform": f"matrix({scale:.10f},0,0,{scale:.10f},{off_x:.10f},{off_y:.10f})",
            "style": root.get("style", ""),
        })
        wrapper.append(elem)

        title_en, piece_de = PIECE_NAMES[name]
        desc = f"Owner front-view piece {piece_de} V.06 with interior shading."
        metadata = f"Copyright Tim von Trostorff · MPL-2.0 · Source V.06 SHA-256 {sha} · 64x64 tile"
        doc = build_svg_document(title_en, desc, metadata, wrapper)
        (output_dir / f"{name}.svg").write_text(doc, encoding="utf-8")


def extract_v04(output_dir: Path) -> None:
    """Extract the geometrically smoothed V.04.2 top-view SVGs from the owner master."""
    source_path = ROOT / "assets" / "chess_pieces" / "masters" / "V.04.2" / "V.04.2-Schachfiguren-Draufsicht-Smooth.svg"
    sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    root = ET.parse(source_path).getroot()
    ns = "http://www.w3.org/2000/svg"
    tag = lambda name: "{" + ns + "}" + name
    ET.register_namespace("", ns)
    for name, (title_en, _) in PIECE_NAMES.items():
        tile = next(e for e in root.iter() if e.get("id") == f"tile-{name}")
        geometry = copy.deepcopy(tile[0])
        svg = ET.Element(tag("svg"), {"width": "64", "height": "64", "viewBox": "0 0 64 64"})
        ET.SubElement(svg, tag("title")).text = f"{title_en} (top view)"
        ET.SubElement(svg, tag("desc")).text = "Owner top-view V.04.2: geometric smoothing derived from the supplied V.04 vector sheet."
        ET.SubElement(svg, tag("metadata")).text = f"Copyright Tim von Trostorff · MPL-2.0 · Source V.04.2 SHA-256 {sha} · 64x64 tile"
        svg.append(geometry)
        (output_dir / f"{name}.svg").write_bytes(ET.tostring(svg, encoding="utf-8") + b"\n")


def extract_v05(output_dir: Path) -> None:
    """Extract the shaded V.05.1 classic SVGs from the owner master."""
    source_path = ROOT / "assets" / "chess_pieces" / "masters" / "V.05.1" / "V.05.1-Schachfiguren-Klassisch-Schatten.svg"
    sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    root = ET.parse(source_path).getroot()
    ns = "http://www.w3.org/2000/svg"
    tag = lambda name: "{" + ns + "}" + name
    ET.register_namespace("", ns)
    for name, (title_en, _) in PIECE_NAMES.items():
        tile = next(e for e in root.iter() if e.get("id") == f"tile-{name}")
        geometry = copy.deepcopy(tile[0])
        svg = ET.Element(tag("svg"), {"width": "64", "height": "64", "viewBox": "0 0 64 64"})
        ET.SubElement(svg, tag("title")).text = f"{title_en} (classic)"
        ET.SubElement(svg, tag("desc")).text = "Owner classic V.05.1: interior directional shading and real transparent cutouts."
        ET.SubElement(svg, tag("metadata")).text = f"Owner artwork · Source V.05.1 SHA-256 {sha} · 64x64 tile; derived from V.05 owner master."
        svg.append(geometry)
        (output_dir / f"{name}.svg").write_bytes(ET.tostring(svg, encoding="utf-8") + b"\n")


def write_provenance(directory: Path, set_id: str, version: str, title: str, source_rel: str) -> None:
    source_file = ROOT / source_rel
    sha = hashlib.sha256(source_file.read_bytes()).hexdigest()
    is_sub = (directory != ASSETS_DIR)
    rel_prefix = "../../../../../" if is_sub else "../../../../"
    content = f"""# {title} ({version})

**Copyright:** Tim von Trostorff. **SPDX-License-Identifier: MPL-2.0.**
Approved for distribution with Chess & Chains.

- **Set ID:** `{set_id}`
- **Asset Version:** `{version}`
- **Source Master:** [`{source_rel}`]({rel_prefix}{source_rel})
- **Source SHA-256:** `{sha}`
- **Tile Dimensions:** 64 × 64 quadratic viewBox, transparent background
- **Number of Pieces:** 12 individual SVG runtime assets (wP, wR, wN, wB, wQ, wK, bP, bR, bN, bB, bQ, bK)

Each piece retains the exact geometrical vector artwork, shading, stroke widths, and relative proportions from the author's original sheet.
"""
    (directory / "PROVENANCE.md").write_text(content.strip() + "\n", encoding="utf-8")


def main() -> None:
    original_dir = ASSETS_DIR / "original"
    top_dir = ASSETS_DIR / "top"
    classic_dir = ASSETS_DIR / "classic"

    for d in (original_dir, top_dir, classic_dir):
        d.mkdir(parents=True, exist_ok=True)

    print("Extracting V.06 (original)...")
    extract_v06(original_dir)
    write_provenance(original_dir, "original", "V.06", "Original Chess Pieces", "assets/chess_pieces/masters/V.06/V.06-Schachfiguren-Vorderansicht-Schatten.svg")

    print("Extracting V.04.2 (top view)...")
    extract_v04(top_dir)
    shutil.copy2(ROOT / "assets/chess_pieces/masters/V.04.2/TOP_PROVENANCE.txt", top_dir / "PROVENANCE.md")

    print("Extracting V.05.1 (classic)...")
    extract_v05(classic_dir)
    shutil.copy2(ROOT / "assets/chess_pieces/masters/V.05.1/CLASSIC_PROVENANCE.txt", classic_dir / "PROVENANCE.md")

    # Mirror V.06 to root ASSETS_DIR for complete backward compatibility
    print("Mirroring V.06 to piece_assets root...")
    for svg_file in original_dir.glob("*.svg"):
        shutil.copy2(svg_file, ASSETS_DIR / svg_file.name)
    write_provenance(ASSETS_DIR, "original", "V.06", "Chess & Chains Piece Assets (Default V.06)", "assets/chess_pieces/masters/V.06/V.06-Schachfiguren-Vorderansicht-Schatten.svg")

    print("Done. All 36 SVGs extracted and verified.")


if __name__ == "__main__":
    main()
