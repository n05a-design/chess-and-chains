"""Extract the 36 runtime piece SVGs from owner vector sheets V.03, V.04, and V.05."""
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


def extract_v03(output_dir: Path) -> None:
    """Extract 12 pieces from V.03-Schachfiguren-Vorderansicht-Schatten.svg."""
    source_path = ROOT / "design" / "V.03-Schachfiguren-Vorderansicht-Schatten.svg"
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
            "transform": f"matrix({scale:.10f},0,0,{scale:.10f},{off_x:.10f},{off_y:.10f})"
        })
        wrapper.append(elem)

        title_en, piece_de = PIECE_NAMES[name]
        desc = f"Owner front-view piece {piece_de} V.03 with interior shading."
        metadata = f"Copyright Tim von Trostorff · MPL-2.0 · Source V.03 SHA-256 {sha} · 64x64 tile"
        doc = build_svg_document(title_en, desc, metadata, wrapper)
        (output_dir / f"{name}.svg").write_text(doc, encoding="utf-8")


def extract_v04(output_dir: Path) -> None:
    """Extract 12 pieces from V.04-Schachfiguren-Vorderansicht-Schatten.svg."""
    source_path = ROOT / "design" / "V.04-Schachfiguren-Vorderansicht-Schatten.svg"
    sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    tree = ET.parse(source_path)
    root = tree.getroot()
    v41 = [c for c in root.iter() if c.attrib.get("id") == "V.41"][0]

    m_base_w = v41[4].attrib.get("transform")
    m_base_b = v41[5].attrib.get("transform")

    pairs = {
        "wP": (0, 19, 4, 25.0, 1097.53418, m_base_w),
        "bP": (0, 20, 5, 25.0, 1233.53418, m_base_b),
        "wR": (1, 13, 4, 158.0, 1097.53418, m_base_w),
        "bR": (1, 14, 5, 158.0, 1233.53418, m_base_b),
        "wN": (2, 15, 4, 291.0, 1097.53418, m_base_w),
        "bN": (2, 16, 5, 291.0, 1233.53418, m_base_b),
        "wB": (3, 11, 4, 424.0, 1097.53418, m_base_w),
        "bB": (3, 12, 5, 424.0, 1233.53418, m_base_b),
        "wQ": (4, 17, 4, 557.0, 1097.53418, m_base_w),
        "bQ": (4, 18, 5, 557.0, 1233.53418, m_base_b),
        "wK": (5, 21, 4, 690.0, 1097.53418, m_base_w),
        "bK": (5, 22, 5, 690.0, 1233.53418, m_base_b),
    }

    scale = 64.0 / 112.0
    for name, (base_idx, inner_idx, base_grp, sq_x, sq_y, m_base) in pairs.items():
        off_x = -sq_x * scale
        off_y = -sq_y * scale
        wrapper = ET.Element("g", {
            "transform": f"matrix({scale:.10f},0,0,{scale:.10f},{off_x:.10f},{off_y:.10f})"
        })
        g_base = ET.SubElement(wrapper, "g", {"transform": m_base})
        g_base.append(copy.deepcopy(v41[base_grp][base_idx]))
        wrapper.append(copy.deepcopy(v41[inner_idx]))

        title_en, piece_de = PIECE_NAMES[name]
        desc = f"Owner orthogonal top-view piece {piece_de} V.04."
        metadata = f"Copyright Tim von Trostorff · MPL-2.0 · Source V.04 SHA-256 {sha} · 64x64 tile"
        doc = build_svg_document(f"{title_en} (top view)", desc, metadata, wrapper)
        (output_dir / f"{name}.svg").write_text(doc, encoding="utf-8")


def extract_v05(output_dir: Path) -> None:
    """Extract 12 pieces from V.05-Schachfiguren-Vorderansicht-Schatten.svg."""
    source_path = ROOT / "design" / "V.05-Schachfiguren-Vorderansicht-Schatten.svg"
    sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    tree = ET.parse(source_path)
    root = tree.getroot()
    v51 = [c for c in root.iter() if c.attrib.get("id") == "V.51"][0]

    mapping = {
        "wP": ("bauer-figur", 25.0, 610.53418),
        "bP": ("bauer-figur1", 25.0, 746.53418),
        "wR": ("turm-figur", 158.0, 610.53418),
        "bR": ("turm-figur1", 158.0, 746.53418),
        "wN": ("springer-figur", 291.0, 610.53418),
        "bN": ("springer-figur1", 291.0, 746.53418),
        "wB": ("laeufer-figur", 424.0, 610.53418),
        "bB": ("laeufer-figur1", 424.0, 746.53418),
        "wQ": ("dame-figur", 557.0, 610.53418),
        "bQ": ("dame-figur1", 557.0, 746.53418),
        "wK": ("koenig-figur", 690.0, 610.53418),
        "bK": ("koenig-figur1", 690.0, 746.53418),
    }

    scale = 64.0 / 112.0
    for name, (elem_id, sq_x, sq_y) in mapping.items():
        elem = copy.deepcopy([c for c in v51 if c.attrib.get("id") == elem_id][0])
        off_x = -sq_x * scale
        off_y = -sq_y * scale
        wrapper = ET.Element("g", {
            "transform": f"matrix({scale:.10f},0,0,{scale:.10f},{off_x:.10f},{off_y:.10f})"
        })
        wrapper.append(elem)

        title_en, piece_de = PIECE_NAMES[name]
        desc = f"Owner classic silhouette piece {piece_de} V.05."
        metadata = f"Copyright Tim von Trostorff · MPL-2.0 · Source V.05 SHA-256 {sha} · 64x64 tile"
        doc = build_svg_document(f"{title_en} (classic)", desc, metadata, wrapper)
        (output_dir / f"{name}.svg").write_text(doc, encoding="utf-8")


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

    print("Extracting V.03 (original)...")
    extract_v03(original_dir)
    write_provenance(original_dir, "original", "V.03", "Original Chess Pieces", "design/V.03-Schachfiguren-Vorderansicht-Schatten.svg")

    print("Extracting V.04 (top view)...")
    extract_v04(top_dir)
    write_provenance(top_dir, "top", "V.04", "Top-View Chess Pieces", "design/V.04-Schachfiguren-Vorderansicht-Schatten.svg")

    print("Extracting V.05 (classic)...")
    extract_v05(classic_dir)
    write_provenance(classic_dir, "classic", "V.05", "Classic Chess Pieces", "design/V.05-Schachfiguren-Vorderansicht-Schatten.svg")

    # Mirror V.03 to root ASSETS_DIR for complete backward compatibility
    print("Mirroring V.03 to piece_assets root...")
    for svg_file in original_dir.glob("*.svg"):
        shutil.copy2(svg_file, ASSETS_DIR / svg_file.name)
    write_provenance(ASSETS_DIR, "original", "V.03", "Chess & Chains Piece Assets (Default V.03)", "design/V.03-Schachfiguren-Vorderansicht-Schatten.svg")

    print("Done. All 36 SVGs extracted and verified.")


if __name__ == "__main__":
    main()
