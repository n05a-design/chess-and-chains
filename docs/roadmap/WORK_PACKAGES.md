# Work Packages – aktive Abhängigkeitsmatrix

**Historische Baseline (F0, 2026-11-19):** alle W00–W12 NOT_STARTED (in `project-manifest.json` als `foundation_baseline` erhalten).

**Aktueller Stand (N02, 2026-11-20)** – maßgeblich ist `project-manifest.json` nach [Statusmodell](../governance/STATUS_MODEL.md); kein Paket ist `ACCEPTED`:

| ID | Status | Umfang des Nachweises / offene Gate-Punkte |
| --- | --- | --- |
| W00 | TESTED | Struktur-/Statusprüfung; Owner-Abnahme offen |
| W01–W04 | IN_PROGRESS | Berichte vorhanden; Owner-Fragen offen |
| W05 | TESTED | Regelkern, Remisansprüche, Perft/Golden-Tests. PGN-Import verarbeitet die Hauptvariante |
| W06 | IMPLEMENTED | Tk-Brett mit Testfiguren, automatisierte Aktions- und Umwandlungstests. Original-SVG, manuelle Plattform- und High-DPI-Abnahme offen |
| W07 | TESTED (Mock) | Adapter + Controller + Presets mit Mock-Engine; echte Engine/ADR-001/Kalibrierung offen |
| W08 | TESTED (Fixtures) | Importer, Packs, Session; realer Lichess-Import, Q-008/Q-009 offen |
| W09 | TESTED | Lokale Bibliothek, Migrieren/Sicherung/Wiederherstellung, Settings. Dateidialog für PGN, Q-012 und ADR-004 offen |
| W10 | IN_PROGRESS | DE/EN-Kataloge; Accessibility-Abnahmen offen |
| W11 | IN_PROGRESS | 12 CI-Jobs auf gemergter Basis erfolgreich. Erweiterte native Matrix für lokalen Folgebranch ausstehend |
| W12 | NOT_STARTED | – |

| ID | Workstream | Prompt | Prerequisite | Verbindliches Gate | Zielphase |
| --- | --- | --- | --- | --- | --- |
| W00 | Repo-/Starter-Inventar & Dokumentations-SSOT | [`prompts/00_MASTER_BOOTSTRAP.md`](../../prompts/00_MASTER_BOOTSTRAP.md) | keine | Clone/HEAD, F0-Struktur, README/MANIFEST/AGENTS, Link- und Manifestprüfung protokolliert | F0 |
| W01 | Produktvertrag & offene Owner-Fragen | [`prompts/01_PRODUCT_SCOPE.md`](../../prompts/01_PRODUCT_SCOPE.md) | W00 | Blick auf Nutzergruppen, MVP/Nicht-Ziele, Q-Register und ADR-000; Blocker markiert | F0 |
| W02 | Legal, Engines und Rechte | [`prompts/02_LICENSE_ENGINE_GATE.md`](../../prompts/02_LICENSE_ENGINE_GATE.md) | W00 | Belegte, getrennte Rechte-/Engine-Matrix, ADR-001 als vorgeschlagene Entscheidung; keine verbotene Bündelung | F0 |
| W03 | Glide-Shell-Audit und Modulreuse | [`prompts/03_GLIDE_SHELL_AUDIT.md`](../../prompts/03_GLIDE_SHELL_AUDIT.md) | W00 | Aktuellster Referenz-Commit, isolierbare Komponenten, Lizenz-/Testplan, Rollback; keine Komplettkopie | F0 |
| W04 | Wettbewerb, UX, Design & Assetinventar | [`prompts/04_COMPETITOR_DESIGN_RESEARCH.md`](../../prompts/04_COMPETITOR_DESIGN_RESEARCH.md) | W00 | Quellenbasierte Konkurrenzmatrix, Designsystem-Vorschlag, Asset-Herkunft und Wireframe-Fragen | F0 |
| W05 | Headless Chess Domain | [`prompts/05_CHESS_CORE.md`](../../prompts/05_CHESS_CORE.md) | W01/W02 | Regelkonformer FEN/PGN-Zugablauf mit vollständigen Prüfungen, ohne GUI/Engine-Verflechtung | F1 |
| W06 | Board, SVG, Interaktion | [`prompts/06_BOARD_UI.md`](../../prompts/06_BOARD_UI.md) | W03/W05 | Original-SVG-Rendering, Boardinteraktion, DPI/Keyboard, native UI-Gates | F1 |
| W07 | Offline-UCI-Engines & Bots | [`prompts/07_UCI_BOTS.md`](../../prompts/07_UCI_BOTS.md) | W02/W05 | UCI-Lifecycle, Fehlerbehandlung, dokumentierte Skills, physischer Offline-Test | F2 |
| W08 | Puzzle Packs, Training | [`prompts/08_PUZZLE_PIPELINE.md`](../../prompts/08_PUZZLE_PIPELINE.md) | W05 | Rechtssicherer Import, erste UCI-Aktion, Ratingminimum, Datenqualitätsberichte | F3 |
| W09 | Storage, Profile, Save/Load | [`prompts/09_STORAGE_PROFILES.md`](../../prompts/09_STORAGE_PROFILES.md) | W05/W08 | Getrennte Nutzerdaten, Migrations- und Restore-Proben, PGN/FEN-Roundtrip | F4 |
| W10 | DE/EN, Accessibility und UX-Polish | [`prompts/10_I18N_ACCESSIBILITY.md`](../../prompts/10_I18N_ACCESSIBILITY.md) | W06/W09 | DE/EN-Katalogparität, Keyboard-/Kontrast-/Scaling-Abnahmen | F4 |
| W11 | QA, Sicherheit und Nachweiskette | [`prompts/11_QA_CI_AUDIT.md`](../../prompts/11_QA_CI_AUDIT.md) | W05–W10 | Echte CI/OS/Offline-/Lieferartefakt-Belege, offene Fehler, keine erfundenen Gates | F5 |
| W12 | Releases, WinGet, Homebrew, Webseite | [`prompts/12_RELEASE_HANDOFF.md`](../../prompts/12_RELEASE_HANDOFF.md) | W02/W11 | Signierte/validierte Installer nach Owner-Freigabe; Paketmanager nur nach realer Distribution | F5 |

## Auftragsregeln

Keine implizite Freigabe eines Arbeitspakets durch die Existenz der jeweiligen Promptdatei. Jede Umsetzung erzeugt einen Bericht in `docs/reports/` mit SHA, diffs, Umgebung, ausgeführten Befehlen und Exitcodes. Erst nach geprüfter Abnahme `status` in `project-manifest.json` und dieser Matrix aktualisieren. Nicht blockierende Aufgaben dürfen parallel bearbeitet werden; gemeinsame Dateien nur über koordinierten Branch/PR-Prozess.
