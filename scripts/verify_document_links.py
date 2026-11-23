"""Check relative Markdown destination paths; URLs and heading anchors are out of scope."""
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r'(?<!!)\[[^\]\n]+\]\(([^)]+)\)')


def _glide_shell_manifest_files() -> set[str]:
    manifest = ROOT / 'src' / 'glide_shell' / 'SHELL_MANIFEST.json'
    if not manifest.is_file():
        return set()
    try:
        data = json.loads(manifest.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return set()
    files = data.get('dateien')
    return set(files) if isinstance(files, dict) else set()


def verify() -> list[str]:
    errors: list[str] = []
    manifest_files = _glide_shell_manifest_files()
    for md in ROOT.rglob('*.md'):
        rel_parts = md.relative_to(ROOT).parts
        if any(p in ('build', 'dist', '.venv') for p in rel_parts):
            continue
        is_locked_shell_doc = (
            len(rel_parts) == 3
            and rel_parts[:2] == ('src', 'glide_shell')
            and md.name in manifest_files
        )
        text = md.read_text(encoding='utf-8')
        for target in LINK_RE.findall(text):
            target = target.split(' ', 1)[0].strip().strip('<>')
            if target.startswith(('https:', 'http:', 'mailto:', '#', 'data:')):
                continue
            path = unquote(target.partition('#')[0])
            if not path:
                continue
            if is_locked_shell_doc and path.startswith('../../../'):
                continue
            resolved = (md.parent/path).resolve()
            if not resolved.is_relative_to(ROOT.resolve()) or not resolved.exists():
                errors.append(f'{md.relative_to(ROOT)} -> {target}')
    return errors

if __name__ == '__main__':
    problems = verify()
    if problems:
        print('Broken relative document links:')
        for line in problems: print(' -', line)
        raise SystemExit(1)
    print('Markdown relative link targets: PASS (anchors/remote URLs not validated).')
