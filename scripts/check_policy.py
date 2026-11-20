"""Static policy scan: no shell=True, no network clients, no bundled engines/large binaries.

Enforces AGENTS.md privacy/licence rules mechanically. Not a full security audit.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NETWORK_MODULES = ("socket", "urllib", "http", "requests", "httpx", "aiohttp", "ftplib", "smtplib", "telnetlib")
IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(" + "|".join(NETWORK_MODULES) + r")\b", re.MULTILINE)
SHELL_RE = re.compile(r"shell\s*=\s*True")
ENGINE_NAMES = re.compile(r"(stockfish|lc0|komodo|leela)", re.IGNORECASE)
MAX_TRACKED_BYTES = 2 * 1024 * 1024


def tracked_files() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
        return [ROOT / p for p in out.decode().split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]


def check() -> list[str]:
    problems: list[str] = []
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        if SHELL_RE.search(text):
            problems.append(f"{rel}: shell=True is forbidden")
        for match in IMPORT_RE.finditer(text):
            problems.append(f"{rel}: network module import '{match.group(1)}' is forbidden (local-first)")
    for path in tracked_files():
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if path.stat().st_size > MAX_TRACKED_BYTES:
            problems.append(f"{rel}: tracked file larger than {MAX_TRACKED_BYTES} bytes")
        if rel.parts[:2] == ("engines", "binaries") and path.name != "README.md":
            problems.append(f"{rel}: engine binaries must not be committed (ADR-001)")
        if ENGINE_NAMES.search(path.name) and path.suffix not in (".md", ".py", ".json", ".csv", ".txt"):
            problems.append(f"{rel}: looks like a third-party engine artefact")
    return problems


if __name__ == "__main__":
    found = check()
    if found:
        print("Policy check FAILED:")
        for line in found:
            print(" -", line)
        sys.exit(1)
    print("Policy check PASS (no shell=True, no network imports in src, no engine binaries/large files).")
