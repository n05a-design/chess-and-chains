"""Bot preset validation and handshake-based UCI option negotiation."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chess_and_chains.engines.presets import BotPreset, PresetError, load_presets, plan_options  # noqa: E402
from chess_and_chains.engines.uci import UCIOption  # noqa: E402


def spin(name, lo, hi, default=None):
    return UCIOption(name, "spin", f"option name {name} type spin", str(default), lo, hi)


FULL = {
    "Threads": spin("Threads", 1, 8),
    "Hash": spin("Hash", 1, 256),
    "Skill Level": spin("Skill Level", 0, 20),
    "UCI_LimitStrength": UCIOption("UCI_LimitStrength", "check", "x", "false"),
    "UCI_Elo": spin("UCI_Elo", 1320, 3190),
}


class PresetTests(unittest.TestCase):
    def test_bundled_presets_are_valid_and_ordered(self):
        presets = load_presets()
        self.assertGreaterEqual(len(presets), 6)
        times = [p.movetime_ms for p in presets]
        self.assertEqual(times, sorted(times))
        skills = [p.skill_level for p in presets]
        self.assertEqual(skills, sorted(skills))

    def test_preset_file_makes_no_strength_claim(self):
        raw = json.loads((Path(__file__).resolve().parents[1] / "src/chess_and_chains/engines/bot_presets.json").read_text())
        self.assertIn("NOT measured", raw["note"])
        for preset in raw["presets"]:
            self.assertNotIn("elo", preset["label_key"].lower())

    def test_invalid_presets_are_rejected(self):
        with self.assertRaises(PresetError):
            BotPreset("x", "k", 0)
        with self.assertRaises(PresetError):
            BotPreset("bad id!", "k", 10)
        with self.assertRaises(PresetError):
            BotPreset("x", "k", 10, threads=True)
        with self.assertRaises(PresetError):
            load_presets('{"schema_version": 2, "presets": []}')
        with self.assertRaises(PresetError):
            load_presets('{"schema_version": 1, "presets": [{"id": "a", "label_key": "k", "movetime_ms": 5, "evil": 1}]}')
        with self.assertRaises(PresetError):
            load_presets("not json")

    def test_only_advertised_options_inside_range_are_sent(self):
        preset = BotPreset("p", "k", 100, skill_level=25, threads=2, hash_mb=64)
        plan = plan_options(preset, FULL)
        self.assertIn(("Threads", 2), plan.apply)
        self.assertIn(("Hash", 64), plan.apply)
        self.assertNotIn("Skill Level", dict(plan.apply))
        self.assertIn("outside advertised range", dict(plan.skipped)["Skill Level"])

    def test_engine_without_options_gets_nothing(self):
        plan = plan_options(load_presets()[3], {})
        self.assertEqual(plan.apply, ())
        self.assertTrue(all(reason == "not advertised by engine" for _, reason in plan.skipped))

    def test_elo_limit_requires_both_switch_and_value(self):
        preset = BotPreset("p", "k", 100, limit_elo=1500)
        plan = plan_options(preset, FULL)
        self.assertIn(("UCI_LimitStrength", True), plan.apply)
        self.assertIn(("UCI_Elo", 1500), plan.apply)
        partial = {k: v for k, v in FULL.items() if k != "UCI_LimitStrength"}
        plan = plan_options(preset, partial)
        self.assertNotIn("UCI_LimitStrength", dict(plan.apply))
        low = plan_options(BotPreset("p", "k", 100, limit_elo=800), FULL)
        self.assertNotIn("UCI_LimitStrength", dict(low.apply))
        self.assertNotIn("UCI_Elo", dict(low.apply))

    def test_extra_option_types_are_checked(self):
        combo = UCIOption("Style", "combo", "x", "Normal", choices=("Normal", "Risky"))
        preset = BotPreset("p", "k", 100, extra_options=(("Style", "Risky"), ("Ponder", True)))
        plan = plan_options(preset, {"Style": combo})
        self.assertIn(("Style", "Risky"), plan.apply)
        self.assertEqual(dict(plan.skipped)["Ponder"], "not advertised by engine")
        bad = plan_options(BotPreset("p", "k", 100, extra_options=(("Style", "Wild"),)), {"Style": combo})
        self.assertEqual(bad.apply, ())


if __name__ == "__main__":
    unittest.main()
