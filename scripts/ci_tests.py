"""Assign every collected test to its CI runner.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import argparse
import faulthandler
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SUITES = {
    "headless": (
        "test_bot_presets",
        "test_brand_assets",
        "test_captured_material",
        "test_chess_core",
        "test_chess_golden",
        "test_engine_analysis",
        "test_engine_registry",
        "test_foundation",
        "test_game_clock",
        "test_game_controller",
        "test_game_session",
        "test_i18n",
        "test_marble_3d",
        "test_puzzles",
        "test_storage",
        "test_training",
        "test_uci_engine",
    ),
    # Keep Tk suites serial and preserve the order used by native CI.
    "gui": (
        "test_board_ui",
        "test_app_integration",
        "test_final_audit",
        "test_glide_shell_integration",
        "test_regression_audit",
    ),
    "pytest": ("test_piece_sets",),
}


def verify_inventory() -> int:
    import pytest

    assignments: dict[str, str] = {}
    for runner, modules in SUITES.items():
        for module in modules:
            if module in assignments:
                raise SystemExit(f"{module}: assigned to multiple CI runners")
            assignments[module] = runner
    tests_root = ROOT / "tests"
    test_files = {*tests_root.rglob("test_*.py"), *tests_root.rglob("*_test.py")}
    nested = sorted(path.relative_to(ROOT).as_posix() for path in test_files if path.parent != tests_root)
    if nested:
        raise SystemExit(f"Nested tests need CI assignments: {nested}")
    files = {path.stem for path in test_files}
    if files != assignments.keys():
        raise SystemExit(
            f"Missing CI assignment: {sorted(files - assignments.keys())}; "
            f"stale assignments: {sorted(assignments.keys() - files)}"
        )

    class Inventory:
        def pytest_collection_finish(self, session):
            collected = set()
            for item in session.items:
                module = item.path.stem
                collected.add(module)
                owner = getattr(item, "cls", None)
                is_unittest = isinstance(owner, type) and issubclass(owner, unittest.TestCase)
                if not is_unittest and assignments[module] != "pytest":
                    raise pytest.UsageError(f"{item.nodeid}: requires the pytest CI runner")
            empty = files - collected
            if empty:
                raise pytest.UsageError(f"No tests collected from {sorted(empty)}")

    return pytest.main(["--collect-only", "-q", "tests"], plugins=[Inventory()])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", choices=("inventory", *SUITES))
    suite = parser.parse_args().suite
    if suite == "inventory":
        return verify_inventory()
    if suite == "pytest":
        import pytest

        return pytest.main(["-rs", *(f"tests/{module}.py" for module in SUITES[suite])])
    if suite == "gui" and sys.platform != "linux":
        faulthandler.dump_traceback_later(270, exit=True)
    tests = unittest.defaultTestLoader.loadTestsFromNames(
        [f"tests.{module}" for module in SUITES[suite]]
    )
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    allowed_skips = {
        "tests.test_regression_audit.Marble2DArtworkFallbackTests.test_svg_path_returns_correct_dimensions":
            "SVG not supported in this Tk build",
    }
    if sys.platform == "win32":
        allowed_skips[
            "tests.test_puzzles.PackTests.test_local_library_rejects_redirected_library_and_pack_folders"
        ] = "Directory symlinks unavailable: "
    unexpected = [
        (test.id(), reason) for test, reason in result.skipped
        if test.id() not in allowed_skips or not reason.startswith(allowed_skips[test.id()])
    ]
    for test_id, reason in unexpected:
        print(f"Unexpected CI skip: {test_id}: {reason}", file=sys.stderr)
    return 0 if result.wasSuccessful() and not unexpected else 1


if __name__ == "__main__":
    raise SystemExit(main())
