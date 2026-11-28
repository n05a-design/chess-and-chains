"""Platform user-data locations. Never inside the package, site-packages or a Git checkout."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import os
import posixpath
import sys
from pathlib import Path
from typing import Mapping

from glide_shell import runtime_paths

APP_DIR_NAME = "Chess and Chains"
LINUX_DIR_NAME = "chess-and-chains"
DATA_DIR_ENV = "CHESS_AND_CHAINS_DATA_DIR"
_PACKAGE_ROOT = Path(__file__).resolve().parents[1]


class UnsafeDataPathError(ValueError):
    """The chosen data path would write into program files or a source checkout."""


class _SimulatedHomePath:
    """Path helper for deterministic cross-platform path tests via ``runtime_paths``."""

    def __init__(self, home: Path) -> None:
        self._home = str(home)

    def expanduser(self, value: str) -> str:
        if value == "~":
            return self._home
        if value.startswith("~/"):
            return posixpath.join(self._home, value[2:])
        return os.path.expanduser(value)

    @staticmethod
    def join(*parts: str) -> str:
        return str(Path(parts[0]).joinpath(*parts[1:]))

    @staticmethod
    def abspath(value: str) -> str:
        return value


def default_data_dir(
    platform: str | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    env = os.environ if environ is None else environ
    plat = platform or sys.platform
    override = env.get(DATA_DIR_ENV)
    if override:
        return Path(override).expanduser()
    app_name = APP_DIR_NAME if (plat == "darwin" or plat.startswith("win")) else LINUX_DIR_NAME
    if home is not None:
        resolved = runtime_paths.platform_data_dir(
            app_name, platform=plat, environ=env, path=_SimulatedHomePath(home),
        )
        return Path(resolved)
    default_dir = runtime_paths.platform_data_dir(app_name, platform=plat, environ=env)
    chosen, _overridden = runtime_paths.resolve_base(None, env, DATA_DIR_ENV, default_dir)
    return Path(chosen)


def ensure_safe_data_dir(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == _PACKAGE_ROOT or resolved.is_relative_to(_PACKAGE_ROOT):
        raise UnsafeDataPathError(f"Refusing to store user data inside the program package: {resolved}")
    if "site-packages" in resolved.parts or "dist-packages" in resolved.parts:
        raise UnsafeDataPathError(f"Refusing to store user data inside site-packages: {resolved}")
    probe = resolved
    while True:
        if (probe / ".git").exists() and (probe / "pyproject.toml").exists():
            raise UnsafeDataPathError(f"Refusing to store user data inside a source checkout: {probe}")
        if probe.parent == probe:
            break
        probe = probe.parent
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


class DataLayout:
    """Separate locations for user database, settings, imported packs and backups."""

    def __init__(self, root: Path) -> None:
        self.root = ensure_safe_data_dir(root)
        self.database = self.root / "chess_and_chains.sqlite3"
        self.settings = self.root / "settings.json"
        self.engine_registry = self.root / "engine_registry.sqlite3"
        self.analysis_cache = self.root / "analysis_cache.sqlite3"
        self.packs = self.root / "puzzle_packs"
        self.backups = self.root / "backups"
        self.import_reports = self.root / "import_reports"

    @classmethod
    def default(cls) -> DataLayout:
        return cls(default_data_dir())
