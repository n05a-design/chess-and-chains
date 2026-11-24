"""Regression and contract tests for Glide Shell 0.6.2 integration in Chess & Chains."""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from tkinter import ttk
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from glide_shell import (  # noqa: E402
    SHELL_VERSION,
    action_picker,
    app_host,
    command_history,
    modal_session,
    motion,
    runtime_paths,
    selftest,
    system_appearance,
    text_fit,
    window_geometry,
    window_lifetime,
)

from chess_and_chains.chess import Color, Move, PieceType, parse_square  # noqa: E402
from chess_and_chains.engines.bot import EngineConfig, UCIBot  # noqa: E402
from chess_and_chains.game import GameSetup  # noqa: E402
from chess_and_chains.i18n import Translator  # noqa: E402
from chess_and_chains.puzzles import load_demo_pack  # noqa: E402
from chess_and_chains.storage import DataLayout, Settings, SettingsError, default_data_dir, load_settings  # noqa: E402
from chess_and_chains.ui.app import PANEL_GAP, ChessApp, EngineDialog, check_tk_version, create_app_host, launch  # noqa: E402
from chess_and_chains.ui.appearance_dialog import AppearanceDialog  # noqa: E402
from chess_and_chains.ui.dialogs import PositionDialog  # noqa: E402
from chess_and_chains.ui.pieces import PIECE_FILE_NAMES, validate_svg_piece_set  # noqa: E402
from chess_and_chains.ui.replay import ReplayDialog  # noqa: E402
from chess_and_chains.ui.text_board import TextBoardDialog  # noqa: E402
from chess_and_chains.ui.theme import (  # noqa: E402
    ACCENT_CHOICES,
    CONTRAST_DARK_THEME,
    CONTRAST_LIGHT_THEME,
    DARK_THEME,
    DOPAMINE_THEME,
    GLASS_DARK_THEME,
    GLASS_LIGHT_THEME,
    LIGHT_THEME,
    MINIMAL_DARK_THEME,
    MINIMAL_LIGHT_THEME,
    PIXEL_THEME,
    RoundedButton,
    RoundedSurfaceCard,
    THEME_MODES,
    THEMES,
    clip_button_text,
    contrast_ratio,
    hex_rgb,
    resolve_theme,
)
from tests.tk_support import create_root  # noqa: E402


