#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Capture real screenshots of the running app for the brand acceptance.

Uses a temporary, isolated data directory (no user data) and Pillow's
``ImageGrab`` (developer tool only, not a runtime dependency). Windows and
macOS only; on Linux use an X11 screenshot tool instead.

    python3 scripts/capture_brand_screenshots.py --out docs/reports/assets/2026-11-26-branding
"""
from __future__ import annotations

import argparse
import ctypes
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SHOTS = (
    # name, appearance kwargs, window geometry, action
    ("01-main-cobalt-light", dict(theme_id="light", accent_choice="accent"), "1280x860", None),
    ("02-main-turquoise-light", dict(theme_id="light", accent_choice="due_action"), "1280x860", None),
    ("03-main-amber-dark", dict(theme_id="dark", accent_choice="flag"), "1280x860", None),
    ("04-light-mode", dict(theme_id="light", accent_choice="clear", piece_set="top"), "1280x860", None),
    ("05-dark-mode", dict(theme_id="dark", accent_choice="accent", piece_set="classic"), "1280x860", None),
    ("06-contrast-dark", dict(theme_id="contrast-dark", accent_choice="export"), "1280x860", None),
    ("07-compact-window", dict(theme_id="light", accent_choice="delete"), "940x860", None),
    ("08-large-font", dict(theme_id="glass-light", accent_choice="import", font_scale_choice="large"), "1280x900", None),
    ("09-about-dialog", dict(theme_id="light", accent_choice="due_action"), "1280x860", "about"),
    ("10-settings-theme-preview", dict(theme_id="dark", accent_choice="due_action"), "1280x900", "settings"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            pass
    import tkinter as tk
    from PIL import ImageGrab

    from chess_and_chains.storage.paths import DataLayout
    from chess_and_chains.ui.app import ChessApp

    args.out.mkdir(parents=True, exist_ok=True)

    def grab(widget: tk.Misc, path: Path) -> None:
        widget.update()
        time.sleep(0.35)
        widget.update()
        x, y = widget.winfo_rootx(), widget.winfo_rooty()
        w, h = widget.winfo_width(), widget.winfo_height()
        ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True).save(path)
        print(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)

    with tempfile.TemporaryDirectory() as tmp:
        for name, appearance, geometry, action in SHOTS:
            root = tk.Tk()
            app = ChessApp(root, data_layout=DataLayout(Path(tmp) / name), locale="de")
            app.apply_appearance(persist=False, **appearance)
            root.geometry(geometry + "+40+40")
            root.deiconify()
            root.lift()
            root.attributes("-topmost", True)
            root.update()
            app.sync_header_density(root.winfo_width())
            target: tk.Misc = root
            if action == "about":
                target = app.show_about_dialog(modal=False)
                target.attributes("-topmost", True)
            elif action == "settings":
                target = app.open_appearance_dialog(modal=False)
                target.attributes("-topmost", True)
            grab(target, args.out / f"{name}.png")
            app.close()
            try:
                root.destroy()
            except tk.TclError:
                pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
