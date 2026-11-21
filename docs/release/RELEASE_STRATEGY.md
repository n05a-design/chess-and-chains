# Release / WinGet / Homebrew – Arbeitsstrategie

**Status: PROPOSED, kein öffentlicher Download.**

**V.0.0.1** ist der versionierte Entwicklungsstand. Die Quell- und Wheel-Version
kann mit `--version` geprüft werden. Die Distribution wartet weiterhin auf die
unten stehenden Gates. [Versionspflege](../governance/GOVERNANCE.md#projektversion)

## Zielkanal

GitHub Releases mit pro Plattform signierten/validierten Paketen, Hashes, klaren Versionsnummern und nachvollziehbarem Quellstand. Website verlinkt dasselbe Release. Erst *danach* WinGet-Community-Repository und Homebrew-Tap.

## Windows

Installer-Technologie noch zu entscheiden (z. B. MSI/WiX vs. Inno Setup; jeweilige Lizenz gesondert). Unterstützte Architektur x64 zuerst; nachgewiesene Install/Uninstall/Upgrade/AV-Reputation. WinGet-Manifeste mit **realen** `InstallerUrl`, SHA256, Version, Scope, Publisher und Programm-ID erstellen. Keine fiktiven Manifest-URLs committen.

Quelle: https://learn.microsoft.com/en-us/windows/package-manager/package/repository

## macOS

ARM64 und Intel getrennt verifizieren oder Universal-Binary entscheiden; Tk/Python-Runtime und lokale UCI-Binaries benötigen Architekturkompatibilität. Signierung und Notarisierung für vertrauenswürdige Distribution prüfen; Apple-Developer-Program-Kosten berücksichtigen. Eigener Tap als Plan `n05a-design/homebrew-apps`, Cask erst mit realem DMG/ZIP und Hash. Keine automatische Veröffentlichung ohne Freigabe.

Quelle: https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap ; https://developer.apple.com/developer-id/

## Linux

Headless-Core, Quellstart und gegebenenfalls AppImage/Flatpak mit getrenntem Release-Gate; zuerst Kompatibilität nachweisen. Kein gefaktes vollständiges Linux-Paket.

## Release-Gates

- Verifiziertes Tag, Commit, Checksums, Signaturen, Quellen/BOM und Notices.
- Keine heimliche Netzverbindung in Standalone-Nutzung; Engine- und Puzzle-Dateien vollständig oder transparente separate Installation.
- Smoke-Test auf sauberer Maschine: First Run, Offline-Spiel, Puzzle, Save/Load, Update, Uninstall.
- macOS Gatekeeper, Windows SmartScreen / Installer-Sicherheit, Launch der getrennt gelieferten Engine.
- README, Changelog, Release Notes und Screenshot-Belege korrespondieren exakt mit dem Build.
- Schrift-/Grafikrechte, lokale Logs ohne PII, keine unpublizierten OneDrive-Daten.
- Owner bestätigt **PUBLIC RELEASE APPROVED** separat.

## Kein Packaging in Foundation F0

`packaging/*` enthält Pläne für Installer und Paketmanager. Das separat lokal
baubare Python-Wheel dient der Entwicklerprüfung. Die Reihenfolge der
ausstehenden Abnahmen steht in der [aktuellen Roadmap](../roadmap/ROADMAP.md).
