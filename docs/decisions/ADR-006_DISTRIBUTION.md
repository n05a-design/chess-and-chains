# ADR-006 – Distribution und Releases

**Status: PARTIALLY DECIDED (20.11.2026).**

Der Inhaber hat GitHub als Entwicklungs- und Dokumentationsort bestätigt. Die Projektseite beschreibt das Zielbild und das geplante Verhalten der fertigen App. Die fertige, freigegebene Version soll auf GitHub veröffentlicht und gemeinsam mit den anderen Programmen im hauseigenen Software-Katalog kostenlos zum Download angeboten werden. Launch-Materialien werden erst zu einem späteren Zeitpunkt beauftragt.

GitHub Releases ist als Quelle für die im Software-Katalog verlinkten Downloads vorgesehen. WinGet via Microsoft Community-Manifest nach installierbarem Windows-Release; macOS über eigenen Homebrew-Cask-Tap `n05a-design/homebrew-apps` **nur als Namensvorschlag**, nicht als bestehendes Repo voraussetzen. Native Windows-x64 und macOS-arm64/x64-Pakete jeweils prüfen; Linux zuerst Quellstart, später Paketannahme.

Installer-Tests müssen Offline-Erststart, Engine-Nutzung gemäß ADR-001, Rätsel, Einstellungen, Save/Load, Upgrade/Deinstall, Signatur- und Prüfsummendaten abdecken. Mac-Code-Signing/Notarization ist vor Veröffentlichung ein Gate; offizielle Apple-Gebühren separat planen.
