"""Validate Foundation F0 without third-party modules or network access."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
NEEDED = [
    'START_HERE.md', 'GITHUB_SETUP.md', 'README.md', 'README.de.md', 'MANIFEST.md',
    'AGENTS.md', 'LICENSE', 'pyproject.toml',
    '.github/copilot-instructions.md', '.github/workflows/checks.yml',
    'docs/decisions/ADR_INDEX.md', 'docs/governance/DOC_INDEX.md', 'docs/questions/OPEN_QUESTIONS.md',
    'docs/research/COMPETITOR_ANALYSIS.md', 'docs/legal/LICENSE_STRATEGY.md',
    'docs/design/ASSET_REGISTER.csv', 'docs/roadmap/WORK_PACKAGES.md',
    'integrations/glide_shell/INTEGRATION_GATE.md',
]

def verify() -> list[str]:
    errors = []
    try:
        manifest = json.loads((ROOT / 'project-manifest.json').read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as ex:
        return [f'Invalid manifest: {ex}']
    works = manifest.get('work_packages', [])
    ids = [x.get('id') for x in works]
    expected_ids = [f'W{n:02d}' for n in range(13)]
    if ids != expected_ids:
        errors.append(f'Expected work IDs {expected_ids}, got {ids}')
    if len(set(ids)) != len(ids):
        errors.append('Duplicate work package ID')
    for name in NEEDED:
        if not (ROOT / name).is_file():
            errors.append(f'Missing required file: {name}')
    for work in works:
        for key in ('prompt', 'gate', 'status', 'phase', 'title'):
            if not work.get(key):
                errors.append(f"{work.get('id')}: missing {key}")
        p = work.get('prompt', '')
        if p and not (ROOT / p).is_file():
            errors.append(f"{work.get('id')}: prompt path missing {p}")
        if work.get('status') not in ('NOT_STARTED','IN_PROGRESS','BLOCKED','IMPLEMENTED','TESTED','CLOSED'):
            errors.append(f"{work.get('id')}: invalid status {work.get('status')}")
    if manifest.get('product_status') != 'FOUNDATION_ONLY_NOT_PLAYABLE':
        errors.append('Product status must explicitly state foundation only')
    if manifest.get('license_gate') != 'OPEN_BLOCKS_BUNDLED_GPL_RELEASE':
        errors.append('License gate must remain open in F0')
    return errors

if __name__ == '__main__':
    problems = verify()
    if problems:
        print('Foundation check FAILED:')
        for problem in problems:
            print(' -', problem)
        sys.exit(1)
    print('Foundation check PASS (structure only, NOT chess functionality).')
