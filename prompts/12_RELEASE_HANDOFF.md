# PROMPT 12 – Release Engineering, Homebrew, WinGet und Übergabe

**Nur nach W02+W11 und Owner-Release-Gate; bis dahin ausschließlich dokumentieren und Dry-Run vorbereiten.** Ein `main`-Commit ist keine veröffentlichte App.

**Ziel:** reproduzierbare Windows-/macOS-Installationspakete, GitHub Release und offizielle Paketmanager-Manifeste mit unveränderlichem Asset-Hash. Optional Linux nach tatsächlicher Abnahme. Runtime muss alle legalen benötigten lokalen Komponenten gemäß ADR-001 enthalten oder ausdrücklich zwischen separater Engine-Installation und Offline-Garantie unterscheiden.

**Arbeiten:** versionierte Build-Inputs, Python/Tk und Engine-Architektur, Lizenz-/Asset-SBOM, SHA-256, Windows Uninstall+Upgrade, macOS Gatekeeper/Notarization, First-run offline smoke; sauberer GitHub Release Draft mit README/Changelog/Screenshots nur nach verifizierten Featureständen. Homebrew Cask in eigenem Tap nach realem DMG+Hash; WinGet Manifest nach echtem Windows-Installer + SHA+PackageIdentifier; GitHub- und App-Webseite nur verifizierte Downloads.

**Übergabe:** Alle Schritte GitHub Remote/Tag/Release/WinGet/Homebrew als getrennte Zustände dokumentieren. Jede Aktion mit URL und Status; kein erfundener Store-Eintrag. `docs/reports/YYYY-MM-DD_W12_release.md` plus vollständiger Agent-Handoff.

**Gate:** Owner bestätigt ausdrücklich Public Release; sonst endet Auftrag mit Release-Candidate-/Vorbereitungsbericht, ohne Push/Merge/Publish nach außen.
