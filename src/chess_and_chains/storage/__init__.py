"""Local-first persistence: user data paths, SQLite database, JSON settings."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from .database import SCHEMA_VERSION, Database, SavedGame, SessionConflict, Statistics, StorageError
from .paths import DataLayout, UnsafeDataPathError, default_data_dir
from .settings import Settings, SettingsError, load_settings, save_settings, update_settings

__all__ = [
    "DataLayout", "Database", "SCHEMA_VERSION", "SavedGame", "SessionConflict", "Settings", "SettingsError",
    "Statistics", "StorageError", "UnsafeDataPathError", "default_data_dir", "load_settings",
    "save_settings", "update_settings",
]
