"""Translation catalogue parity and coverage of keys used by the UI."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chess_and_chains.engines.presets import load_presets  # noqa: E402
from chess_and_chains.i18n import CATALOGS, SUPPORTED_LOCALES, Translator, system_locale  # noqa: E402
from chess_and_chains.i18n.catalog import placeholders  # noqa: E402
from chess_and_chains.puzzles.pack import load_demo_pack  # noqa: E402

KEY_USE = re.compile(r"""\bself\.t\(\s*["']([a-z0-9_.]+)["']""")


class CatalogTests(unittest.TestCase):
    def test_all_locales_have_identical_keys(self):
        reference = set(CATALOGS["en"])
        for locale in SUPPORTED_LOCALES:
            with self.subTest(locale=locale):
                self.assertEqual(set(CATALOGS[locale]) ^ reference, set())

    def test_placeholders_match_across_locales(self):
        for key, text in CATALOGS["en"].items():
            for locale in SUPPORTED_LOCALES:
                with self.subTest(key=key, locale=locale):
                    self.assertEqual(placeholders(CATALOGS[locale][key]), placeholders(text))

    def test_no_empty_or_untranslated_values(self):
        same_ok = {"app.title", "header.mode.puzzle", "board.design.standard"}
        for key, text in CATALOGS["de"].items():
            with self.subTest(key=key):
                self.assertTrue(text.strip())
                if key not in same_ok and not key.startswith("bot.level"):
                    self.assertNotEqual(text, CATALOGS["en"][key], "German text equals English")

    def test_every_key_used_in_ui_exists(self):
        used = set()
        for path in (ROOT / "src" / "chess_and_chains" / "ui").glob("*.py"):
            used |= set(KEY_USE.findall(path.read_text(encoding="utf-8")))
        used |= {p.label_key for p in load_presets()}
        self.assertTrue(used, "no translation usage found")
        self.assertEqual(used - set(CATALOGS["en"]), set())

    def test_translator_and_locale_detection(self):
        t = Translator("de")
        self.assertEqual(t("status.to_move", side=t("side.white")), "Weiß am Zug")
        self.assertEqual(Translator("en")("side.black"), "Black")
        self.assertEqual(system_locale({"LANG": "de_DE.UTF-8"}), "de")
        self.assertEqual(Translator("xx").locale in SUPPORTED_LOCALES, True)
        with self.assertRaises(KeyError):
            t("does.not.exist")

    def test_chess_notation_is_not_localised(self):
        for locale in SUPPORTED_LOCALES:
            for text in CATALOGS[locale].values():
                self.assertNotRegex(text, r"\b[DTLS][a-h][1-8]\b", "German piece letters must not be used in notation")

    def test_demo_puzzle_themes_have_distinct_labels_in_both_locales(self):
        themes = {theme for puzzle in load_demo_pack().puzzles for theme in puzzle.themes}
        for locale in SUPPORTED_LOCALES:
            with self.subTest(locale=locale):
                t = Translator(locale)
                labels = {t.puzzle_theme_label(theme) for theme in themes}
                self.assertEqual(len(labels), len(themes))
                self.assertNotIn(t("puzzle.all_themes"), labels)
                for theme in themes:
                    label = t.puzzle_theme_label(theme)
                    self.assertEqual(label, t(f"puzzle.theme.{theme}"))
                    self.assertNotEqual(label, theme)

    def test_custom_puzzle_theme_keeps_its_identifier_in_the_label(self):
        self.assertEqual(Translator("de").puzzle_theme_label("localStudy"), "Kennung: localStudy")
        self.assertEqual(Translator("en").puzzle_theme_label("localStudy"), "Tag: localStudy")


if __name__ == "__main__":
    unittest.main()
