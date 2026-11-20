"""Shared DE/EN localisation (UI language only; chess notation is unaffected)."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from .catalog import CATALOGS, DEFAULT_LOCALE, SUPPORTED_LOCALES, Translator, system_locale

__all__ = ["CATALOGS", "DEFAULT_LOCALE", "SUPPORTED_LOCALES", "Translator", "system_locale"]
