# Work Packages – aktive Abhängigkeitsmatrix

**Historische Baseline (F0, 2026-11-19):** alle W00–W12 NOT_STARTED (in `project-manifest.json` als `foundation_baseline` erhalten).

**Aktueller Stand V.0.0.1 vom 21.11.2026.** Acht Pakete haben geprüfte Teilumfänge, vier sind in Arbeit und eines ist blockiert. Für kein Paket ist eine vollständige Abnahme belegt. Maßgeblich sind [Maschinenmanifest](../../project-manifest.json) und [Statusmodell](../governance/STATUS_MODEL.md). [Nachweise für W00–W12](../reports/2026-11-21_W00-W12-paketabgleich.md)

| ID | Status | Umfang des Nachweises / offene Gate-Punkte |
| --- | --- | --- |
| W00 | TESTED | Struktur-/Statusprüfung; Owner-Abnahme offen |
| W01 | IN_PROGRESS | MVP-Vertrag und Fragenregister ausgearbeitet. ADR-000 und weitere Scope-Entscheidungen offen. |
| W02 | IN_PROGRESS | Rechte- und Engine-Vergleich dokumentiert. Konkrete Vertriebsentscheidung ADR-001 und Lieferinventar offen. |
| W03 | IN_PROGRESS | Inventar mit aktuellem Glide-/Steps-Quellabgleich. Isolierte Verträge und Q-006 offen. |
| W04 | IN_PROGRESS | Quellenrecherche, Connected System und Assetregister vorhanden. Freigabe der Markenexporte und Detailentscheidungen nach ADR-005 offen. |
| W05 | TESTED | Regelkern mit Remisansprüchen, Perft, FEN und PGN-Hauptvariante geprüft. Tote Stellungen nach unmittelbaren Schlägen oder kurzen Zwangsfolgen in Patt und Materialremis werden erkannt. Allgemeine Erkennung und Gesamtregelabnahme stehen aus. [W05-Nachweis](../reports/2026-11-21_W05-mehrzuegige-tote-stellungen.md) |
| W06 | TESTED | Tk-Brett mit Vorderansichten V.02, Draufsicht, PNG-Fallbacks und Tk-9-Brettvorschau. Automatisierte Plattformmatrix erfolgreich. Finale Inhaber-Bretter, native Sichtprüfung, High-DPI und Barrierefreiheit stehen aus. [Figuren V.02](../reports/2026-11-21_W06-figurenschatten-v02.md) · [Brettvorschau](../reports/2026-11-20_W06-svg-brettvorschau.md) |
| W07 | TESTED (Mock) | Adapter, Controller, Presets und asynchroner UCI-Bereitschaftstest mit Mock-Engine. Echte Engine, ADR-001 und Kalibrierung offen. [Bereitschaftstest](../reports/2026-11-21_W07-uci-verbindungstest.md) |
| W08 | TESTED (Fixtures) | Importer mit Qualitätsgrenzen, korrekter Demo-Herkunft und reproduzierbarer Auswahl mit Seed. Pakete, Session, Themen-/Ratingfilter und Fortschritt geprüft. Realdaten nach Q-022, Qualitätsprofil und Q-008/Q-009 offen. [W08-Prüfnachweis](../reports/2026-11-21_W08-puzzle-seed.md) |
| W09 | TESTED | Windows-PGN-Dateiaustausch belegt. SQLite-Rücksicherung prüft Partiedaten vor dem Austausch. Schreibfehler und unterbrochene Transfers wurden im isolierten Test geprüft. Native Abnahmen auf macOS/Linux, Q-012 und ADR-004 offen. [W09-Prüfnachweis](../reports/2026-11-21_W09-sichere-wiederherstellung.md) |
| W10 | TESTED | Feldfokus und Tastaturabläufe einschließlich Korrektur in PR #10 geprüft. DE/EN-Rätselthemen lokal im Filter und in den Rätseldetails geprüft. CI für den Folgebranch, native Systemskalierung bei 150/200 % und Screenreader stehen aus. [W10-Prüfnachweis](../reports/2026-11-21_W10-raetselthemen.md) |
| W11 | TESTED | PR #10 mit je 14/14 Jobs auf Push, PR und `main`, einschließlich nativer macOS-GUI für Python 3.11 und 3.14. Der Prüfstand der Folgecommits steht im Entwicklungsabgleich. Native Installations- und Offline-Abnahme bleiben offen. [Entwicklungsabgleich](../reports/2026-11-21_W11-entwicklungsabgleich.md) |
| W12 | BLOCKED | Öffentliche Distribution wartet auf ADR-001, ADR-005, ADR-006 und manuelle W11-Abnahme. [Vertriebsstrategie](../release/RELEASE_STRATEGY.md) |

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
