#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Derive every Chess & Chains logo resource from the three owner masters.

Masters (single source, never edited by this script)::

    design/01_Logo/svg/Logo_Chess-&-Chains-01.svg   in-app signet, theme-tinted at runtime
    design/01_Logo/svg/Logo_Chess-&-Chains-02.svg   full-colour internal brand emblem (About)
    design/01_Logo/svg/Logo_Chess-&-Chains-03.svg   official app icon and public identity

Usage::

    python3 -B scripts/build_brand_assets.py           # write / refresh all outputs
    python3 -B scripts/build_brand_assets.py --check   # verify only, writes nothing

Rasters come from the standard-library renderer in
``src/chess_and_chains/ui/brand_raster.py``. ``--check`` compares decoded
pixels (PNG, ICO, ICNS) and exact bytes (SVG copies, manifest), because zlib
builds may compress identical pixels differently. The manifest records a
platform-independent pixel SHA-256 for every raster.

Exit codes: 0 ok, 1 outdated/missing outputs, 2 blocked (master missing,
changed or unsupported).
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chess_and_chains.ui import brand_raster as br  # noqa: E402

MASTER_DIR = ROOT / "design/01_Logo/svg"
RUNTIME_DIR = ROOT / "src/chess_and_chains/ui/brand_assets"
PUBLIC_DIR = ROOT / "assets/branding"
MANIFEST = PUBLIC_DIR / "brand-manifest.json"
GENERATOR_VERSION = 1

# Byte identity with the owner masters (LF checkout, see .gitattributes).
MASTERS: dict[str, dict[str, str]] = {
    "in_app": {
        "file": "Logo_Chess-&-Chains-01.svg",
        "sha256": "d133adb801f70b04f303331d35c8769ef988887c2a4272c03f20067dcd1a3f62",
    },
    "internal_brand": {
        "file": "Logo_Chess-&-Chains-02.svg",
        "sha256": "a2e1cb7854f76c2c9bd7078a9855cddf7bef6a7c1db0ca9d4e6819b725142c0e",
    },
    "app_icon": {
        "file": "Logo_Chess-&-Chains-03.svg",
        "sha256": "228a289fade583e92206aa9b69cd9f7b329640809f593a250373192fbb637618",
    },
}

ICON_SIZES = (16, 24, 32, 48, 64, 96, 128, 192, 256, 512, 1024)
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
FAVICON_ICO_SIZES = (16, 32, 48)
FAVICON_PNG_SIZES = (16, 32, 64, 192, 512)
RUNTIME_ICON_SIZES = (16, 32, 48, 64, 128)  # window/taskbar iconphoto set; 256 is app-icon.png
MACOS_SIZES = (16, 32, 64, 128, 256, 512, 1024)
# Apple icon grid: the 824 px body sits centred on a transparent 1024 px canvas.
MACOS_BODY_RATIO = 824.0 / 1024.0

# Wordmark files in brand_assets are not derived from the logo masters.
RUNTIME_UNMANAGED = {"wordmark.svg", "wordmark.png"}
PUBLIC_MANAGED_DIRS = ("icons", "favicon", "emblem", "signet")


class Blocked(Exception):
    """A master is missing, changed or uses unsupported SVG features."""


def load_masters() -> dict[str, tuple[bytes, br.Document]]:
    out = {}
    for role, info in MASTERS.items():
        path = MASTER_DIR / info["file"]
        if not path.is_file():
            raise Blocked(f"missing master: {info['file']} in {MASTER_DIR}")
        content = path.read_bytes()
        digest = sha256(content).hexdigest()
        if digest != info["sha256"]:
            hint = " (CRLF checkout? see .gitattributes)" if b"\r\n" in content else ""
            raise Blocked(
                f"{info['file']} differs from the registered master: {digest}{hint}. "
                "Update MASTERS in scripts/build_brand_assets.py and design/01_Logo/README.md "
                "only for an intentional owner master change."
            )
        try:
            document = br.parse_svg(content)
        except br.UnsupportedSvg as exc:
            raise Blocked(f"{info['file']}: {exc}") from exc
        out[role] = (content, document)
    return out


