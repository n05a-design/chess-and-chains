"""These are scaffold tests, not chess-rule/GUI/engine acceptance."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from chess_and_chains import __version__  # noqa: E402
from scripts.verify_starter import verify  # noqa: E402

class FoundationTests(unittest.TestCase):
    def test_manifest_and_expected_files(self):
        self.assertEqual(verify(), [])

    def test_version_is_pre_release(self):
        self.assertEqual(__version__, '0.1.0.dev0')

    def test_cli_headless_check_does_not_open_gui(self):
        completed = subprocess.run([sys.executable, '-m', 'chess_and_chains', '--headless-check'],
            env={**__import__('os').environ, 'PYTHONPATH': str(ROOT / 'src')},
            capture_output=True, text=True, timeout=15)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('GUI prototype available', completed.stdout)

    def test_all_work_packages_are_pending(self):
        data = json.loads((ROOT / 'project-manifest.json').read_text(encoding='utf-8'))
        self.assertTrue(all(item['status']=='NOT_STARTED' for item in data['work_packages']))

if __name__ == '__main__':
    unittest.main()
