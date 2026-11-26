"""Logo masters, derived brand resources and the stdlib renderer (no Tk needed)."""
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import csv
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chess_and_chains.ui import brand_raster as br  # noqa: E402

_spec = importlib.util.spec_from_file_location("build_brand_assets", ROOT / "scripts/build_brand_assets.py")
build_brand_assets = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_brand_assets)  # type: ignore[union-attr]

MASTER_DIR = ROOT / "design/01_Logo/svg"
RUNTIME = ROOT / "src/chess_and_chains/ui/brand_assets"
PUBLIC = ROOT / "assets/branding"
BLUE, YELLOW, ICON_YELLOW, BOARD_DARK = (36, 71, 216), (244, 196, 0), (255, 220, 11), (23, 25, 32)


def _doc(role: str) -> br.Document:
    return br.parse_svg((MASTER_DIR / build_brand_assets.MASTERS[role]["file"]).read_bytes())


def _colours(rows: list[bytes], min_alpha: int = 255) -> set[tuple[int, int, int]]:
    return {tuple(row[i:i + 3]) for row in rows for i in range(0, len(row), 4) if row[i + 3] >= min_alpha}


def _alpha(rows: list[bytes], x: int, y: int) -> int:
    return rows[y][x * 4 + 3]


class MasterTests(unittest.TestCase):
    def test_three_masters_exist_unchanged_and_lf_only(self):
        for role, info in build_brand_assets.MASTERS.items():
            content = (MASTER_DIR / info["file"]).read_bytes()
            self.assertEqual(sha256(content).hexdigest(), info["sha256"], role)
            self.assertNotIn(b"\r\n", content)
            self.assertNotIn(b"<!ENTITY", content)

    def test_role_mapping(self):
        self.assertEqual(
            {role: info["file"] for role, info in build_brand_assets.MASTERS.items()},
            {"in_app": "Logo_Chess-&-Chains-01.svg",
             "internal_brand": "Logo_Chess-&-Chains-02.svg",
             "app_icon": "Logo_Chess-&-Chains-03.svg"},
        )

    def test_master_colours_match_brand_tokens(self):
        tokens = json.loads((ROOT / "docs/design/brand-tokens.json").read_text(encoding="utf-8"))
        logo = tokens["logo"]["colors"]
        expected = {tuple(int(logo[k][i:i + 2], 16) for i in (1, 3, 5)) for k in logo}
        found = {s.fill for role in ("in_app", "internal_brand", "app_icon") for s in _doc(role).shapes}
        found |= {s.stroke for role in ("in_app", "app_icon") for s in _doc(role).shapes if s.stroke}
        self.assertEqual(found, expected)

    def test_nested_matrix_transforms_and_square_viewbox(self):
        doc = _doc("in_app")
        self.assertEqual(doc.view_box, (0.0, 0.0, 842.0, 842.0))
        links, separators = br.signet_roles(doc)
        self.assertEqual({s.fill for s in links}, {YELLOW, BLUE})
        self.assertTrue(all(s.stroke == (0, 0, 0) and s.fill_rule == "evenodd" for s in separators))
        x, y, w, h = br.bounds([s.subpaths for s in doc.shapes])
        self.assertTrue(0 < x and 0 < y and x + w < 842 and y + h < 842)


