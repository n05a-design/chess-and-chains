#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Build a standalone local macOS ``Chess & Chains.app`` development bundle.

No extra third-party packager required — uses ad-hoc ``codesign`` together
with the active python.org framework executable so Chess & Chains can launch
cleanly from Finder, Dock, or Spotlight outside any IDE/host tool.

The bundle icon is Logo 03 (``design/01_Logo/svg/Logo_Chess-&-Chains-03.svg``)
as ``ChessAndChains.icns``, generated platform-independently by
``scripts/build_brand_assets.py`` with the transparent 824/1024 Apple icon grid.
"""
from __future__ import annotations

import argparse
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src"
ICON_ICNS = REPO / "assets" / "branding" / "icons" / "chess-and-chains.icns"
APP_NAME = "Chess & Chains"
BUNDLE_ID = "de.n05a.chessandchains"


def read_version() -> str:
    init_file = SRC / "chess_and_chains" / "__init__.py"
    for line in init_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__ = "):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"Could not read __version__ from {init_file}")


def python_starter() -> Path:
    candidates = [
        Path(sys.base_prefix) / "Resources" / "Python.app" / "Contents" / "MacOS" / "Python",
        Path(sys.executable),
    ]
    for cand in candidates:
        if cand.is_file():
            return cand
    raise SystemExit("No Python executable found to embed into the local macOS .app bundle.")


def build_app(target_dir: Path) -> Path:
    version = read_version()
    app_dir = target_dir / f"{APP_NAME}.app"
    if app_dir.exists():
        shutil.rmtree(app_dir)
    contents = app_dir / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    src_dst = resources / "src"
    macos.mkdir(parents=True)
    resources.mkdir(parents=True)

    for pkg in ("chess_and_chains", "glide_shell"):
        shutil.copytree(
            SRC / pkg,
            src_dst / pkg,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        )

    py_copy = macos / "chess-python"
    shutil.copy2(python_starter(), py_copy)
    launcher = macos / APP_NAME
    launcher.write_text(
        "#!/bin/sh\n"
        'HERE="$(cd "$(dirname "$0")" && pwd)"\n'
        'export PYTHONPATH="$HERE/../Resources/src${PYTHONPATH:+:$PYTHONPATH}"\n'
        'exec "$HERE/chess-python" "$HERE/../Resources/src/chess_and_chains/start.py" "$@"\n',
        encoding="utf-8",
    )
    launcher.chmod(0o755)

    icns_file = "ChessAndChains.icns"
    if not ICON_ICNS.is_file():
        raise SystemExit(f"Missing {ICON_ICNS}; run python3 -B scripts/build_brand_assets.py first.")
    shutil.copy2(ICON_ICNS, resources / icns_file)

    info = {
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleShortVersionString": version,
        "CFBundleVersion": version,
        "CFBundleExecutable": APP_NAME,
        "CFBundleIconFile": icns_file,
        "CFBundlePackageType": "APPL",
        "CFBundleInfoDictionaryVersion": "6.0",
        "LSApplicationCategoryType": "public.app-category.board-games",
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": "MPL-2.0 Local Development Bundle",
    }
    with open(contents / "Info.plist", "wb") as fh:
        plistlib.dump(info, fh)
    (contents / "PkgInfo").write_text("APPL????", encoding="ascii")

    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(app_dir)], check=True, capture_output=True)
    return app_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Build local standalone macOS .app bundle for Chess & Chains.")
    parser.add_argument("--dest", type=Path, default=REPO / "build" / "macos", help="Output directory")
    args = parser.parse_args()
    if sys.platform != "darwin":
        raise SystemExit("This helper builds a macOS .app bundle and requires macOS.")
    args.dest.mkdir(parents=True, exist_ok=True)
    app_path = build_app(args.dest)
    print(f"Built standalone macOS app: {app_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