def _pixel_digest(rows: list[bytes]) -> str:
    return sha256(b"".join(rows)).hexdigest()


def _square(document: br.Document, size: int) -> list[bytes]:
    return br.render(br.layers_from_document(document), br.Frame.fit(document.view_box, size, size))


def _macos(document: br.Document, size: int) -> list[bytes]:
    vx, vy, vw, vh = document.view_box
    margin = vw * (1 / MACOS_BODY_RATIO - 1) / 2
    box = (vx - margin, vy - margin, vw + 2 * margin, vh + 2 * margin)
    return br.render(br.layers_from_document(document), br.Frame.fit(box, size, size))


def _cropped(document: br.Document, height: int, pad_ratio: float = 0.0) -> list[bytes]:
    x, y, w, h = br.bounds([s.subpaths for s in document.shapes], pad=0.0)
    pad = max(w, h) * pad_ratio
    box = (x - pad, y - pad, w + 2 * pad, h + 2 * pad)
    width = max(1, round(box[2] * height / box[3]))
    return br.render(br.layers_from_document(document), br.Frame.fit(box, width, height))


def build() -> dict[str, dict]:
    """Return ``{relative path: {kind, master, content, pixels}}`` for every output."""
    masters = load_masters()
    outputs: dict[str, dict] = {}

    def copy(rel: str, role: str) -> None:
        outputs[rel] = {"kind": "copy", "master": role, "content": masters[role][0]}

    def raster(rel: str, role: str, rows: list[bytes]) -> None:
        outputs[rel] = {"kind": "png", "master": role, "content": br.encode_png(rows), "pixels": rows}

    icon_doc = masters["app_icon"][1]
    emblem_doc = masters["internal_brand"][1]
    signet_doc = masters["in_app"][1]

    icons = {size: _square(icon_doc, size) for size in sorted({*ICON_SIZES, *ICO_SIZES, *FAVICON_PNG_SIZES})}
    mac = {size: _macos(icon_doc, size) for size in MACOS_SIZES}

    # ---- runtime package resources (src/chess_and_chains/ui/brand_assets)
    rt = "src/chess_and_chains/ui/brand_assets/"
    copy(rt + "signet.svg", "in_app")
    raster(rt + "signet.png", "in_app", _cropped(signet_doc, 256))
    copy(rt + "brand-emblem.svg", "internal_brand")
    raster(rt + "brand-emblem.png", "internal_brand", _square(emblem_doc, 96))
    raster(rt + "brand-emblem-192.png", "internal_brand", _square(emblem_doc, 192))
    copy(rt + "app-icon.svg", "app_icon")
    raster(rt + "app-icon.png", "app_icon", icons[256])
    for size in RUNTIME_ICON_SIZES:
        raster(rt + f"app-icon-{size}.png", "app_icon", icons[size])
    raster(rt + "app-icon-macos.png", "app_icon", mac[512])
    ico = {size: icons[size] for size in ICO_SIZES}
    outputs[rt + "app-icon.ico"] = {"kind": "ico", "master": "app_icon", "content": br.encode_ico(ico), "pixels": ico}

    # ---- public / packaging resources (assets/branding)
    pub = "assets/branding/"
    copy(pub + "icons/chess-and-chains.svg", "app_icon")
    for size in ICON_SIZES:
        raster(pub + f"icons/chess-and-chains-{size}.png", "app_icon", icons[size])
    outputs[pub + "icons/chess-and-chains.ico"] = {
        "kind": "ico", "master": "app_icon", "content": br.encode_ico(ico), "pixels": ico}
    outputs[pub + "icons/chess-and-chains.icns"] = {
        "kind": "icns", "master": "app_icon", "content": br.encode_icns(mac),
        "pixels": {kind: mac[size] for kind, size in br.ICNS_TYPES}}
    raster(pub + "icons/chess-and-chains-macos-1024.png", "app_icon", mac[1024])
    copy(pub + "favicon/favicon.svg", "app_icon")
    fav = {size: icons[size] for size in FAVICON_ICO_SIZES}
    outputs[pub + "favicon/favicon.ico"] = {"kind": "ico", "master": "app_icon", "content": br.encode_ico(fav), "pixels": fav}
    for size in FAVICON_PNG_SIZES:
        raster(pub + f"favicon/favicon-{size}.png", "app_icon", icons[size])
    copy(pub + "emblem/chess-and-chains-emblem.svg", "internal_brand")
    raster(pub + "emblem/chess-and-chains-emblem-512.png", "internal_brand", _square(emblem_doc, 512))
    copy(pub + "signet/chess-and-chains-signet.svg", "in_app")
    raster(pub + "signet/chess-and-chains-signet-512.png", "in_app", _cropped(signet_doc, 512, 0.02))

    outputs[str(MANIFEST.relative_to(ROOT)).replace("\\", "/")] = {
        "kind": "manifest", "master": None, "content": _manifest(outputs)}
    return outputs


