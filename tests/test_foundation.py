"""Foundation and status-model consistency tests (not chess/GUI/engine acceptance)."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))
from chess_and_chains import DISPLAY_VERSION, __version__  # noqa: E402
from scripts import verify_starter  # noqa: E402
from scripts.verify_starter import parse_dependencies, verify  # noqa: E402

MANIFEST = json.loads((ROOT / 'project-manifest.json').read_text(encoding='utf-8'))


def _with(work_id, **changes):
    data = copy.deepcopy(MANIFEST)
    for work in data['work_packages']:
        if work['id'] == work_id:
            work.update(changes)
    return data


class FoundationTests(unittest.TestCase):
    def test_manifest_and_expected_files(self):
        self.assertEqual(verify(), [])

    def test_asset_register_rejects_missing_paths_and_changed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            register = root / "docs/design/ASSET_REGISTER.csv"
            register.parent.mkdir(parents=True)
            (root / "drawing.svg").write_bytes(b"<svg/>")
            register.write_text(
                "asset_id,planned_path,source_hash\n"
                f"drawing,drawing.svg,{'0' * 64}\n"
                "drawing,missing.svg,\n",
                encoding="utf-8",
            )
            problems = []
            with patch.object(verify_starter, "ROOT", root):
                verify_starter._check_asset_register(problems)
        self.assertEqual(
            problems,
            [
                "Asset register drawing: SHA-256 mismatch for drawing.svg",
                "Asset register: duplicate ID drawing",
                "Asset register drawing: missing or invalid repository path missing.svg",
            ],
        )

    def test_project_version_matches_runtime(self):
        self.assertEqual(__version__, MANIFEST['project_version'])
        self.assertEqual(DISPLAY_VERSION, f'V.{__version__}')

    def test_archive_check_reports_changed_or_missing_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / verify_starter.ONEDRIVE_ARCHIVE
            sources.parent.mkdir(parents=True)
            (sources.parent / 'changed.txt').write_bytes(b'changed snapshot')
            sources.write_text(
                'archive_path,archive_sha256\n'
                f"changed.txt,{'0' * 64}\nmissing.txt,{'0' * 64}\n",
                encoding='utf-8',
            )
            problems = []
            with patch.object(verify_starter, 'ROOT', root):
                verify_starter._check_archive_hashes(problems)
        self.assertEqual(problems, [
            'OneDrive archive: SHA-256 mismatch for changed.txt',
            'OneDrive archive: missing or invalid snapshot path missing.txt',
        ])

    def test_project_version_rejects_display_label_in_machine_manifest(self):
        errors = verify({**MANIFEST, 'project_version': DISPLAY_VERSION})
        self.assertTrue(any('project_version must be a numeric' in error for error in errors))

    def test_cli_version_uses_project_label(self):
        completed = subprocess.run(
            [sys.executable, '-m', 'chess_and_chains', '--version'],
            env={**os.environ, 'PYTHONPATH': str(ROOT / 'src')},
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), f'Chess & Chains {DISPLAY_VERSION}')

    def test_cli_headless_check_does_not_open_gui(self):
        completed = subprocess.run(
            [sys.executable, '-m', 'chess_and_chains', '--headless-check'],
            env={**os.environ, 'PYTHONPATH': str(ROOT / 'src')},
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('GUI prototype available', completed.stdout)
        self.assertIn('no engine bundled', completed.stdout)
        self.assertIn(DISPLAY_VERSION, completed.stdout)


class StatusModelTests(unittest.TestCase):
    def test_historical_f0_baseline_is_preserved(self):
        self.assertEqual(MANIFEST['foundation_baseline']['product_status'], 'FOUNDATION_ONLY_NOT_PLAYABLE')
        self.assertEqual(MANIFEST['foundation_baseline']['work_package_status'], 'NOT_STARTED')
        broken = copy.deepcopy(MANIFEST)
        broken['foundation_baseline']['product_status'] = 'RELEASED'
        self.assertTrue(any('foundation_baseline' in e for e in verify(broken)))

    def test_acceptance_requires_owner_record_and_accepted_dependencies(self):
        errors = verify(_with('W05', status='ACCEPTED', open_gate_items=[]))
        self.assertTrue(any('acceptance.by/date/reference' in e for e in errors))
        self.assertTrue(any('dependency W01 to be ACCEPTED' in e for e in errors))

    def test_acceptance_rejects_a_remaining_blocker(self):
        data = _with(
            'W00', status='ACCEPTED', open_gate_items=[], blocked_by=['pending gate'],
            acceptance={'by': 'test owner', 'date': '2026-11-21', 'reference': 'test record'},
        )
        self.assertIn('W00: ACCEPTED cannot have open gate items', verify(data))

    def test_promotion_requires_evidence_scope_and_tests(self):
        errors = verify(_with('W12', status='IN_PROGRESS', status_evidence=[]))
        self.assertTrue(any('W12: status IN_PROGRESS requires status_evidence' in e for e in errors))
        errors = verify(_with('W10', status='TESTED', status_evidence=['docs/reports/README.md'], scope=''))
        self.assertTrue(any('W10: status TESTED requires an explicit scope' in e for e in errors))
        self.assertTrue(any('W10: status TESTED requires at least one tests/' in e for e in errors))

    def test_implemented_package_cannot_depend_on_unstarted_work(self):
        data = _with('W12', status='IMPLEMENTED', status_evidence=['docs/reports/README.md'],
                     scope='x', open_gate_items=[])
        for work in data['work_packages']:
            if work['id'] == 'W02':
                work['status'] = 'NOT_STARTED'
        self.assertTrue(any('W12: IMPLEMENTED although dependency W02 is NOT_STARTED' in e for e in verify(data)))

    def test_evidence_paths_exist(self):
        for work in MANIFEST['work_packages']:
            for path in work.get('status_evidence', []):
                with self.subTest(work=work['id'], path=path):
                    self.assertTrue((ROOT / path).exists())

    def test_license_gate_and_stockfish_exclusion_stay_open(self):
        self.assertEqual(MANIFEST['license_gate'], 'OPEN_BLOCKS_BUNDLED_GPL_RELEASE')
        self.assertIn('stockfish_binary', MANIFEST['not_included'])
        self.assertFalse(list((ROOT / 'engines' / 'binaries').glob('stockfish*')))

    def test_dependency_parser(self):
        self.assertEqual(parse_dependencies('keine'), [])
        self.assertEqual(parse_dependencies('W01/W02'), ['W01', 'W02'])
        self.assertEqual(parse_dependencies('W05–W07'), ['W05', 'W06', 'W07'])
        with self.assertRaises(ValueError):
            parse_dependencies('later')


if __name__ == '__main__':
    unittest.main()
