"""Final audit regression, negative, and counter-probe tests for Chess & Chains V.0.3.0.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import sys
import tkinter as tk
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chess_and_chains.i18n import Translator
from chess_and_chains.ui.appearance_dialog import AppearanceDialog
from chess_and_chains.ui.branding import macos_dock_icon
from chess_and_chains.ui.dropdown import GlideDropdown
from chess_and_chains.ui.theme import resolve_theme


class FinalAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk unavailable: {exc}")
        self.root.withdraw()
        self.addCleanup(self._cleanup_root)

    def _cleanup_root(self) -> None:
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass

    def test_macos_dock_icon_has_transparent_hig_margin(self) -> None:
        img = macos_dock_icon(self.root, "app-icon")
        self.assertEqual(img.width(), img.height())
        self.assertGreaterEqual(img.width(), 256)
        if sys.platform == "darwin":
            # Corner pixel (0, 0) must be transparent due to 824/1024 HIG padding
            self.assertTrue(img.transparency_get(0, 0))

    def test_dropdown_selection_disabled_and_theme_inheritance(self) -> None:
        light = resolve_theme("light")
        dark = resolve_theme("dark")
        var = tk.StringVar(self.root, value="a")
        called: list[str] = []
        dd = GlideDropdown(
            self.root,
            var,
            [("a", "Alpha"), ("b", "Beta")],
            light,
            on_change=called.append,
        )
        dd.pack()
        self.root.update_idletasks()

        # Simulate selecting index 1
        dd._open_popup()
        self.assertIsNotNone(dd._popup)
        dd._select_index(1)
        self.assertEqual(var.get(), "b")
        self.assertEqual(called, ["b"])
        self.assertIsNone(dd._popup)

        # Negative test: disabled dropdown must not open popup
        dd.set_state("disabled")
        dd._on_click(None)  # type: ignore[arg-type]
        self.assertIsNone(dd._popup)

        # Theme inheritance
        dd.apply_theme(dark)
        self.assertEqual(dd._palette.window, dark.window)

    def test_appearance_dialog_dependency_cancel_rollback_and_responsive(self) -> None:
        t = Translator("de")
        light = resolve_theme("light")
        applied: list[dict[str, object]] = []

        def on_apply(**kwargs: object) -> None:
            applied.append(dict(kwargs))

        dlg = AppearanceDialog(
            self.root,
            t,
            light,
            theme_id="light",
            board_design_choice="standard",
            board_perspective="2d",
            on_apply=on_apply,
            modal=False,
        )
        self.addCleanup(lambda: dlg.winfo_exists() and dlg.destroy())
        self.root.update_idletasks()

        # Standard board locks perspective to 2d and disables dropdown
        self.assertEqual(dlg.perspective_var.get(), "2d")
        self.assertIsNotNone(dlg._persp_dropdown)
        self.assertEqual(dlg._persp_dropdown._state, "disabled")

        # Switching to marble enables perspective dropdown
        dlg.board_design_var.set("marble")
        dlg._on_board_design_change("marble")
        self.assertEqual(dlg._persp_dropdown._state, "normal")

        # Cancel rolls back to initial snapshot (standard / light)
        dlg.theme_var.set("dark")
        dlg._on_any_change("dark")
        dlg._cancel()
        self.assertTrue(applied)
        self.assertEqual(applied[-1]["theme_id"], "light")
        self.assertEqual(applied[-1]["board_design_choice"], "standard")

    def test_resolve_theme_unknown_id_fallback(self) -> None:
        p = resolve_theme("nonexistent-theme-xyz")
        self.assertTrue(p.window.startswith("#"))
        self.assertTrue(p.ink.startswith("#"))


if __name__ == "__main__":
    unittest.main()
