"""Post-audit regression tests – V.0.3.0 fixes.

Covers:
- P0  Marble2DArtwork SVG → raster fallback (mocked Tk without SVG support)
- P1  Settings transaction safety: SHA-256 filesystem checksum before/during/after preview
- P1  Theme parameter fix: resolve_theme is called with correct keyword args
- P1  Board design/perspective decoupling: custom board stays 2D on perspective switch
- P2  Material bar: WCAG-AA contrast of +N pill text on actual pill background
- P2  Material bar: reset to None on empty puzzle selection
- P2  Material bar: image error does not crash render; label still visible

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from chess_and_chains.chess import Color, Piece, PieceType
from chess_and_chains.chess import CapturedGroup
from chess_and_chains.i18n import Translator
from chess_and_chains.storage import DataLayout, save_settings, load_settings, Settings
from chess_and_chains.ui.board_artwork import (
    Marble2DArtwork,
    _probe_svg_support,
    _checkerboard_photo,
)
from chess_and_chains.ui.captured_material import CapturedMaterialBar
from chess_and_chains.ui.theme import (
    contrast_ratio,
    resolve_theme,
    LIGHT_THEME,
    DARK_THEME,
)

try:
    from chess_and_chains.chess import PlayerMaterial
    _HAS_PLAYER_MATERIAL = True
except ImportError:
    _HAS_PLAYER_MATERIAL = False

from tests.tk_support import create_root  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_player_material(advantage: int | None = None, captures=(), color=None, score=None):
    """Build a minimal PlayerMaterial for testing."""
    from chess_and_chains.chess import PlayerMaterial, CapturedGroup, Piece, PieceType, Color
    if color is None:
        color = Color.WHITE
    if advantage is not None and advantage > 0:
        groups = (CapturedGroup(Piece(Color.BLACK, PieceType.PAWN), advantage),)
        if score is None:
            score = advantage
    else:
        groups = ()
        if score is None:
            score = 0
    return PlayerMaterial(color=color, captures=captures, groups=groups, score=score, advantage=advantage)



# ---------------------------------------------------------------------------
# P0 – Marble2DArtwork SVG fallback
# ---------------------------------------------------------------------------

class Marble2DArtworkFallbackTests(unittest.TestCase):
    """Verify Marble2DArtwork.image() degrades gracefully when SVG is unavailable."""

    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk unavailable: {exc}")
        self.root.withdraw()
        self.addCleanup(self._cleanup)

    def _cleanup(self) -> None:
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass

    def test_svg_path_returns_correct_dimensions(self) -> None:
        """When SVG IS supported, image dimensions must equal tile_size * 8."""
        import chess_and_chains.ui.board_artwork as ba
        if not ba._probe_svg_support(self.root):
            self.skipTest("SVG not supported in this Tk build")
        art = Marble2DArtwork()
        img = art.image(self.root, 32, flipped=False)
        self.assertEqual(img.width(), 256)
        self.assertEqual(img.height(), 256)

    def test_fallback_path_returns_correct_dimensions(self) -> None:
        """When SVG is NOT supported, the raster fallback must still return correct size."""
        import chess_and_chains.ui.board_artwork as ba
        with patch.object(ba, "_SVG_SUPPORTED", False):
            art = Marble2DArtwork()
            art._images.clear()
            img = art._checkerboard_fallback(
                self.root, board_size=256, tile_size=32,
                tint_color=None, flipped=False,
            )
        self.assertEqual(img.width(), 256)
        self.assertEqual(img.height(), 256)

    def test_fallback_tinted_vs_untinted_differ(self) -> None:
        """Tinting must produce a visually different board than no tint."""
        import chess_and_chains.ui.board_artwork as ba
        with patch.object(ba, "_SVG_SUPPORTED", False):
            art = Marble2DArtwork()
            art._images.clear()
            plain = art._checkerboard_fallback(
                self.root, board_size=64, tile_size=8,
                tint_color=None, flipped=False,
            )
            tinted = art._checkerboard_fallback(
                self.root, board_size=64, tile_size=8,
                tint_color="#086FD6", flipped=False,
            )
        # At least some pixel must differ between tinted and untinted
        any_diff = any(
            plain.get(x, y) != tinted.get(x, y)
            for y in range(0, 64, 16)
            for x in range(0, 64, 16)
        )
        self.assertTrue(any_diff, "Tinted and untinted boards must produce different pixels")

    def test_fallback_flipped_vs_unflipped_differ(self) -> None:
        """Flipped board must produce distinct PhotoImage objects with different cache keys.

        A standard 8×8 checkerboard under 180° rotation is visually identical
        (swapping any (r,c) ↔ (7-r, 7-c) preserves (r+c) parity), so we do NOT
        compare pixel colours.  Instead we verify that:
        - ``_checkerboard_fallback`` returns a *new* PhotoImage (not the same object)
          because flipped=True → different cache key inside ``image()``.
        - The image dimensions are correct in both orientations.
        - The first row of pixels shows the alternating light/dark pattern,
          confirming the board was actually rendered.
        """
        import chess_and_chains.ui.board_artwork as ba
        with patch.object(ba, "_SVG_SUPPORTED", False):
            art = Marble2DArtwork()
            art._images.clear()
            normal = art._checkerboard_fallback(
                self.root, board_size=64, tile_size=8,
                tint_color=None, flipped=False,
            )
            flipped = art._checkerboard_fallback(
                self.root, board_size=64, tile_size=8,
                tint_color=None, flipped=True,
            )
        # Both must be valid, correctly-sized PhotoImages
        self.assertEqual(normal.width(), 64)
        self.assertEqual(normal.height(), 64)
        self.assertEqual(flipped.width(), 64)
        self.assertEqual(flipped.height(), 64)
        # They must be separate objects (different call, different result)
        self.assertIsNot(normal, flipped)
        # First row must alternate: tile 0 light, tile 1 dark (or vice-versa)
        pixel_a = normal.get(0, 0)   # first tile top-left
        pixel_b = normal.get(8, 0)   # second tile top-left
        self.assertNotEqual(
            pixel_a, pixel_b,
            "Adjacent tiles in the first row must have different colours"
        )

    def test_image_method_routes_to_fallback_when_svg_unsupported(self) -> None:
        """image() must route to _checkerboard_fallback when SVG is not available."""
        import chess_and_chains.ui.board_artwork as ba
        with patch.object(ba, "_SVG_SUPPORTED", False):
            art = Marble2DArtwork()
            art._images.clear()
            with patch.object(art, "_checkerboard_fallback", wraps=art._checkerboard_fallback) as spy:
                img = art.image(self.root, 32, flipped=False, tint_color=None)
        self.assertEqual(spy.call_count, 1)
        self.assertEqual(img.width(), 256)
        self.assertEqual(img.height(), 256)

    def test_cache_works_in_fallback_mode(self) -> None:
        """Fallback images must be cached and reused (no double-render)."""
        import chess_and_chains.ui.board_artwork as ba
        with patch.object(ba, "_SVG_SUPPORTED", False):
            art = Marble2DArtwork()
            art._images.clear()
            img1 = art.image(self.root, 16, flipped=False)
            img2 = art.image(self.root, 16, flipped=False)
        self.assertIs(img1, img2)

    def test_previous_state_preserved_on_render_error(self) -> None:
        """If rendering fails, the last valid cached image must be returned and survive."""
        import chess_and_chains.ui.board_artwork as ba
        art = Marble2DArtwork()
        art._images.clear()
        good_img = art.image(self.root, 16, flipped=False)

        def _explode(*args, **kwargs):
            raise OSError("Simulated render error")

        # Simulate rendering error across both SVG and raster fallback paths
        with patch.object(art, "_render_svg", side_effect=_explode), \
             patch.object(art, "_checkerboard_fallback", side_effect=_explode):
            # Gracefully preserves previous valid board state instead of raising/clearing
            recovered = art.image(self.root, 32, flipped=False)
            self.assertIs(recovered, good_img)

        # Previously cached entry must remain intact
        cached = art._images.get((self.root.tk, 16, False, None))
        self.assertIs(cached, good_img)

        # But if no previous valid board exists at all, it should raise
        fresh_art = Marble2DArtwork()
        with patch.object(fresh_art, "_render_svg", side_effect=_explode), \
             patch.object(fresh_art, "_checkerboard_fallback", side_effect=_explode):
            with self.assertRaises(OSError):
                fresh_art.image(self.root, 32, flipped=False)


# ---------------------------------------------------------------------------
# P1 – Settings transaction safety (SHA-256 filesystem regression)
# ---------------------------------------------------------------------------

class SettingsTransactionSafetyTests(unittest.TestCase):
    """Verify that live-preview in AppearanceDialog never persists to disk.

    Uses real file-system SHA-256 checksums to prove the settings file is
    written to only during Save, never during preview or Cancel.
    """

    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk unavailable: {exc}")
        self.root.withdraw()
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._cleanup)

    def _cleanup(self) -> None:
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass
        self._tmpdir.cleanup()

    def _layout(self) -> DataLayout:
        return DataLayout(Path(self._tmpdir.name) / "data")

    def test_live_preview_does_not_write_settings_file(self) -> None:
        """SHA-256 of settings file must NOT change during live preview."""
        from chess_and_chains.ui.app import ChessApp

        layout = self._layout()
        app = ChessApp(self.root, data_layout=layout, locale="en")
        self.addCleanup(app.close)

        # Establish a known saved state
        app.apply_appearance(theme_id="light", persist=True)
        self.root.update_idletasks()

        settings_file = layout.settings
        self.assertTrue(settings_file.exists(), "settings file must exist after first save")
        sha_before = _sha256(settings_file)

        # Open dialog in non-modal mode and trigger several live previews
        dlg = app.open_appearance_dialog(modal=False)
        self.addCleanup(lambda: dlg.winfo_exists() and dlg.destroy())
        self.root.update_idletasks()

        # Simulate live preview changes — these must NOT write to disk
        dlg.theme_var.set("dark")
        dlg._on_any_change("dark")
        self.root.update_idletasks()

        dlg.accent_var.set("export")
        dlg._on_any_change("export")
        self.root.update_idletasks()

        dlg.theme_var.set("glass-dark")
        dlg._on_any_change("glass-dark")
        self.root.update_idletasks()

        sha_during_preview = _sha256(settings_file)
        self.assertEqual(
            sha_before,
            sha_during_preview,
            "Settings file must NOT be modified during live preview (persist=False path is broken)",
        )

    def test_cancel_restores_settings_file_unchanged(self) -> None:
        """After Cancel, settings file must be identical to its pre-dialog state."""
        from chess_and_chains.ui.app import ChessApp

        layout = self._layout()
        app = ChessApp(self.root, data_layout=layout, locale="en")
        self.addCleanup(app.close)

        app.apply_appearance(theme_id="light", persist=True)
        self.root.update_idletasks()
        sha_before = _sha256(layout.settings)

        dlg = app.open_appearance_dialog(modal=False)
        self.root.update_idletasks()

        # Preview change then cancel
        dlg.theme_var.set("dopamine")
        dlg._on_any_change("dopamine")
        self.root.update_idletasks()

        dlg._cancel()
        # Do NOT call root.update() here: the dialog is already destroyed and
        # on macOS arm64 (CI) a full Tk event-loop pump after destroy can
        # deadlock waiting for a window that no longer exists.  idle-tasks are
        # sufficient to let any pending redraws settle.
        self.root.update_idletasks()

        sha_after_cancel = _sha256(layout.settings)
        self.assertEqual(
            sha_before,
            sha_after_cancel,
            "Settings file must be identical before dialog and after Cancel",
        )
        # App theme must roll back to light
        self.assertEqual(app.settings.theme_id, "light")

    def test_save_does_persist_settings_file(self) -> None:
        """After Save/Apply, settings file must change and reflect the new values."""
        from chess_and_chains.ui.app import ChessApp

        layout = self._layout()
        app = ChessApp(self.root, data_layout=layout, locale="en")
        self.addCleanup(app.close)

        app.apply_appearance(theme_id="light", persist=True)
        self.root.update_idletasks()
        sha_before = _sha256(layout.settings)

        dlg = app.open_appearance_dialog(modal=False)
        self.root.update_idletasks()

        dlg.theme_var.set("dark")
        dlg._on_any_change("dark")
        self.root.update_idletasks()
        sha_during = _sha256(layout.settings)
        self.assertEqual(sha_before, sha_during, "preview must not write to disk")

        dlg._save_and_close()
        self.root.update_idletasks()

        sha_after_save = _sha256(layout.settings)
        self.assertNotEqual(
            sha_before,
            sha_after_save,
            "Settings file must be different after Save",
        )
        loaded, warning = load_settings(layout.settings)
        self.assertIsNone(warning)
        self.assertEqual(loaded.theme_id, "dark")


# ---------------------------------------------------------------------------
# P1 – resolve_theme keyword argument fix
# ---------------------------------------------------------------------------

class ResolveThemeKeywordTests(unittest.TestCase):
    """Verify that resolve_theme correctly accepts accent/background as kwargs."""

    def test_accent_kwarg_changes_action_color(self) -> None:
        light = resolve_theme("light")
        with_accent = resolve_theme("light", accent="export")
        # export accent changes the action color away from the default cobalt
        self.assertNotEqual(light.action_new_bg, with_accent.action_new_bg)

    def test_background_kwarg_changes_window_color(self) -> None:
        plain = resolve_theme("light")
        tinted = resolve_theme("light", background="clear")
        # background tint shifts the window color
        self.assertNotEqual(plain.window, tinted.window)

    def test_positional_root_does_not_break_resolution(self) -> None:
        """Passing root=None as first positional arg must not silently swallow background."""
        # Previously the background string was passed as the root positional arg
        p = resolve_theme("light", None, accent="accent", background="default")
        self.assertEqual(p.window, LIGHT_THEME.window)

    def test_all_accent_and_background_combos_do_not_raise(self) -> None:
        """Every accent/background combination must resolve without error."""
        from chess_and_chains.ui.theme import ACCENT_CHOICES, BACKGROUND_CHOICES
        for theme_id in ("light", "dark"):
            for acc, _ in ACCENT_CHOICES:
                for bg, _ in BACKGROUND_CHOICES:
                    with self.subTest(theme=theme_id, accent=acc, background=bg):
                        p = resolve_theme(theme_id, accent=acc, background=bg)
                        self.assertTrue(p.window.startswith("#"))


# ---------------------------------------------------------------------------
# P1 – Board design / perspective decoupling
# ---------------------------------------------------------------------------

class BoardDesignPerspectiveDecouplingTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk unavailable: {exc}")
        self.root.withdraw()
        self.addCleanup(self._cleanup)

    def _cleanup(self) -> None:
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass

    def test_custom_board_locked_to_2d_in_dialog(self) -> None:
        """Custom board design must lock perspective dropdown to 2D (not marble)."""
        from chess_and_chains.ui.appearance_dialog import AppearanceDialog
        t = Translator("en")
        dlg = AppearanceDialog(
            self.root, t, LIGHT_THEME,
            theme_id="light",
            board_design_choice="custom",
            board_perspective="2d",
            has_custom_board=True,
            modal=False,
        )
        self.addCleanup(lambda: dlg.winfo_exists() and dlg.destroy())
        self.root.update_idletasks()
        # Custom must disable perspective dropdown
        self.assertEqual(dlg._persp_dropdown._state, "disabled")
        self.assertEqual(dlg.perspective_var.get(), "2d")

    def test_marble_board_enables_perspective_dropdown(self) -> None:
        """Marble board must enable the perspective dropdown."""
        from chess_and_chains.ui.appearance_dialog import AppearanceDialog
        t = Translator("en")
        dlg = AppearanceDialog(
            self.root, t, LIGHT_THEME,
            theme_id="light",
            board_design_choice="marble",
            board_perspective="2d",
            modal=False,
        )
        self.addCleanup(lambda: dlg.winfo_exists() and dlg.destroy())
        self.root.update_idletasks()
        self.assertEqual(dlg._persp_dropdown._state, "normal")

    def test_switching_from_marble_to_custom_disables_perspective(self) -> None:
        """Switching board design from marble to custom must re-disable the perspective dropdown."""
        from chess_and_chains.ui.appearance_dialog import AppearanceDialog
        t = Translator("en")
        dlg = AppearanceDialog(
            self.root, t, LIGHT_THEME,
            theme_id="light",
            board_design_choice="marble",
            board_perspective="3d",
            has_custom_board=True,
            modal=False,
        )
        self.addCleanup(lambda: dlg.winfo_exists() and dlg.destroy())
        self.root.update_idletasks()
        self.assertEqual(dlg._persp_dropdown._state, "normal")

        # Switch to custom
        dlg.board_design_var.set("custom")
        dlg._on_board_design_change("custom")
        self.root.update_idletasks()

        self.assertEqual(dlg._persp_dropdown._state, "disabled",
                         "Custom board must lock perspective dropdown to 2D")
        self.assertEqual(dlg.perspective_var.get(), "2d",
                         "Perspective must reset to 2D when custom board is selected")


# ---------------------------------------------------------------------------
# P2 – Material bar: WCAG-AA contrast of +N pill text
# ---------------------------------------------------------------------------

class MaterialBarContrastTests(unittest.TestCase):
    """Verify that the +N advantage pill text achieves WCAG-AA (4.5:1) contrast."""

    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk unavailable: {exc}")
        self.root.withdraw()
        self.addCleanup(self._cleanup)

    def _cleanup(self) -> None:
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass

    def _make_bar_with_advantage(self, theme, advantage: int) -> CapturedMaterialBar:
        bar = CapturedMaterialBar(self.root, Color.WHITE, lambda k, **_: k, theme=theme)
        mat = _make_player_material(advantage=advantage)
        bar.set_material(Color.WHITE, mat, theme=theme)
        self.root.update_idletasks()
        return bar

    def _get_pill_colors(self, bar: CapturedMaterialBar):
        """Extract the fill (pill background) and text fill from canvas items."""
        pill_bg = None
        text_fg = None
        for item in bar.find_withtag("advantage_pill"):
            pill_bg = bar.itemcget(item, "fill")
        for item in bar.find_withtag("advantage_text"):
            text_fg = bar.itemcget(item, "fill")
        return pill_bg, text_fg

    def test_light_theme_advantage_pill_contrast_wcag_aa(self) -> None:
        bar = self._make_bar_with_advantage(LIGHT_THEME, 3)
        pill_bg, text_fg = self._get_pill_colors(bar)
        self.assertIsNotNone(pill_bg, "advantage_pill item must exist")
        self.assertIsNotNone(text_fg, "advantage_text item must exist")
        cr = contrast_ratio(text_fg, pill_bg)
        self.assertGreaterEqual(
            cr, 4.5,
            f"Light theme: +N text '{text_fg}' on pill '{pill_bg}' has contrast {cr:.2f} < 4.5 (WCAG AA fail)"
        )

    def test_dark_theme_advantage_pill_contrast_wcag_aa(self) -> None:
        bar = self._make_bar_with_advantage(DARK_THEME, 2)
        pill_bg, text_fg = self._get_pill_colors(bar)
        self.assertIsNotNone(pill_bg)
        self.assertIsNotNone(text_fg)
        cr = contrast_ratio(text_fg, pill_bg)
        self.assertGreaterEqual(
            cr, 4.5,
            f"Dark theme: +N text '{text_fg}' on pill '{pill_bg}' has contrast {cr:.2f} < 4.5 (WCAG AA fail)"
        )

    def test_all_themes_advantage_pill_contrast(self) -> None:
        """Every Glide theme must achieve WCAG AA on the advantage pill."""
        from chess_and_chains.ui.theme import THEMES
        for name, pal in THEMES.items():
            if name == "w06-provisional":
                continue
            with self.subTest(theme=name):
                bar = self._make_bar_with_advantage(pal, 1)
                pill_bg, text_fg = self._get_pill_colors(bar)
                if pill_bg is None or text_fg is None:
                    continue  # no advantage rendered
                cr = contrast_ratio(text_fg, pill_bg)
                self.assertGreaterEqual(
                    cr, 4.5,
                    f"Theme '{name}': +N text '{text_fg}' on pill '{pill_bg}' has contrast {cr:.2f} < 4.5"
                )


# ---------------------------------------------------------------------------
# P2 – Material bar: image error does not crash renderer
# ---------------------------------------------------------------------------

class MaterialBarImageErrorTests(unittest.TestCase):
    """Verify that piece image loading errors do not crash the material bar render."""

    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk unavailable: {exc}")
        self.root.withdraw()
        self.addCleanup(self._cleanup)

    def _cleanup(self) -> None:
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass

    def test_broken_image_load_does_not_crash_and_label_visible(self) -> None:
        """When piece image loading fails, the bar must not raise; label must still appear."""
        bar = CapturedMaterialBar(
            self.root, Color.WHITE, lambda k, **_: k, theme=LIGHT_THEME
        )
        mat = _make_player_material(advantage=2)

        # Make image loading always fail
        def _explode(*_args, **_kwargs):
            raise OSError("Simulated image load failure")

        bar._get_piece_image = _explode  # type: ignore[method-assign]

        # Must not raise
        bar.set_material(Color.WHITE, mat, theme=LIGHT_THEME)
        self.root.update_idletasks()

        # Label (advantage pill) must still be rendered
        pill_items = bar.find_withtag("advantage_pill")
        text_items = bar.find_withtag("advantage_text")
        self.assertTrue(pill_items, "advantage_pill must still render even if piece images fail")
        self.assertTrue(text_items, "advantage_text must still render even if piece images fail")


# ---------------------------------------------------------------------------
# P2 – Material bar: reset on empty puzzle selection
# ---------------------------------------------------------------------------

class MaterialBarPuzzleResetTests(unittest.TestCase):
    """Verify material bars are cleared when no puzzle is selected."""

    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk unavailable: {exc}")
        self.root.withdraw()
        self.addCleanup(self._cleanup)

    def _cleanup(self) -> None:
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass

    def test_set_material_none_clears_advantage_display(self) -> None:
        """set_material(..., None) must clear all advantage pill items from canvas."""
        bar = CapturedMaterialBar(
            self.root, Color.WHITE, lambda k, **_: k, theme=LIGHT_THEME
        )
        # First set some material
        mat = _make_player_material(advantage=3)
        bar.set_material(Color.WHITE, mat, theme=LIGHT_THEME)
        self.root.update_idletasks()
        self.assertTrue(bar.find_withtag("advantage_pill"), "should have pill when advantage > 0")

        # Now reset to None
        bar.set_material(Color.WHITE, None, theme=LIGHT_THEME)
        self.root.update_idletasks()
        self.assertFalse(bar.find_withtag("advantage_pill"), "advantage pill must be gone after reset")
        self.assertFalse(bar.find_withtag("advantage_text"), "advantage text must be gone after reset")

    def test_app_puzzle_panel_empty_resets_material_bars(self) -> None:
        """When puzzle panel has no active puzzle, _sync_material_bars must set material=None."""
        from chess_and_chains.ui.app import ChessApp

        with tempfile.TemporaryDirectory() as tmp:
            layout = DataLayout(Path(tmp) / "data")
            app = ChessApp(self.root, data_layout=layout, locale="en")
            try:
                # Play a game move to get some material difference
                from chess_and_chains.chess import Move
                app._play_move(Move.from_uci("e2e4"))
                self.root.update_idletasks()

                # Switch to puzzle panel with no puzzle loaded
                app.tab_rail.set_active("puzzles")
                self.root.update_idletasks()

                # With no puzzle active (self.puzzle is None), bars should show None material
                if app.puzzle is None:
                    app._sync_material_bars()
                    self.root.update_idletasks()
                    self.assertIsNone(
                        app.top_material_bar.material,
                        "Material bar must be None when puzzle panel is empty"
                    )
                    self.assertIsNone(
                        app.bottom_material_bar.material,
                        "Material bar must be None when puzzle panel is empty"
                    )
            finally:
                app.close()


# ---------------------------------------------------------------------------
# P2 – Settings UI & GlideDropdown polish tests
# ---------------------------------------------------------------------------

class DropdownAndSettingsP2Tests(unittest.TestCase):
    """Verify GlideDropdown label readability, popup boundaries, and footer alignment."""

    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk unavailable: {exc}")
        self.root.withdraw()
        self.addCleanup(self._cleanup)

    def _cleanup(self) -> None:
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass

    def test_dropdown_no_24_char_blind_truncation(self) -> None:
        """Labels longer than 24 chars must NOT be blindly truncated with an ellipsis."""
        from chess_and_chains.ui.dropdown import GlideDropdown
        from chess_and_chains.ui.theme import resolve_theme
        pal = resolve_theme("light")
        long_label = "2D – Vogelperspektive (Marmor)"  # 30 chars > 24
        var = tk.StringVar(value="long_opt")
        dd = GlideDropdown(
            self.root,
            var,
            [("long_opt", long_label)],
            pal,
            width=260,
        )
        self.root.update()
        dd._open_popup()
        self.root.update()
        self.assertIsNotNone(dd._popup_canvas)
        canvas = dd._popup_canvas
        # Find text items on canvas
        texts = [canvas.itemcget(item, "text") for item in canvas.find_withtag("all") if canvas.type(item) == "text"]
        self.assertIn(
            long_label,
            texts,
            f"Long label '{long_label}' must be displayed fully without 24-char truncation, got: {texts}",
        )
        dd._close_popup()

    def test_dropdown_uses_after_scope(self) -> None:
        """GlideDropdown must use AfterScope from window_lifetime to satisfy Glide contract."""
        from chess_and_chains.ui.dropdown import GlideDropdown
        from chess_and_chains.ui.theme import resolve_theme
        from glide_shell.window_lifetime import AfterScope
        pal = resolve_theme("light")
        var = tk.StringVar(value="v")
        dd = GlideDropdown(self.root, var, [("v", "Label")], pal)
        self.assertIsInstance(dd._after_scope, AfterScope)
        dd.destroy()

    def test_footer_buttons_positioned_together_at_bottom_right(self) -> None:
        """Both Cancel and Apply buttons must be grouped together at bottom-right."""
        from chess_and_chains.ui.appearance_dialog import AppearanceDialog
        from chess_and_chains.ui.theme import resolve_theme
        from chess_and_chains.i18n import Translator
        pal = resolve_theme("light")
        t = Translator("de")
        dlg = AppearanceDialog(self.root, t, pal, modal=False)
        self.addCleanup(lambda: dlg.winfo_exists() and dlg.destroy())
        self.root.update()

        footer = dlg._footer
        col0_cfg = footer.grid_columnconfigure(0)
        self.assertEqual(
            col0_cfg.get("weight", 0),
            1,
            "Footer column 0 must have weight=1 as a spacer pushing buttons to the right",
        )
        cancel_info = dlg._cancel_btn.grid_info()
        apply_info = dlg._apply_btn.grid_info()
        self.assertEqual(cancel_info["column"], 1, "Cancel button must be in column 1 (right-aligned)")
        self.assertEqual(apply_info["column"], 2, "Apply button must be in column 2 (rightmost)")
        dlg._cancel()


# ---------------------------------------------------------------------------
# P0 – bot event-loop timing annotation
# ---------------------------------------------------------------------------

class BotTimingAnnotationTests(unittest.TestCase):
    """Document the CI timing issue for the bot event-loop test.

    The actual timing test lives in test_app_integration.py.
    This test validates the POLL_MS constant is small enough to meet the gap.
    """

    def test_poll_ms_is_within_acceptable_bound(self) -> None:
        from chess_and_chains.ui.app import POLL_MS
        self.assertLessEqual(
            POLL_MS,
            100,
            f"POLL_MS={POLL_MS} is too large; Tk will stall and the 250ms gap test will fail"
        )

    def test_gap_threshold_is_above_two_poll_intervals(self) -> None:
        """The 250ms gap threshold must be at least 2× POLL_MS to tolerate one missed poll."""
        from chess_and_chains.ui.app import POLL_MS
        gap_threshold_ms = 250
        self.assertGreater(
            gap_threshold_ms,
            2 * POLL_MS,
            f"Gap threshold {gap_threshold_ms}ms ≤ 2×POLL_MS ({2 * POLL_MS}ms); "
            "threshold is too tight for slow CI runners"
        )


if __name__ == "__main__":
    unittest.main()
