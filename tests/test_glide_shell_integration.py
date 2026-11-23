"""Regression and contract tests for Glide Shell 0.6.2 integration in Chess & Chains."""

from __future__ import annotations

import ast
import json
import os
import re
import sys
import tempfile
import tomllib
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

from chess_and_chains.chess import Move  # noqa: E402
from chess_and_chains.engines.bot import EngineConfig, UCIBot  # noqa: E402
from chess_and_chains.puzzles import load_demo_pack  # noqa: E402
from chess_and_chains.storage import DataLayout, Settings, SettingsError, default_data_dir, load_settings  # noqa: E402
from chess_and_chains.ui.app import ChessApp, EngineDialog, check_tk_version, create_app_host, launch  # noqa: E402
from chess_and_chains.ui.pieces import PIECE_FILE_NAMES, validate_svg_piece_set  # noqa: E402
from chess_and_chains.ui.theme import (  # noqa: E402
    DARK_THEME,
    LIGHT_THEME,
    THEME_MODES,
    contrast_ratio,
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
            self.addCleanup(app.close)
            app.apply_theme("dark")
            self.assertIs(app.theme, DARK_THEME)
            self.assertEqual(app.root.cget("background"), DARK_THEME.window)
            loaded, warning = load_settings(layout.settings)
            self.assertIsNone(warning)
            self.assertEqual(loaded.theme_id, "dark")

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


if __name__ == "__main__":
    unittest.main()