class GeneratorTests(unittest.TestCase):
    def test_check_mode_reports_no_differences(self):
        outputs = build_brand_assets.build()
        self.assertEqual(build_brand_assets.differences(outputs), [])

    def test_runtime_and_public_svgs_are_byte_copies_of_masters(self):
        pairs = {
            RUNTIME / "signet.svg": "in_app", RUNTIME / "brand-emblem.svg": "internal_brand",
            RUNTIME / "app-icon.svg": "app_icon", PUBLIC / "icons/chess-and-chains.svg": "app_icon",
            PUBLIC / "favicon/favicon.svg": "app_icon",
        }
        for path, role in pairs.items():
            self.assertEqual(sha256(path.read_bytes()).hexdigest(), build_brand_assets.MASTERS[role]["sha256"], path)

    def test_manifest_records_masters_and_pixel_hashes(self):
        manifest = json.loads((PUBLIC / "brand-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["masters"]["app_icon"]["sha256"], build_brand_assets.MASTERS["app_icon"]["sha256"])
        entry = next(e for e in manifest["outputs"] if e["path"].endswith("chess-and-chains-512.png"))
        rows = br.decode_png((ROOT / entry["path"]).read_bytes())
        self.assertEqual(entry["pixel_sha256"], sha256(b"".join(rows)).hexdigest())
        self.assertEqual(entry["master"], "Logo_Chess-&-Chains-03.svg")

    def test_icon_resources_complete(self):
        ico = br.decode_ico((PUBLIC / "icons/chess-and-chains.ico").read_bytes())
        self.assertEqual(sorted(ico), [16, 24, 32, 48, 64, 128, 256])
        self.assertEqual(sorted(br.decode_ico((RUNTIME / "app-icon.ico").read_bytes())), sorted(ico))
        self.assertEqual(sorted(br.decode_ico((PUBLIC / "favicon/favicon.ico").read_bytes())), [16, 32, 48])
        icns = br.decode_icns((PUBLIC / "icons/chess-and-chains.icns").read_bytes())
        self.assertEqual(set(icns), {kind for kind, _ in br.ICNS_TYPES})
        self.assertEqual(len(icns[b"ic10"]), 1024)
        for size in (16, 24, 32, 48, 64, 96, 128, 192, 256, 512, 1024):
            rows = br.decode_png((PUBLIC / f"icons/chess-and-chains-{size}.png").read_bytes())
            self.assertEqual((len(rows[0]) // 4, len(rows)), (size, size))

    def test_app_icon_keeps_original_colours_and_transparent_corners(self):
        rows = br.decode_png((PUBLIC / "icons/chess-and-chains-512.png").read_bytes())
        colours = _colours(rows)
        for colour in (ICON_YELLOW, BOARD_DARK, BLUE, YELLOW, (255, 255, 255)):
            self.assertIn(colour, colours)
        for x, y in ((0, 0), (511, 0), (0, 511), (511, 511)):
            self.assertEqual(_alpha(rows, x, y), 0)
        self.assertEqual(_alpha(rows, 256, 2), 255)  # yellow frame reaches the canvas edge

    def test_small_icons_keep_a_recognisable_link(self):
        for size in (16, 32):
            rows = br.decode_png((PUBLIC / f"icons/chess-and-chains-{size}.png").read_bytes())
            blueish = [px for px in _colours(rows, 200) if px[2] > 150 and px[0] < 120]
            self.assertTrue(blueish, f"no blue link pixels at {size}px")
            self.assertEqual(_alpha(rows, size // 2, size // 2), 255)

    def test_macos_icon_has_transparent_apple_grid_margin(self):
        rows = br.decode_png((PUBLIC / "icons/chess-and-chains-macos-1024.png").read_bytes())
        self.assertEqual(_alpha(rows, 90, 512), 0)
        self.assertEqual(_alpha(rows, 104, 512), 255)
        self.assertEqual(_alpha(rows, 512, 512), 255)

    def test_emblem_is_full_colour_without_logo03_frame(self):
        emblem = _doc("internal_brand")
        icon = _doc("app_icon")
        board = lambda d: br.bounds([s.subpaths for s in d.shapes if s.fill == BOARD_DARK])  # noqa: E731
        # Logo 02 scales the board towards the edge; Logo 03 keeps the wide yellow frame.
        self.assertGreater(board(emblem)[2], board(icon)[2] * 1.1)
        rows = br.decode_png((RUNTIME / "brand-emblem.png").read_bytes())
        self.assertEqual(len(rows), 96)
        self.assertIn(ICON_YELLOW, _colours(rows))


class SignetRenderingTests(unittest.TestCase):
    def setUp(self):
        self.doc = _doc("in_app")
        self.box = br.signet_visible_box(self.doc)

    def _render(self, colour=(7, 103, 199), height=120, layers=None):
        width = round(self.box[2] * height / self.box[3])
        layers = layers or br.signet_layers(self.doc, (colour, colour))
        return br.render(layers, br.Frame.fit(self.box, width, height))

    def test_visible_box_excludes_transparent_viewbox_margins(self):
        x, y, w, h = self.box
        self.assertAlmostEqual(w / h, 1.508, places=2)  # Logo 01 V.2
        self.assertGreater(x, 60)
        self.assertLess(w, 842 * 0.9)

    def test_tinted_signet_is_monochrome_transparent_and_not_clipped(self):
        rows = self._render()
        self.assertEqual(_colours(rows, 1), {(7, 103, 199)})
        self.assertEqual(_alpha(rows, 0, 0), 0)
        height, width = len(rows), len(rows[0]) // 4
        for edge in (rows[0], rows[-1]):
            self.assertTrue(any(edge[i + 3] for i in range(0, len(edge), 4)), "ink must touch top and bottom")
        self.assertTrue(any(_alpha(rows, 0, y) for y in range(height)))
        self.assertTrue(any(_alpha(rows, width - 1, y) for y in range(height)))

    def test_separator_bands_become_transparent_cut_outs(self):
        cut = self._render()
        merged = self._render(layers=[layer for layer in br.signet_layers(self.doc, ((7, 103, 199),) * 2)
                                      if layer.mode == "over"])
        opaque = lambda rows: sum(1 for r in rows for i in range(3, len(r), 4) if r[i] > 128)  # noqa: E731
        # Without the cut-outs both links fuse at the overpass; with them, a visible gap remains.
        self.assertGreater(opaque(merged) - opaque(cut), 150)

    def test_alpha_mask_is_identical_for_every_theme_colour(self):
        masks = []
        for colour in ((7, 103, 199), (14, 116, 144), (255, 192, 56), (43, 43, 43)):
            masks.append([bytes(r[i] for i in range(3, len(r), 4)) for r in self._render(colour, 48)])
        self.assertTrue(all(mask == masks[0] for mask in masks))

    def test_very_small_signet_still_renders(self):
        rows = self._render(height=8)
        self.assertEqual(len(rows), 8)
        self.assertTrue(_colours(rows, 1))

    def test_old_orthogonal_signet_is_gone(self):
        for path in (RUNTIME / "signet.svg", RUNTIME / "app-icon.svg"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("M40 31 Q46 31", text)
            self.assertNotIn("Local design candidate", text)


class NegativeTests(unittest.TestCase):
    def test_unsupported_or_unsafe_svgs_are_rejected(self):
        bad = {
            "entity": b'<!DOCTYPE svg [<!ENTITY x "y">]><svg viewBox="0 0 1 1"/>',
            "image": b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><image href="x.png"/></svg>',
            "rotate": (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">'
                       b'<g transform="rotate(4)"><path d="M0 0L1 1Z" style="fill:white"/></g></svg>'),
            "arc": (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">'
                    b'<path d="M0 0A1 1 0 0 0 1 1Z" style="fill:white"/></svg>'),
            "broken": b'<svg viewBox="0 0 1 1"><path',
            "no-viewbox": b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L1 1Z"/></svg>',
        }
        for name, content in bad.items():
            with self.subTest(name), self.assertRaises(br.UnsupportedSvg):
                br.parse_svg(content)

    def test_signet_structure_change_is_rejected(self):
        content = (MASTER_DIR / "Logo_Chess-&-Chains-01.svg").read_bytes().replace(b"fill:rgb(36,71,216)", b"fill:rgb(1,2,3)")
        with self.assertRaises(br.UnsupportedSvg):
            br.signet_roles(br.parse_svg(content))

    def test_missing_or_changed_master_blocks_the_generator(self):
        with tempfile.TemporaryDirectory() as tmp:
            masters = Path(tmp)
            for info in build_brand_assets.MASTERS.values():
                shutil.copy(MASTER_DIR / info["file"], masters / info["file"])
            with patch.object(build_brand_assets, "MASTER_DIR", masters):
                (masters / "Logo_Chess-&-Chains-02.svg").write_bytes(b"<svg/>")
                with self.assertRaisesRegex(build_brand_assets.Blocked, "differs from the registered master"):
                    build_brand_assets.load_masters()
                (masters / "Logo_Chess-&-Chains-02.svg").unlink()
                with self.assertRaisesRegex(build_brand_assets.Blocked, "missing master"):
                    build_brand_assets.load_masters()
                self.assertEqual(build_brand_assets.main(["--check"]), 2)

    def test_check_detects_outdated_missing_and_unexpected_outputs(self):
        outputs = build_brand_assets.build()
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp)
            for rel, item in outputs.items():
                (fake / rel).parent.mkdir(parents=True, exist_ok=True)
                (fake / rel).write_bytes(item["content"])
            stale = "assets/branding/icons/chess-and-chains-32.png"
            (fake / stale).write_bytes(br.encode_png([b"\0\0\0\0" * 32] * 32))
            (fake / "assets/branding/icons/chess-and-chains.ico").unlink()
            (fake / "assets/branding/icons/old-logo.png").write_bytes(b"x")
            with patch.multiple(build_brand_assets, ROOT=fake, RUNTIME_DIR=fake / "src/chess_and_chains/ui/brand_assets",
                                PUBLIC_DIR=fake / "assets/branding"):
                problems = build_brand_assets.differences(outputs)
        self.assertIn(f"outdated: {stale}", problems)
        self.assertIn("missing: assets/branding/icons/chess-and-chains.ico", problems)
        self.assertIn("unexpected file: assets/branding/icons/old-logo.png", problems)


class IntegrationReferenceTests(unittest.TestCase):
    def test_readmes_use_logo03_export_relatively(self):
        for name in ("README.md", "README.de.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn('src="assets/branding/icons/chess-and-chains-512.png"', text, name)
            self.assertIn('width="96"', text)
            self.assertIn("actions/workflows/checks.yml/badge.svg", text)

    def test_social_preview_export(self):
        path = ROOT / "marketing/social/chess-and-chains-social-preview.png"
        content = path.read_bytes()
        self.assertLess(len(content), 1_000_000)
        width, height = int.from_bytes(content[16:20], "big"), int.from_bytes(content[20:24], "big")
        self.assertEqual((width, height), (1280, 640))
        self.assertTrue((ROOT / "marketing/source/chess-and-chains-social-preview.svg").is_file())

    def test_packaging_references_generated_icons(self):
        macos = (ROOT / "packaging/macos/build_app.py").read_text(encoding="utf-8")
        self.assertIn("assets/branding/icons/chess-and-chains.icns", macos.replace("\\", "/").replace('" / "', "/"))
        self.assertIn('BUNDLE_ID = "de.n05a.chessandchains"', macos)
        desktop = (ROOT / "packaging/linux/chess-and-chains.desktop").read_text(encoding="utf-8")
        self.assertIn("Icon=chess-and-chains", desktop)
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('"brand_assets/*.ico"', pyproject)

    def test_asset_register_lists_masters_and_runtime_logo_files(self):
        with (ROOT / "docs/design/ASSET_REGISTER.csv").open(encoding="utf-8", newline="") as stream:
            rows = {row["planned_path"]: row for row in csv.DictReader(stream)}
        for info in build_brand_assets.MASTERS.values():
            row = rows["design/01_Logo/svg/" + info["file"]]
            self.assertEqual(row["source_hash"], info["sha256"])
        for name in ("signet.svg", "signet.png", "brand-emblem.svg", "brand-emblem.png", "app-icon.svg",
                     "app-icon.png", "app-icon.ico", "app-icon-macos.png"):
            row = rows[f"src/chess_and_chains/ui/brand_assets/{name}"]
            self.assertEqual(row["source_hash"], sha256((RUNTIME / name).read_bytes()).hexdigest(), name)

    def test_logo_documentation_lists_master_hashes(self):
        text = (ROOT / "design/01_Logo/README.md").read_text(encoding="utf-8")
        for info in build_brand_assets.MASTERS.values():
            self.assertIn(info["sha256"], text)
        self.assertTrue(re.search(r"build_brand_assets\.py --check", text))


if __name__ == "__main__":
    unittest.main()