def _manifest(outputs: dict[str, dict]) -> bytes:
    entries = []
    for rel in sorted(outputs):
        item = outputs[rel]
        entry = {"path": rel, "kind": item["kind"], "master": MASTERS[item["master"]]["file"]}
        if item["kind"] == "copy":
            entry["sha256"] = sha256(item["content"]).hexdigest()
        elif item["kind"] == "png":
            rows = item["pixels"]
            entry["size"] = [len(rows[0]) // 4, len(rows)]
            entry["pixel_sha256"] = _pixel_digest(rows)
        else:
            images = item["pixels"]
            entry["entries"] = {str(k.decode() if isinstance(k, bytes) else k): _pixel_digest(v)
                                for k, v in sorted(images.items())}
        entries.append(entry)
    data = {
        "generator": "scripts/build_brand_assets.py",
        "generator_version": GENERATOR_VERSION,
        "renderer": "chess_and_chains.ui.brand_raster (stdlib, 8x8 supersampling)",
        "masters": {role: {"file": "design/01_Logo/svg/" + info["file"], "sha256": info["sha256"]}
                    for role, info in MASTERS.items()},
        "outputs": entries,
    }
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _decode(kind: str, content: bytes):
    if kind == "png":
        return br.decode_png(content)
    if kind == "ico":
        return br.decode_ico(content)
    return br.decode_icns(content)


def differences(outputs: dict[str, dict]) -> list[str]:
    problems: list[str] = []
    for rel, item in outputs.items():
        path = ROOT / rel
        if not path.is_file():
            problems.append(f"missing: {rel}")
            continue
        stored = path.read_bytes()
        if item["kind"] in ("copy", "manifest"):
            if stored != item["content"]:
                problems.append(f"outdated: {rel}")
            continue
        try:
            pixels = _decode(item["kind"], stored)
        except (ValueError, struct.error, zlib.error) as exc:
            problems.append(f"unreadable: {rel} ({exc})")
            continue
        if pixels != item["pixels"]:
            problems.append(f"outdated: {rel}")
    expected = set(outputs)
    managed = [RUNTIME_DIR] + [PUBLIC_DIR / d for d in PUBLIC_MANAGED_DIRS]
    for directory in managed:
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            if path.is_file() and rel not in expected and path.name not in RUNTIME_UNMANAGED:
                problems.append(f"unexpected file: {rel}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="verify outputs against the masters without writing")
    args = parser.parse_args(argv)
    try:
        outputs = build()
    except (Blocked, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    if args.check:
        problems = differences(outputs)
        for problem in problems:
            print(problem, file=sys.stderr)
        if problems:
            print(f"FAILED: {len(problems)} brand asset problem(s). Run python3 -B scripts/build_brand_assets.py",
                  file=sys.stderr)
            return 1
        print(f"OK: {len(outputs)} brand outputs match the three logo masters.")
        return 0
    for rel, item in outputs.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if item["kind"] not in ("copy", "manifest") and path.is_file():
            try:
                if _decode(item["kind"], path.read_bytes()) == item["pixels"]:
                    continue  # identical pixels: keep committed bytes stable
            except (ValueError, struct.error, zlib.error):
                pass
        if path.is_file() and path.read_bytes() == item["content"]:
            continue
        path.write_bytes(item["content"])
        print(f"wrote {rel} ({len(item['content'])} bytes)")
    print(f"{len(outputs)} brand outputs up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
