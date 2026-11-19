# ADR-006 – Distribution und Releases

**Status: PROPOSED.**

GitHub Releases als kanonische Downloadquelle; eigene Webseite als Landingpage ohne exklusive Downloads. WinGet via Microsoft Community-Manifest nach installierbarem Windows-Release; macOS über eigenen Homebrew-Cask-Tap `n05a-design/homebrew-apps` **nur als Namensvorschlag**, nicht als bestehendes Repo voraussetzen. Native Windows-x64 und macOS-arm64/x64-Pakete jeweils prüfen; Linux zuerst Quellstart, später Paketannahme.

Installer-Tests müssen Offline-Erststart, Engine-Nutzung gemäß ADR-001, Rätsel, Einstellungen, Save/Load, Upgrade/Deinstall, Signatur- und Prüfsummendaten abdecken. Mac-Code-Signing/Notarization ist vor Veröffentlichung ein Gate; offizielle Apple-Gebühren separat planen.