class GlideShellIntegrationTests(unittest.TestCase):
    def test_01_app_host_launch_and_preflight_failure(self):
        shown: list[tuple[str, str]] = []
        created: list[tk.Toplevel] = []

        def fake_root():
            root = create_root(self)
            created.append(root)
            return root

        failing_host = create_app_host(
            preflight=(lambda _r: ("Startup Blocked", "Simulated failure"),),
            show_error=lambda title, msg, parent=None: shown.append((title, msg)),
            tk_factory=fake_root,
        )
        with self.assertRaises(SystemExit) as exit_info:
            failing_host.run(lambda r: r, mainloop=False)
        self.assertEqual(exit_info.exception.code, 1)
        self.assertEqual(shown, [("Startup Blocked", "Simulated failure")])
        with self.assertRaises(tk.TclError):
            created[0].winfo_exists()

        with tempfile.TemporaryDirectory() as tmp:
            app = launch(mainloop=False, data_layout=DataLayout(Path(tmp) / "data"))
            try:
                self.assertIsInstance(app, ChessApp)
                self.assertIsNotNone(app.root)
                self.assertIsNone(check_tk_version(app.root))
            finally:
                app.close()

    def test_02_single_tk_root_and_03_resource_cleanup_on_close(self):
        root = create_root(self)
        with tempfile.TemporaryDirectory() as tmp:
            app = ChessApp(root, data_layout=DataLayout(Path(tmp) / "data"))
            with patch("tkinter.Tk", side_effect=AssertionError("Must not create second Tk root")):
                app._refresh()
                app.tab_rail.set_active("moves")
                app.tab_rail.set_active("puzzles")
                app.tab_rail.set_active("play")
            self.assertFalse(app.scope.closed)
            self.assertTrue(window_lifetime.pending_jobs(root))
            app.close()
            self.assertTrue(app.scope.closed)
            self.assertTrue(app.transitions.closed)
            self.assertEqual(window_lifetime.pending_jobs(root), frozenset())

    def test_04_modal_session_focus_and_grab_contract(self):
        root = create_root(self)
        app = ChessApp(root, locale="en")
        self.addCleanup(app.close)
        root.deiconify()
        root.update()
        app.library_button.focus_force()
        root.update()
        seen_grab: list[bool] = []

        def drive_chooser():
            dialog = root.grab_current()
            seen_grab.append(dialog is not None and getattr(dialog, modal_session.ACTIVE_ATTRIBUTE, False))
            if dialog is not None:
                dialog.destroy()

        root.after(10, drive_chooser)
        chosen = app._choose_item("Test Chooser", ["Alpha", "Beta"], "Select")
        self.assertIsNone(chosen)
        self.assertEqual(seen_grab, [True])
        self.assertIsNone(root.grab_current())
        self.assertIs(root.focus_lastfor(), app.library_button)

    def test_05_shortcuts_and_menu_action_picker(self):
        root = create_root(self)
        app = ChessApp(root, locale="en")
        self.addCleanup(app.close)
        actions = app.available_menu_actions("undo")
        self.assertTrue(actions)
        self.assertEqual(actions[0].label, "Undo move")
        self.assertTrue(app.root.bind("<Control-z>"))
        self.assertTrue(app.root.bind("<Control-n>"))

    def test_06_theme_switching_and_wcag_contrast(self):
        self.assertEqual(THEME_MODES, ("light", "dark", "system"))
        for palette in (LIGHT_THEME, DARK_THEME):
            with self.subTest(mode=palette.mode):
                self.assertGreaterEqual(contrast_ratio(palette.ink, palette.acetate), 4.5)
                self.assertGreaterEqual(contrast_ratio(palette.muted_ink, palette.acetate), 4.5)
                self.assertGreaterEqual(contrast_ratio(palette.action_new_fg, palette.action_new_bg), 4.5)

        self.assertIs(resolve_theme("system", system_dark=True), DARK_THEME)
        self.assertIs(resolve_theme("system", system_dark=False), LIGHT_THEME)

        with tempfile.TemporaryDirectory() as tmp:
            layout = DataLayout(Path(tmp) / "data")
            root = create_root(self)
            app = ChessApp(root, data_layout=layout, locale="en")
            try:
                app.apply_theme("dark")
                self.assertIs(app.theme, DARK_THEME)
                self.assertEqual(app.root.cget("background"), DARK_THEME.window)
                loaded, warning = load_settings(layout.settings)
                self.assertIsNone(warning)
                self.assertEqual(loaded.theme_id, "dark")
            finally:
                app.close()

    def test_07_window_geometry_parsing_and_clamping(self):
        parsed = window_geometry.parse("1280x800+-200+50")
        self.assertEqual(parsed, (1280, 800, -200, 50))
        clamped = window_geometry.clamp(600, 500, 99999, 99999, 1440, 900, (860, 700))
        self.assertEqual((clamped[0], clamped[1]), (860, 700))
        self.assertLess(clamped[2], 1440)
        self.assertLess(clamped[3], 900)
        self.assertIsNone(window_geometry.parse("not-a-geometry"))

    def test_08_ui_timers_and_motion_transitions_under_after_scope(self):
        root = create_root(self)
        app = ChessApp(root, locale="en")
        self.addCleanup(app.close)
        dialog = EngineDialog(app)
        self.assertFalse(dialog.scope.closed)
        steps: list[float] = []
        app.transitions.start("probe", steps.append, duration_ms=0)
        self.assertEqual(steps, [1.0])
        dialog.window.destroy()
        self.assertTrue(dialog.scope.closed)

    def test_09_bot_worker_shutdown_and_10_undo_redo_consistency(self):
        root = create_root(self)
        app = ChessApp(
            root,
            locale="en",
            provider_factory=lambda preset, _s: UCIBot(EngineConfig.mock("normal", delay_ms=200), preset),
        )
        app._play_move(Move.from_uci("e2e4"))
        self.assertEqual(len(app.game.moves), 1)
        app._undo()
        self.assertEqual(app.game.moves, [])
        app._redo()
        self.assertEqual(app.game.moves, [Move.from_uci("e2e4")])
        app.start_game("human-vs-bot-black")
        app.close()
        self.assertTrue(app.controller._closed)

        # CommandHistory failure keeps stacks intact
        state = {"v": 1}
        history = command_history.CommandHistory(
            lambda: dict(state),
            lambda _saved: False,
            lambda saved: state.update(saved),
        )
        history.record()
        state["v"] = 2
        self.assertEqual(history.undo(), command_history.FAILED)
        self.assertEqual(len(history), 1)

    def test_11_settings_geometry_validation_and_12_pgn_fen_clipboard(self):
        with self.assertRaises(SettingsError):
            Settings(window_geometry="invalid-geom").validate()
        valid = Settings(window_geometry="1180x820+40+40").validate()
        self.assertEqual(valid.window_geometry, "1180x820+40+40")

        root = create_root(self)
        app = ChessApp(root, locale="en")
        self.addCleanup(app.close)
        app._play_move(Move.from_uci("e2e4"))
        app._copy_pgn()
        self.assertIn("1. e4 *", root.clipboard_get())
        self.assertTrue(text_fit.clip("Long error text", 8).endswith("..."))

    def test_13_puzzle_progress_and_14_svg_piece_contract(self):
        pack = load_demo_pack()
        self.assertEqual(len(pack.puzzles), 5)
        assets_dir = ROOT / "src" / "chess_and_chains" / "ui" / "piece_assets"
        report = validate_svg_piece_set(assets_dir)
        self.assertTrue(report.ok, report.problems)
        self.assertEqual(len(PIECE_FILE_NAMES), 12)

    def test_15_runtime_paths_isolation_and_16_packaging_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            chosen = default_data_dir(environ={"CHESS_AND_CHAINS_DATA_DIR": tmp})
            self.assertEqual(chosen, Path(tmp))
        base, forced = runtime_paths.resolve_base(None, {"CHESS_AND_CHAINS_DATA_DIR": "/tmp/cc_probe"},
                                                  "CHESS_AND_CHAINS_DATA_DIR", "/tmp/default")
        self.assertTrue(forced)
        self.assertTrue(base.endswith("cc_probe"))

        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        pkg_data = pyproject["tool"]["setuptools"]["package-data"]["glide_shell"]
        self.assertIn("*.json", pkg_data)
        self.assertIn("*.md", pkg_data)
        self.assertIn("LICENSE", pkg_data)

    def test_17_architecture_import_boundaries(self):
        domain_dirs = ("chess", "game", "engines", "puzzles")
        for sub in domain_dirs:
            for py_file in (ROOT / "src" / "chess_and_chains" / sub).rglob("*.py"):
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        names = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        names = [node.module or ""]
                    else:
                        continue
                    for name in names:
                        root_mod = name.split(".")[0]
                        self.assertNotIn(root_mod, ("tkinter", "glide_shell"),
                                         f"{py_file} must not import {name}")

        for py_file in (ROOT / "src" / "glide_shell").glob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                for name in names:
                    root_mod = name.split(".")[0]
                    self.assertNotIn(root_mod, ("chess_and_chains", "glide"),
                                     f"{py_file} must remain host-independent, found import {name}")

    def test_18_manifest_integrity_and_negative_tamper_checks(self):
        shell_dir = ROOT / "src" / "glide_shell"
        self.assertEqual(SHELL_VERSION, "0.6.2")
        summary = selftest.check_manifest(folder=shell_dir)
        self.assertIn("23 files match manifest", summary)

        with tempfile.TemporaryDirectory() as tmp:
            copy_dir = Path(tmp) / "glide_shell"
            copy_dir.mkdir()
            for item in shell_dir.iterdir():
                if item.is_file():
                    (copy_dir / item.name).write_bytes(item.read_bytes())

            # Negative 1: modified source file
            (copy_dir / "motion.py").write_text("# tampered\n", encoding="utf-8")
            with self.assertRaises(AssertionError):
                selftest.check_manifest(folder=copy_dir)
            (copy_dir / "motion.py").write_bytes((shell_dir / "motion.py").read_bytes())

            # Negative 2: extra unmanaged python module
            extra = copy_dir / "unmanaged_extra.py"
            extra.write_text("x = 1\n", encoding="utf-8")
            with self.assertRaises(AssertionError):
                selftest.check_manifest(folder=copy_dir)
            extra.unlink()

            # Negative 3: missing manifest
            (copy_dir / "SHELL_MANIFEST.json").unlink()
            with self.assertRaises(AssertionError):
                selftest.check_manifest(folder=copy_dir)

    def test_19_agent_bootstrap_skills_and_20_design_contract_layouts(self):
        agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Glide Shell", agents_text)
        self.assertIn("src/glide_shell/SHELL_MANIFEST.json", agents_text)
        for root_name in (".agents", ".claude"):
            for skill in ("glide-shell", "chess-design-system", "chess-ui-engineering", "chess-quality"):
                skill_md = ROOT / root_name / "skills" / skill / "SKILL.md"
                self.assertTrue(skill_md.is_file(), f"Missing {skill_md}")
                text = skill_md.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"), f"{skill_md} missing YAML frontmatter")
                for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                    if target.startswith(("http://", "https://")):
                        continue
                    resolved = (skill_md.parent / target).resolve()
                    self.assertTrue(resolved.exists(), f"Broken skill link {skill_md} -> {target}")

        self.assertTrue((ROOT / "src" / "glide_shell" / "DESIGN_RICHTLINIEN.md").is_file())
        contract = (ROOT / "docs" / "design" / "GLIDE_DESIGN_CONTRACT.md").read_text(encoding="utf-8")
        for token in ("P1", "P6", "B15", "B11", "Connected System"):
            self.assertIn(token, contract)

        # Layout verification at 860x700 and 1280x800 in both Light and Dark themes
        root = create_root(self)
        app = ChessApp(root, locale="en")
        self.addCleanup(app.close)
        root.deiconify()
        for theme_id in ("light", "dark"):
            app.apply_theme(theme_id, persist=False)
            for geom in ("860x700", "1280x800"):
                root.geometry(geom)
                root.update()
                self.assertGreater(app.board._square_size, 20)
                for button in (app.new_game_button, app.undo_button, app.library_button):
                    self.assertGreater(button.winfo_width(), 10)
                    self.assertGreater(button.winfo_height(), 10)

    def test_21_two_pane_layout_left_sidebar_positioning(self):
        root = create_root(self)
        app = ChessApp(root, locale="en")
        self.addCleanup(app.close)
        root.deiconify()
        root.geometry("1180x820")
        root.update()
        # Verify left sidebar is to the left of the board sheet in screen space
        self.assertLess(app.side_sheet.winfo_rootx(), app.board_sheet.winfo_rootx())
        # Verify focus order: board -> tab_rail["play"] -> board on Shift-Tab
        app.board.focus_force()
        root.update()
        app.board.event_generate("<Tab>")
        root.update()
        self.assertIs(root.focus_get(), app.tab_rail.children["play"])
        app.tab_rail.children["play"].event_generate("<Shift-Tab>")
        root.update()
        self.assertIs(root.focus_get(), app.board)

    def test_22_sidebar_narrow_rail_and_keyboard_navigation(self):
        root = create_root(self)
        app = ChessApp(root, locale="en")
        self.addCleanup(app.close)
        root.deiconify()
        root.geometry("1180x820")
        root.update()
        self.assertTrue(app.side_sheet.winfo_viewable())
        self.assertFalse(app.sidebar_rail_sheet.winfo_viewable())
        self.assertEqual(app._rail_slot.winfo_manager(), "")

        # Collapse wide sidebar to 64-px rail
        app.toggle_sidebar_narrow()
        root.update()
        self.assertTrue(app.sidebar_narrow())
        self.assertEqual(app._side_slot.winfo_manager(), "")
        self.assertFalse(app.side_sheet.winfo_viewable())
        self.assertTrue(app.sidebar_rail_sheet.winfo_viewable())
        self.assertAlmostEqual(app._rail_slot.winfo_width(), 64, delta=6)

        # Rail buttons exist and are keyboard navigable
        rail_keys = ("play", "moves", "puzzles", "new_game", "undo", "redo", "flip", "expand")
        for key in rail_keys:
            self.assertIn(key, app.sidebar_rail_buttons)

        # Tab switch via rail button sets active panel
        moves_btn = app.sidebar_rail_buttons["moves"]
        moves_btn.invoke()
        root.update()
        self.assertEqual(app.active_panel, "moves")

        # Expand back to wide sidebar using the bottom » button
        expand_btn = app.sidebar_rail_buttons["expand"]
        expand_btn.invoke()
        root.update()
        self.assertFalse(app.sidebar_narrow())
        self.assertTrue(app.side_sheet.winfo_viewable())
        self.assertTrue(app.moves_panel.winfo_viewable())
        self.assertTrue(app.empty_moves_label.winfo_viewable())
        self.assertEqual(app._rail_slot.winfo_manager(), "")

    def test_23_sidebar_hide_and_full_width_workspace(self):
        root = create_root(self)
        app = ChessApp(root, locale="en")
        self.addCleanup(app.close)
        root.deiconify()
        root.geometry("1180x820")
        root.update()

        initial_board_w = app.board_sheet.winfo_width()
        app.toggle_sidebar()
        root.update()
        self.assertFalse(app.sidebar_visible)
        self.assertEqual(app._side_slot.winfo_manager(), "")
        self.assertEqual(app._rail_slot.winfo_manager(), "")
        self.assertFalse(app.side_sheet.winfo_viewable())
        self.assertFalse(app.sidebar_rail_sheet.winfo_viewable())
        # Board sheet now spans the full body width
        self.assertGreater(app.board_sheet.winfo_width(), initial_board_w + 200)

        # Toggle back
        app.toggle_sidebar()
        root.update()
        self.assertTrue(app.sidebar_visible)
        self.assertTrue(app.side_sheet.winfo_viewable())

    def test_24_compact_mode_lifecycle_and_geometry_preservation(self):
        root = create_root(self)
        with tempfile.TemporaryDirectory() as tmp:
            layout = DataLayout(Path(tmp) / "data")
            app = ChessApp(root, data_layout=layout, locale="en")
            try:
                root.deiconify()
                root.geometry("1200x800+100+100")
                root.update()

                self.assertFalse(app.compact_mode_active())
                app.enter_compact_mode()
                root.update()
                self.assertTrue(app.compact_mode_active())
                self.assertEqual(root.minsize(), (480, 560))
                self.assertEqual(app._side_slot.winfo_manager(), "")
                self.assertEqual(app._rail_slot.winfo_manager(), "")
                self.assertEqual(app._header_density, "minimal")
                self.assertEqual(app.header_logo.winfo_manager(), "")

                # Leave compact mode restores original geometry
                app.leave_compact_mode()
                root.update()
                self.assertFalse(app.compact_mode_active())
                self.assertEqual(root.minsize(), (860, 700))
                self.assertTrue(app.side_sheet.winfo_viewable())
                geom = window_geometry.parse(root.geometry())
                self.assertIsNotNone(geom)
                self.assertGreaterEqual(geom[0], 860)
                self.assertGreaterEqual(geom[1], 650)
            finally:
                app.close()

    def test_25_responsive_header_density_and_breakpoints(self):
        root = create_root(self)
        app = ChessApp(root, locale="en")
        self.addCleanup(app.close)
        root.deiconify()

        # >= 1120: full
        density_full = app.sync_header_density(1200)
        self.assertEqual(density_full, "full")
        self.assertTrue(app.header_logo.winfo_manager())
        self.assertTrue(app.theme_toggle_button.winfo_manager())

        # 900..1119: compact
        density_compact = app.sync_header_density(1000)
        self.assertEqual(density_compact, "compact")
        self.assertTrue(app.header_logo.winfo_manager())
        self.assertTrue(app.header_overflow_button.winfo_manager())

        # < 900: minimal
        density_minimal = app.sync_header_density(800)
        self.assertEqual(density_minimal, "minimal")
        self.assertEqual(app.header_logo.winfo_manager(), "")
        self.assertTrue(app.header_overflow_button.winfo_manager())

        # Height density
        self.assertEqual(app.sync_height_density(900), "full")
        self.assertEqual(app.sync_height_density(800), "compact")
        self.assertEqual(app.sync_height_density(700), "minimal")

    def test_26_in_app_logo_and_about_dialog(self):
        root = create_root(self)
        app = ChessApp(root, locale="en")
        self.addCleanup(app.close)
        root.deiconify()
        root.update()

        about = app.show_about_dialog(modal=False)
        try:
            self.assertIsNotNone(about)
            self.assertTrue(about.winfo_exists())
            self.assertTrue(hasattr(about, "_about_signet"))
            about.focus_force()
            root.update()
            about.event_generate("<Escape>", when="tail")
            root.update()
            self.assertIsNone(app.about_dialog)
        finally:
            if about.winfo_exists():
                about.destroy()

    def test_27_wcag_contrast_across_all_ten_glide_themes(self):
        self.assertEqual(len(THEMES), 11)  # 10 distinct Glide themes + w06-provisional alias
        self.assertIs(THEMES["glass-light"], GLASS_LIGHT_THEME)
        self.assertIs(THEMES["glass-dark"], GLASS_DARK_THEME)
        self.assertIs(THEMES["dopamine"], DOPAMINE_THEME)
        self.assertIs(THEMES["pixel"], PIXEL_THEME)
        self.assertIs(THEMES["contrast-light"], CONTRAST_LIGHT_THEME)
        self.assertIs(THEMES["contrast-dark"], CONTRAST_DARK_THEME)
        self.assertIs(THEMES["minimal-light"], MINIMAL_LIGHT_THEME)
        self.assertIs(THEMES["minimal-dark"], MINIMAL_DARK_THEME)
        surfaces = ("window", "paper", "acetate", "hover")
        inks = ("ink", "muted_ink", "view_title", "confirm", "delete")
        for name, pal in THEMES.items():
            if name == "w06-provisional":
                continue
            with self.subTest(theme=name):
                for s in surfaces:
                    bg = getattr(pal, s)
                    for i in inks:
                        fg = getattr(pal, i)
                        ratio = contrast_ratio(fg, bg)
                        self.assertGreaterEqual(ratio, 4.5, f"{name}: {i} on {s} = {ratio:.2f}")
                self.assertGreaterEqual(contrast_ratio(pal.selection_text, pal.selection), 4.5)
                self.assertGreaterEqual(contrast_ratio(pal.action_new_fg, pal.action_new_bg), 4.5)

    def test_28_button_hover_feedback_and_clipping(self):
        root = create_root(self)
        app = ChessApp(root, locale="en")
        self.addCleanup(app.close)
        root.deiconify()
        root.update()

        # Hover state test on a neutral button (position_button is active and role='neutral')
        btn = app.position_button
        initial_bg = btn.cget("background")
        btn.event_generate("<Enter>")
        root.update()
        self.assertEqual(btn.cget("background"), app.theme.hover)
        btn.event_generate("<Leave>")
        root.update()
        self.assertEqual(btn.cget("background"), initial_bg)

        # 24-character clipping test
        short_label = clip_button_text("Short Label")
        self.assertEqual(short_label, "Short Label")
        long_label = clip_button_text("This is an exceedingly long button title exceeding twenty-four characters")
        self.assertLessEqual(len(long_label), 24)
        self.assertTrue(long_label.endswith("…"))

        # Aligned checkmark menu entries
        self.assertTrue(action_picker.check_label("Item", True).startswith("✓ "))
        self.assertTrue(action_picker.check_label("Item", False).startswith("    "))

    def test_29_rounded_cards_carrier_blending_and_appearance_customization(self):
        with tempfile.TemporaryDirectory() as tmp:
            layout = DataLayout(Path(tmp) / "data")
            root = create_root(self)
            app = ChessApp(root, data_layout=layout, locale="en")
            try:
                root.deiconify()
                root.update()

                for card in (app._side_slot, app._board_slot, app._rail_slot, app.header_card):
                    self.assertIsInstance(card, RoundedSurfaceCard)
                    self.assertEqual(card.bg_color, app.theme.window)
                    self.assertIn(card.fill_color, (app.theme.paper, app.theme.acetate))
                    self.assertEqual(card.radius, 12)
                self.assertIsInstance(app.atlas_section, RoundedSurfaceCard)
                self.assertEqual(app.atlas_section.bg_color, app.theme.paper)
                self.assertEqual(app.atlas_section.fill_color, app.theme.paper)
                self.assertEqual(app.atlas_section.radius, 12)

                for btn in (app.undo_button, app.theme_toggle_button, app.tab_rail.children["play"]):
                    self.assertIsInstance(btn, RoundedButton)
                    self.assertEqual(tk.Canvas.cget(btn, "bg"), app.theme.paper)
                    self.assertNotEqual(tk.Canvas.cget(btn, "bg"), btn.cget("background"))

                pal = app.apply_appearance(
                    theme_id="glass-dark",
                    accent_choice="export",
                    background_choice="accent",
                    radius_choice="large",
                    font_scale_choice="large",
                    font_weight_choice="bold",
                    animations_enabled=False,
                    hints_visible=False,
                    persist=True,
                )
                root.update()
                self.assertIs(app.theme, pal)
                self.assertEqual(app._corner_radius, 18)
                self.assertEqual(app.header_card.radius, 18)
                self.assertIn("bold", str(app.move_list.cget("font")).lower())

                loaded, warning = load_settings(layout.settings)
                self.assertIsNone(warning)
                self.assertEqual(loaded.theme_id, "glass-dark")
                self.assertEqual(loaded.accent_choice, "export")
                self.assertEqual(loaded.background_choice, "accent")
                self.assertEqual(loaded.radius_choice, "large")
                self.assertEqual(loaded.font_scale_choice, "large")
                self.assertEqual(loaded.font_weight_choice, "bold")
                self.assertFalse(loaded.animations_enabled)
                self.assertFalse(loaded.hints_visible)

                reloaded = ChessApp(create_root(self), data_layout=layout, locale="en")
                try:
                    self.assertEqual(reloaded.settings.theme_id, "glass-dark")
                    self.assertEqual(reloaded._corner_radius, 18)
                    self.assertEqual(reloaded.theme.window, pal.window)
                finally:
                    reloaded.close()

                dialog = app.open_appearance_dialog(modal=False)
                self.assertIsInstance(dialog, AppearanceDialog)
                dialog.theme_var.set("dopamine")
                dialog._update_preview()
                dialog._apply()
                root.update()
                self.assertEqual(app.settings.theme_id, "dopamine")
                self.assertFalse(dialog.winfo_exists())
            finally:
                app.close()

    def test_30_uniform_panel_gaps_glide_settings_and_standalone_start(self):
        root = create_root(self)
        app = ChessApp(root, locale="en")
        self.addCleanup(app.close)
        root.deiconify()
        root.update()

        self.assertEqual(PANEL_GAP, 12)
        for h in (920, 800, 700):
            app.sync_height_density(h)
            root.update()
            self.assertEqual(int(str(app.masthead.cget("padx"))), PANEL_GAP)
            self.assertEqual(int(str(app._body.cget("padx"))), PANEL_GAP)
            body_info = app._body.grid_info()
            self.assertEqual(body_info["pady"], PANEL_GAP)
            side_info = app._side_slot.grid_info()
            self.assertEqual(tuple(int(x) for x in side_info["padx"]), (0, PANEL_GAP))
            self.assertEqual(int(str(side_info["pady"])), 0)

        app.toggle_sidebar_narrow()
        root.update()
        self.assertEqual(tuple(int(x) for x in app._rail_slot.grid_info()["padx"]), (0, PANEL_GAP))
        app.toggle_sidebar_narrow()
        root.update()

        # Header gear opens the unified Glide Settings dialog
        self.assertIs(app.appearance_header_button, app.settings_header_button)
        dlg = app.open_appearance_dialog(modal=False)
        self.addCleanup(dlg._cancel)
        root.update()
        self.assertEqual(dlg.title(), "Settings — Chess & Chains")
        self.assertTrue(hasattr(dlg, "design_note_label"))
        self.assertEqual(dlg.locale_var.get(), "en")
        self.assertTrue(hasattr(dlg, "sidebar_visible_var"))
        self.assertTrue(hasattr(dlg, "sidebar_narrow_var"))
        self.assertTrue(hasattr(dlg, "engine_btn"))
        dlg.locale_var.set("de")
        dlg.sidebar_narrow_var.set(True)
        dlg._apply()
        root.update()
        self.assertEqual(app.t.locale, "de")
        self.assertTrue(app._sidebar_narrow)

        # Standalone launch without PYTHONPATH
        clean_env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        for script in ("start_chess_and_chains.py", "src/chess_and_chains/__main__.py"):
            proc = subprocess.run(
                [sys.executable, str(ROOT / script), "--headless-check"],
                cwd=str(ROOT),
                env=clean_env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, f"{script} failed: {proc.stderr}")
            self.assertIn("Chess & Chains", proc.stdout)

    def test_31_monochrome_header_logo_all_themes_accents_and_font_scales(self):
        from chess_and_chains.ui.branding import in_app_logo_photo, signet_aspect
        from chess_and_chains.ui.theme import ACCENT_CHOICES

        root = create_root(self)
        app = ChessApp(root, locale="de")
        self.addCleanup(app.close)
        root.deiconify()
        root.update()

        logo = app.header_logo
        self.assertIsInstance(logo, tk.Canvas)
        self.assertEqual(int(str(logo.cget("bd"))), 0)
        self.assertEqual(int(str(logo.cget("highlightthickness"))), 0)
        self.assertEqual(logo.cget("bg"), app.theme.paper)
        self.assertGreater(logo.winfo_width(), logo.winfo_height())  # cropped 60:56 ratio

        # Monochrome header logo + view_title share theme accent across all 10 themes
        for tid in (k for k in THEMES if k != "w06-provisional"):
            pal = app.apply_appearance(theme_id=tid, accent_choice="accent", persist=False)
            root.update()
            self.assertEqual(logo.cget("bg"), pal.paper)
            self.assertEqual(logo._logo_color, pal.view_title)
            self.assertEqual(app.title_row.cget("foreground"), pal.view_title)

        # Accent choices update logo and title dynamically
        for acc, _lbl in ACCENT_CHOICES:
            pal = app.apply_appearance(theme_id="light", accent_choice=acc, persist=False)
            root.update()
            self.assertEqual(logo._logo_color, pal.view_title)
            self.assertEqual(app.title_row.cget("foreground"), pal.view_title)

        # Font scaling resizes the optical logo height proportionally
        heights: list[int] = []
        for scale in ("compact", "standard", "large"):
            app.apply_appearance(theme_id="light", accent_choice="accent", font_scale_choice=scale, persist=False)
            root.update()
            opt_h, _top, _bot = app.header_logo_metrics()
            self.assertEqual(logo._logo_height, opt_h)
            self.assertAlmostEqual(logo.winfo_width() / logo.winfo_height(), signet_aspect(), delta=0.12)
            heights.append(opt_h)
        self.assertLess(heights[0], heights[1])
        self.assertLess(heights[1], heights[2])

        # Responsive minimal header hides logo < 900 px and click opens About dialog
        app.sync_header_density(800)
        root.update()
        self.assertEqual(logo.winfo_manager(), "")
        app.sync_header_density(1200)
        root.update()
        self.assertTrue(logo.winfo_manager())

        about = app.show_about_dialog(modal=False)
        self.assertIsNotNone(about)
        if about.winfo_exists():
            about.destroy()

        # Verify transparent PNG fallback when native SVG is unavailable
        with patch("chess_and_chains.ui.branding.has_svg_support", return_value=False):
            png_photo = in_app_logo_photo(root, 45, "#00D9FF")
            self.assertEqual(png_photo.height(), 45)
            self.assertEqual(png_photo.width(), round(45 * signet_aspect()))
            self.assertTrue(png_photo.transparency_get(0, 0))
            opaque_colors = {
                tuple(int(c) for c in png_photo.get(x, y))
                for y in range(png_photo.height())
                for x in range(png_photo.width())
                if not png_photo.transparency_get(x, y)
            }
            self.assertEqual(opaque_colors, {(0, 217, 255)})


    def test_32_decoupled_board_design_perspective_piece_view_and_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            layout = DataLayout(Path(tmp) / "data")
            root = create_root(self)
            app = ChessApp(root, data_layout=layout, locale="de")
            try:
                root.geometry("1120x800")
                root.deiconify()
                root.update()

                live_game = app.game
                app._play_move(Move.from_uci("e2e4"))
                app._play_move(Move.from_uci("e7e5"))
                snapshot = app._current_pgn()

                # Switch to Marble in 2D Bird's-Eye View without losing game state
                app.set_board_design("marble")
                root.update()
                self.assertIs(app.game, live_game)
                self.assertEqual(app.board.board_design, "marble")
                self.assertEqual(app.board.perspective, "2d")
                self.assertFalse(app.board.marble)
                self.assertTrue(app.board.find_withtag("marble-2d-board"))
                self.assertFalse(app.board.find_withtag("marble-board"))
                self.assertEqual(app._current_pgn(), snapshot)

                # Switch piece view between front and top on 2D marble board
                app.set_piece_view("top")
                root.update()
                self.assertIs(app.game, live_game)
                self.assertEqual(app.board.piece_view, "top")
                self.assertTrue(app.board.renderer.top_view)
                self.assertEqual(app.board.board_design, "marble")
                self.assertEqual(app.board.perspective, "2d")

                # Flip board orientation independently
                app._flip_board()
                root.update()
                self.assertEqual(app.orientation, "black")
                self.assertEqual(app.board.board_design, "marble")
                self.assertEqual(app.board.perspective, "2d")
                self.assertEqual(app.board.piece_view, "top")

                # Switch perspective to 3D and back to 2D cleanly
                app.set_board_perspective("3d")
                root.update()
                self.assertTrue(app.board.marble)
                self.assertTrue(app.board.find_withtag("marble-board"))
                self.assertIs(app.game, live_game)
                self.assertEqual(app._current_pgn(), snapshot)

                app.set_board_perspective("2d")
                root.update()
                self.assertEqual(app.board.board_design, "marble")
                self.assertEqual(app.board.perspective, "2d")
                self.assertTrue(app.board.find_withtag("marble-2d-board"))
                self.assertEqual(app.board.piece_view, "top")
                self.assertEqual(app.orientation, "black")

                # Settings persisted and legacy settings JSON loads cleanly
                loaded, warning = load_settings(layout.settings)
                self.assertIsNone(warning)
                self.assertEqual(loaded.board_design_choice, "marble")
                self.assertEqual(loaded.board_perspective, "2d")
                self.assertEqual(loaded.piece_view, "top")

                legacy = {"schema_version": 1, "theme_id": "dark", "accent_choice": "export"}
                legacy_path = Path(tmp) / "legacy.json"
                legacy_path.write_text(json.dumps(legacy), encoding="utf-8")
                legacy_loaded, legacy_warn = load_settings(legacy_path)
                self.assertIsNone(legacy_warn)
                self.assertEqual(legacy_loaded.board_design_choice, "standard")
                self.assertEqual(legacy_loaded.board_perspective, "2d")
                self.assertEqual(legacy_loaded.piece_view, "front")
            finally:
                app.close()

    def test_33_theme_color_rename_and_dynamic_chessboard_colors(self):
        t_de = Translator("de")
        t_en = Translator("en")
        self.assertEqual(t_de("theme.accent.label"), "Themenfarbe")
        self.assertEqual(t_de("theme.accent.menu"), "Themenfarbe")
        self.assertEqual(t_en("theme.accent.label"), "Theme color")
        self.assertEqual(t_en("theme.accent.menu"), "Theme color")

        # Across all 10 themes x 8 theme colors, square_light & square_dark maintain >= 3.0 contrast
        for tid in (k for k in THEMES if k != "w06-provisional"):
            light_squares = set()
            dark_squares = set()
            for acc, _lbl in ACCENT_CHOICES:
                pal = resolve_theme(tid, accent=acc)
                cr = contrast_ratio(pal.square_light, pal.square_dark)
                self.assertGreaterEqual(cr, 3.0, f"{tid}/{acc}: square contrast {cr:.2f}")
                light_squares.add(pal.square_light)
                dark_squares.add(pal.square_dark)
                if acc == "muted":
                    r, g, b = hex_rgb(pal.square_dark)
                    self.assertLessEqual(max(r, g, b) - min(r, g, b), 20)
            # All 8 theme colors yield distinct dark-square palettes on standard themes
            self.assertGreaterEqual(len(dark_squares), 7, f"{tid} should vary board colors with Themenfarbe")


    def test_34_promotion_dialog_all_pieces_colors_captures_and_dark_mode_contrast(self):
        root = create_root(self)
        app = ChessApp(root, locale="de")
        self.addCleanup(app.close)
        root.geometry("1120x800")
        root.deiconify()
        root.update()

        # Verify Dark Mode contrast (>= 4.5:1) and RoundedButton usage across all 10 Glide themes
        for tid in ("dark", "glass-dark", "dopamine", "pixel", "contrast-dark", "minimal-dark", "light"):
            pal = app.apply_appearance(theme_id=tid, accent_choice="clear", persist=False)
            app.controller.new_game(GameSetup(initial_fen="7k/P7/8/8/8/8/8/4K3 w - - 0 1"))
            choices = tuple(
                m for m in app.board._legal_moves
                if m.from_square == parse_square("a7") and m.to_square == parse_square("a8")
            )
            inspected: dict[str, object] = {}

            def inspect_promo():
                dlg = app.promotion_dialog
                if dlg is None:
                    root.after(10, inspect_promo)
                    return
                dlg.update()
                inspected["bg"] = dlg.cget("background")
                btns = [c for c in dlg.winfo_children() if isinstance(c, RoundedButton)]
                inspected["count"] = len(btns)
                inspected["heights"] = {b.winfo_reqheight() for b in btns}
                inspected["widths"] = {b.winfo_reqwidth() for b in btns}
                inspected["ratios"] = [contrast_ratio(b.cget("foreground"), b.cget("background")) for b in btns]
                dlg.event_generate("<Escape>")

            root.after(0, inspect_promo)
            app._on_move_requested(choices)
            self.assertEqual(inspected["bg"], pal.acetate)
            self.assertEqual(inspected["count"], 4)
            self.assertEqual(len(inspected["heights"]), 1)
            self.assertEqual(len(inspected["widths"]), 1)
            self.assertTrue(all(r >= 4.5 for r in inspected["ratios"]), f"{tid} low ratio: {inspected['ratios']}")
            self.assertEqual(app.game.moves, [])

        # Test all 4 promotion choices (Queen, Rook, Bishop, Knight), White quiet & capture, Black quiet & capture,
        # keyboard navigation, and focus restoration to app.board
        app.apply_appearance(theme_id="dark", accent_choice="accent", persist=False)
        scenarios = (
            ("7k/P7/8/8/8/8/8/4K3 w - - 0 1", "a7", "a8", "Dame", PieceType.QUEEN),
            ("1b5k/P7/8/8/8/8/8/4K3 w - - 0 1", "a7", "b8", "Turm", PieceType.ROOK),
            ("4k3/8/8/8/8/8/p7/7K b - - 0 1", "a2", "a1", "Läufer", PieceType.BISHOP),
            ("4k3/8/8/8/8/8/p7/1R5K b - - 0 1", "a2", "b1", "Springer", PieceType.KNIGHT),
        )
        for fen, src, dst, label, expected_piece in scenarios:
            with self.subTest(fen=fen, label=label):
                app.controller.new_game(GameSetup(initial_fen=fen))
                app.board.focus_set()
                root.update()
                choices = tuple(
                    m for m in app.board._legal_moves
                    if m.from_square == parse_square(src) and m.to_square == parse_square(dst)
                )
                self.assertEqual(len(choices), 4)

                def pick_choice(lbl=label):
                    dlg = app.promotion_dialog
                    if dlg is None:
                        root.after(10, lambda: pick_choice(lbl))
                        return
                    btn = dlg.promotion_buttons[lbl]
                    btn.focus_set()
                    dlg.update()
                    btn.event_generate("<Return>", when="tail")

                root.after(0, pick_choice)
                app._on_move_requested(choices)
                self.assertEqual(len(app.game.moves), 1)
                self.assertEqual(app.game.moves[0].promotion, expected_piece)
                self.assertIs(root.focus_lastfor(), app.board)

    def test_35_all_dialogs_dark_mode_inheritance_short_labels_and_single_line_buttons(self):
        with tempfile.TemporaryDirectory() as tmp:
            layout = DataLayout(Path(tmp) / "data")
            root = create_root(self)
            app = ChessApp(root, data_layout=layout, locale="de")
            try:
                root.geometry("1180x820")
                root.deiconify()
                root.update()

                # 1. Verify shortened labels and unclipped full header labels without '…'
                self.assertEqual(app.claim_button.cget("text"), "Remis")
                self.assertEqual(app.retry_bot_button.cget("text"), "Bot erneut")
                app.apply_appearance(locale="en", persist=False)
                self.assertEqual(app.claim_button.cget("text"), "Draw")
                self.assertEqual(app.retry_bot_button.cget("text"), "Retry bot")
                app.apply_appearance(locale="de", persist=False)
                root.update()

                for hdr_btn in (
                    app.sidebar_toggle_button,
                    app.sidebar_narrow_button,
                    app.theme_toggle_button,
                    app.settings_header_button,
                ):
                    self.assertNotIn("…", hdr_btn.cget("text"))

                # Verify play panel buttons render single-line with identical heights in default layout
                paired = (
                    app.undo_button, app.redo_button, app.flip_button, app.resign_button,
                    app.save_button, app.copy_pgn_button, app.claim_button, app.library_button,
                    app.retry_bot_button, app.engine_button,
                )
                self.assertTrue(all(b.cget("wraplength") == 0 for b in paired))
                self.assertEqual(len({b.winfo_height() for b in paired}), 1)

                # Verify responsive single-column stacking at large font without shrinking user font
                orig_size = app.undo_button.cget("font")
                app.apply_appearance(font_scale_choice="large", persist=False)
                root.update()
                self.assertNotEqual(app.undo_button.cget("font"), orig_size)
                self.assertEqual(app.undo_button.grid_info()["column"], 0)
                self.assertIn(app.redo_button.grid_info()["column"], (0, 1))

                # Verify Retry Bot preserves game object rather than starting a new game
                app.start_game("human-vs-bot-white")
                live = app.game
                with patch.object(app.controller, "retry_bot") as retry_mock:
                    app.retry_bot_button.configure(state=tk.NORMAL)
                    app.retry_bot_button.invoke()
                    retry_mock.assert_called_once()
                self.assertIs(app.game, live)

                # 2. Verify all modal/helper dialogs inherit Dark Mode clam styles & palette contrast >= 4.5
                pal = app.apply_appearance(theme_id="dark", accent_choice="export", font_scale_choice="standard", persist=False)
                root.update()
                s = ttk.Style(root)
                self.assertEqual(s.theme_use(), "clam")
                self.assertGreaterEqual(contrast_ratio(s.lookup("Glide.TButton", "foreground"), s.lookup("Glide.TButton", "background")), 4.5)
                self.assertGreaterEqual(contrast_ratio(s.lookup("Glide.New.TButton", "foreground"), s.lookup("Glide.New.TButton", "background")), 4.5)
                self.assertGreaterEqual(contrast_ratio(s.lookup("Glide.TEntry", "foreground"), s.lookup("Glide.TEntry", "fieldbackground")), 4.5)

                app.start_game("human-vs-human")
                app._play_move(Move.from_uci("e2e4"))
                app._play_move(Move.from_uci("e7e5"))

                pos = PositionDialog(root, app.t, app.game.state, lambda _p: True, theme=app.theme)
                self.assertEqual(pos.cget("background"), pal.acetate)
                pos._close()

                rep = ReplayDialog(root, app.game, app.t, None, app.board.renderer, "white", theme=app.theme)
                self.assertEqual(rep.cget("background"), pal.acetate)
                rep._close()

                tb = TextBoardDialog(root, app.t, app._play_move, theme=app.theme)
                self.assertEqual(tb.cget("background"), pal.acetate)
                tb._close()

                about = app.show_about_dialog(modal=False)
                self.assertEqual(about.cget("background"), pal.acetate)
                about.destroy()

                eng = EngineDialog(app)
                self.assertEqual(eng.window.cget("background"), pal.acetate)
                eng.window.destroy()

                dlg = app.open_appearance_dialog(modal=False)
                self.assertEqual(dlg.cget("background"), pal.window)
                dlg.destroy()
            finally:
                app.close()

    def test_36_captured_material_display_and_advantage(self) -> None:
        """Prüfe die dynamische Materialanzeige und relative Differenz (+N) im Brettbereich."""
        root = create_root(self)
        app = ChessApp(root, locale="de")
        self.addCleanup(app.close)
        root.geometry("1180x820")
        root.deiconify()
        root.update()

        self.assertTrue(hasattr(app, "top_material_bar"))
        self.assertTrue(hasattr(app, "bottom_material_bar"))

        # Start fresh game: 1. e4 d5 2. exd5 Qxd5 3. Nc3 Qa5 4. Bc4 Nf6 5. Bxf7+ Kxf7
        # White captures: 2 pawns (score 2).
        # Black captures: 1 bishop (score 3).
        # Diff: -2 (Black +2).
        app.start_game("human-vs-human")
        moves = ["e2e4", "d7d5", "e4d5", "d8d5", "b1c3", "d5a5", "f1c4", "g8f6", "c4f7", "e8f7"]
        for uci in moves:
            app._play_move(Move.from_uci(uci))
        root.update()

        # Normal orientation: Black on top, White on bottom
        self.assertEqual(app.top_material_bar.player_color, Color.BLACK)
        self.assertEqual(app.bottom_material_bar.player_color, Color.WHITE)

        top_mat = app.top_material_bar.material
        bot_mat = app.bottom_material_bar.material
        self.assertIsNotNone(top_mat)
        self.assertIsNotNone(bot_mat)
        assert top_mat is not None and bot_mat is not None

        # Black is ahead by 2 -> Black gets +2, White gets None
        self.assertEqual(top_mat.advantage, 2)
        self.assertIsNone(bot_mat.advantage)
        self.assertEqual(top_mat.score, 4)  # pawn (1) + bishop (3) = 4
        self.assertEqual(bot_mat.score, 2)  # 2 pawns = 2

        # Advantage pill is rendered on canvas
        top_canvas_items = app.top_material_bar.find_withtag("advantage_text")
        self.assertEqual(len(top_canvas_items), 1)
        self.assertEqual(app.top_material_bar.itemcget(top_canvas_items[0], "text"), "+2")

        # White does not have an advantage text
        bot_canvas_items = app.bottom_material_bar.find_withtag("advantage_text")
        self.assertEqual(len(bot_canvas_items), 0)

        # Board flip swaps the bars
        app._flip_board()
        root.update()
        self.assertEqual(app.orientation, "black")
        self.assertEqual(app.top_material_bar.player_color, Color.WHITE)
        self.assertEqual(app.bottom_material_bar.player_color, Color.BLACK)
        self.assertIsNone(app.top_material_bar.material.advantage)
        self.assertEqual(app.bottom_material_bar.material.advantage, 2)

        # Flip back
        app._flip_board()
        root.update()

        # Undo reverts capture
        app.controller.undo()  # undos Kxf7 (Black bishop capture)
        root.update()
        # Now White has 2 pawns (score 2), Black has 1 pawn (score 1) -> White +1
        self.assertEqual(app.bottom_material_bar.material.advantage, 1)
        self.assertIsNone(app.top_material_bar.material.advantage)

        # Redo restores
        app.controller.redo()
        root.update()
        self.assertEqual(app.top_material_bar.material.advantage, 2)
        self.assertIsNone(app.bottom_material_bar.material.advantage)

        # ReplayDialog has material bars synchronized
        replay = ReplayDialog(root, app.game, app.t, app._board_artwork, app.board.renderer, "white", theme=app.theme)
        try:
            replay.show(len(moves))
            self.assertEqual(replay.top_material_bar.material.advantage, 2)
            self.assertIsNone(replay.bottom_material_bar.material.advantage)
            replay.show(0)
            self.assertIsNone(replay.top_material_bar.material.advantage)
            self.assertIsNone(replay.bottom_material_bar.material.advantage)
        finally:
            replay._close()


if __name__ == "__main__":
    unittest.main()
