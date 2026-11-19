"""Check relative Markdown destination paths; URLs and heading anchors are out of scope."""
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r'(?<!!)\[[^\]\n]+\]\(([^)]+)\)')


def verify() -> list[str]:
    errors: list[str] = []
    for md in ROOT.rglob('*.md'):
        if any(p in ('build', 'dist', '.venv') for p in md.relative_to(ROOT).parts):
            continue
        text = md.read_text(encoding='utf-8')
        for target in LINK_RE.findall(text):
            target = target.split(' ', 1)[0].strip().strip('<>')
            if target.startswith(('https:', 'http:', 'mailto:', '#', 'data:')):
                continue
            path = unquote(target.partition('#')[0])
            if not path:
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
