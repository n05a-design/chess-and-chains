"""Validate repository structure and the evidence-based work-package status model.

Runs without third-party modules or network access. This is a consistency
check of the manifest, not a chess, GUI or engine acceptance test.
"""
from __future__ import annotations

from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
NEEDED = [
    'START_HERE.md', 'GITHUB_SETUP.md', 'README.md', 'README.de.md', 'MANIFEST.md',
    'AGENTS.md', 'LICENSE', 'pyproject.toml',
    '.github/copilot-instructions.md', '.github/workflows/checks.yml',
    'docs/decisions/ADR_INDEX.md', 'docs/governance/DOC_INDEX.md', 'docs/questions/OPEN_QUESTIONS.md',
    'docs/research/COMPETITOR_ANALYSIS.md', 'docs/legal/LICENSE_STRATEGY.md',
    'docs/design/ASSET_REGISTER.csv', 'docs/roadmap/WORK_PACKAGES.md',
    'docs/governance/STATUS_MODEL.md',
    'integrations/glide_shell/INTEGRATION_GATE.md',
]

# Ordered from least to most mature; BLOCKED is orthogonal and ranks with IN_PROGRESS.
STATUS_ORDER = {
    'NOT_STARTED': 0,
    'IN_PROGRESS': 1,
    'BLOCKED': 1,
    'IMPLEMENTED': 2,
    'TESTED': 3,
    'ACCEPTED': 4,
    'RELEASED': 5,
}
PRODUCT_STATUSES = {
    'FOUNDATION_ONLY_NOT_PLAYABLE',
    'PROTOTYPE_LOCAL_PLAY_NOT_RELEASED',
    'ALPHA_NOT_RELEASED',
    'RELEASED',
}
BASELINE = {
    'foundation_version': 'F0',
    'snapshot_date': '2026-11-19',
    'product_status': 'FOUNDATION_ONLY_NOT_PLAYABLE',
    'work_package_status': 'NOT_STARTED',
}


def parse_dependencies(text: str) -> list[str]:
    """Expand ``W01/W02`` and ranges such as ``W05–W10`` into work IDs."""
    if not text or text.strip().lower() in ('keine', 'none', '-'):
        return []
    result: list[str] = []
    for part in re.split(r'[/,]', text):
        part = part.strip()
        match = re.fullmatch(r'W(\d{2})\s*[–-]\s*W(\d{2})', part)
        if match:
            start, end = int(match.group(1)), int(match.group(2))
            result.extend(f'W{n:02d}' for n in range(start, end + 1))
        elif re.fullmatch(r'W\d{2}', part):
            result.append(part)
        else:
            raise ValueError(f'Unparseable dependency {part!r}')
    return result


def _check_work(work: dict, by_id: dict[str, dict], errors: list[str], check_paths: bool) -> None:
    wid = work.get('id')
    status = work.get('status')
    if status not in STATUS_ORDER:
        errors.append(f'{wid}: invalid status {status}')
        return
    rank = STATUS_ORDER[status]
    evidence = work.get('status_evidence', [])
    if rank > 0 and not evidence:
        errors.append(f'{wid}: status {status} requires status_evidence')
    if check_paths:
        for path in evidence:
            if not (ROOT / path).exists():
                errors.append(f'{wid}: evidence path missing {path}')
    if status in ('IMPLEMENTED', 'TESTED', 'ACCEPTED', 'RELEASED') and not work.get('scope'):
        errors.append(f'{wid}: status {status} requires an explicit scope')
    if status in ('IMPLEMENTED', 'TESTED') and 'open_gate_items' not in work:
        errors.append(f'{wid}: status {status} must list open_gate_items (may be empty)')
    if rank >= STATUS_ORDER['TESTED'] and not any(p.startswith('tests/') for p in evidence):
        errors.append(f'{wid}: status {status} requires at least one tests/ evidence file')
    if status == 'BLOCKED' and not work.get('blocked_by'):
        errors.append(f'{wid}: BLOCKED requires blocked_by')
    if status in ('ACCEPTED', 'RELEASED'):
        acceptance = work.get('acceptance') or {}
        if not all(acceptance.get(k) for k in ('by', 'date', 'reference')):
            errors.append(f'{wid}: {status} requires acceptance.by/date/reference from the owner')
        if work.get('open_gate_items'):
            errors.append(f'{wid}: {status} cannot have open gate items')
    if status == 'RELEASED' and not (work.get('release') or {}).get('tag'):
        errors.append(f'{wid}: RELEASED requires release.tag')
    try:
        deps = parse_dependencies(work.get('depends_on', ''))
    except ValueError as error:
        errors.append(f'{wid}: {error}')
        return
    for dep in deps:
        if dep not in by_id:
            errors.append(f'{wid}: unknown dependency {dep}')
            continue
        dep_status = by_id[dep].get('status')
        if rank >= STATUS_ORDER['IMPLEMENTED'] and dep_status == 'NOT_STARTED':
            errors.append(f'{wid}: {status} although dependency {dep} is NOT_STARTED')
        if status in ('ACCEPTED', 'RELEASED') and dep_status not in ('ACCEPTED', 'RELEASED'):
            errors.append(f'{wid}: {status} requires dependency {dep} to be ACCEPTED')


def verify(manifest: dict | None = None) -> list[str]:
    """Return a list of problems; an injected manifest skips file-system checks."""
    errors: list[str] = []
    check_paths = manifest is None
    if manifest is None:
        try:
            manifest = json.loads((ROOT / 'project-manifest.json').read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as ex:
            return [f'Invalid manifest: {ex}']
        for name in NEEDED:
            if not (ROOT / name).is_file():
                errors.append(f'Missing required file: {name}')
    works = manifest.get('work_packages', [])
    ids = [x.get('id') for x in works]
    expected_ids = [f'W{n:02d}' for n in range(13)]
    if ids != expected_ids:
        errors.append(f'Expected work IDs {expected_ids}, got {ids}')
    if len(set(ids)) != len(ids):
        errors.append('Duplicate work package ID')
    by_id = {w.get('id'): w for w in works}
    for work in works:
        for key in ('prompt', 'gate', 'status', 'phase', 'title'):
            if not work.get(key):
                errors.append(f"{work.get('id')}: missing {key}")
        p = work.get('prompt', '')
        if check_paths and p and not (ROOT / p).is_file():
            errors.append(f"{work.get('id')}: prompt path missing {p}")
        _check_work(work, by_id, errors, check_paths)

    if manifest.get('foundation_baseline') != BASELINE:
        errors.append('foundation_baseline must preserve the historical F0 planning state unchanged')
    product_status = manifest.get('product_status')
    if product_status not in PRODUCT_STATUSES:
        errors.append(f'Unknown product_status {product_status}')
    if product_status == 'RELEASED' and by_id.get('W12', {}).get('status') != 'RELEASED':
        errors.append('product_status RELEASED requires W12 RELEASED')
    if manifest.get('license_gate') != 'OPEN_BLOCKS_BUNDLED_GPL_RELEASE':
        errors.append('License gate must remain open until ADR-001 is ACCEPTED by the owner')
    if 'stockfish_binary' not in manifest.get('not_included', []):
        errors.append('stockfish_binary must stay listed as not included while the license gate is open')
    return errors


if __name__ == '__main__':
    problems = verify()
    if problems:
        print('Foundation/status check FAILED:')
        for problem in problems:
            print(' -', problem)
        sys.exit(1)
    print('Foundation/status check PASS (structure + status evidence only, NOT chess functionality).')
