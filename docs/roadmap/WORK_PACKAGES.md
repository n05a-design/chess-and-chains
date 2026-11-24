# Work Packages – aktive Abhängigkeitsmatrix

**Historische Baseline (F0, 2026-11-19):** alle W00–W12 NOT_STARTED (in `project-manifest.json` als `foundation_baseline` erhalten).

**Aktueller Stand V.0.3.0 vom 24.11.2026.** Acht Pakete haben geprüfte Teilumfänge, vier sind in Arbeit und eines ist blockiert. Für kein Paket ist eine vollständige Abnahme belegt. Maßgeblich sind [Maschinenmanifest](../../project-manifest.json) und [Statusmodell](../governance/STATUS_MODEL.md). [Nachweise für W00–W12](../reports/2026-11-21_W00-W12-paketabgleich.md)

| ID | Status | Umfang des Nachweises / offene Gate-Punkte |
| --- | --- | --- |
| W00 | TESTED | Struktur-, Status- und Linkprüfung; Dokumentations- und Ablageaudit vom 21.11.2026. Owner-Abnahme offen. [Audit](../reports/2026-11-21_W11-dokumentations-und-ablageaudit.md) |
| W01 | IN_PROGRESS | MVP-Vertrag und Fragenregister ausgearbeitet. ADR-000 und weitere Scope-Entscheidungen offen. |
| W02 | IN_PROGRESS | Rechte- und Engine-Vergleich dokumentiert. Konkrete Vertriebsentscheidung ADR-001 und Lieferinventar offen. |
| W03 | TESTED | Glide Shell `0.6.2` aus `n05a-design/glide-to-do` Tag `v1.0.2` (`7dcd8dc04366`) vollständig nach `src/glide_shell/` übernommen (`SHELL_MANIFEST.json`, `selftest` 13/13), `AppHost`/Dialoge/Timer/Themes/Pfade migriert, Designvertrag und Multi-Agent-Skills integriert. Owner-Abnahme von W03 offen. [Integration Gate](../../integrations/glide_shell/INTEGRATION_GATE.md) · [Bericht](../reports/2026-11-23_W03-W06-W10-glide-shell-1.0.2-integration.md) |
| W04 | IN_PROGRESS | Quellenrecherche, Connected System und Assetregister vorhanden. Freigabe der Markenexporte und Detailentscheidungen nach ADR-005 offen. |
| W05 | TESTED | Regelkern mit Remisansprüchen, Perft, FEN und PGN-Hauptvariante geprüft. Tote Stellungen werden bei kurzen Zwangsfolgen und nachweisbar geschlossenen Bauernsperren erkannt. Allgemeine Erkennung und Gesamtregelabnahme stehen aus. [Zwangsfolgen](../reports/2026-11-21_W05-mehrzuegige-tote-stellungen.md) · [Bauernsperren](../reports/2026-11-21_W05-bauernsperren.md) |
| W06 | TESTED | Tk-Brett mit V.02, Draufsicht, PNG-Fallbacks und Tk-9-Brettvorschau. Perspektivwechsel mit wiederverwendeten Feldbildern bestand nach PR #13 die Plattformmatrix. Finale Inhaber-Bretter, native Sichtprüfung, High-DPI und Barrierefreiheit stehen aus. [Figuren V.02](../reports/2026-11-21_W06-figurenschatten-v02.md) · [Brettvorschau](../reports/2026-11-21_W06-svg-brettcache.md) · [Lokaler 3D-Marmorprototyp](../reports/2026-11-21_W06_marmorbrett-3d.md) |
| W07 | TESTED (Mock) | Adapter, Controller, Presets und asynchroner UCI-Bereitschaftstest mit Mock-Engine. Echte Engine, ADR-001 und Kalibrierung offen. [Bereitschaftstest](../reports/2026-11-21_W07-uci-verbindungstest.md) |
| W08 | TESTED (Fixtures) | Offline-Builder mit Qualitätsgrenzen und Seed. Lokale Pakete werden vor der Installation geprüft und im Puzzle Lab geöffnet. Wiederholfilter, gestufte Hinweise und Aufgaben-Neustart geprüft. Realdaten nach Q-022, Qualitätsprofil und Q-008/Q-009 offen. [Rätselpakete](../reports/2026-11-21_W08-W09-lokale-raetselpakete.md) · [Training](../reports/2026-11-21_W08-W09-raetselneustart-partiewiedergabe.md) |
| W09 | TESTED | PGN/FEN-Austausch, Bibliothekssuche, Partiewiedergabe und SQLite-Rücksicherung geprüft. Lokale Rätselpakete behalten getrennten Fortschritt und die letzte Auswahl über Neustarts. Manuelle Systemdialogabnahme, Q-012 und ADR-004 offen. [FEN](../reports/2026-11-21_W05-W09-fen-austausch.md) · [Suche](../reports/2026-11-21_W09-partiebibliothek-suche.md) · [Wiedergabe](../reports/2026-11-21_W08-W09-raetselneustart-partiewiedergabe.md) · [Rücksicherung](../reports/2026-11-21_W09-sichere-wiederherstellung.md) |
| W10 | TESTED | Feldfokus und DE/EN-Rätselthemen in `main` geprüft. PGN-Import, Export und Abbruch per Tastatur mit Fokusrückkehr in PR #12 geprüft. Brett als Text mit Tastaturzügen in PR #15. Native Systemskalierung, physischer Ziffernblock und Screenreader stehen aus. [Dialogtastatur](../reports/2026-11-21_W10-dialogtastatur.md) · [Brett als Text](../reports/2026-11-21_W10-brett-als-text.md) |
| W11 | TESTED | PRs #12 bis #17 mit je 14/14 Jobs nach dem Merge in `main`, einschließlich nativer GUI-Tests auf Windows und macOS für Python 3.11 und 3.14. Native Installations-, Offline- und Artefaktabnahme stehen aus. [Merge-Lauf PR #17](https://github.com/n05a-design/chess-and-chains/actions/runs/44932980772) · [Ablageaudit](../reports/2026-11-21_W11-dokumentations-und-ablageaudit.md) |
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

## Nächster Schritt je Paket

| ID | Nächster Schritt | Wartet auf |
| --- | --- | --- |
| W00 | Owner-Abnahme der Struktur | Inhaber |
| W01 | ADR-000 bestätigen, Q-010/Q-011 beantworten | Inhaber |
| W02 | Weg A prüfen und ADR-001 entscheiden | Inhaber, Rechtsprüfung |
| W03 | Owner-Abnahme der Glide-Shell-0.6.2-Integration | Inhaber |
| W04 | Markenexporte nach ADR-005 freigeben | Inhaber |
| W05 | Weitere verblockte Stellungen und längere Zwangsfolgen | – |
| W06 | Finale Bretter prüfen, native Sichtprüfung | Bretter (Q-004), Gerät |
| W07 | Echte Engine anbinden und kalibrieren | ADR-001, ADR-007 |
| W08 | Realdatenimport mit Bericht | Q-022, Q-008, Q-009 |
| W09 | Native Dialoge macOS/Linux, Profilmodell | Q-012, ADR-004 |
| W10 | Skalierung, Screenreader, Ziffernblock nativ prüfen | Gerät |
| W11 | Installations- und Offline-Abnahme | W12-Artefakte |
| W12 | Installer bauen und prüfen | ADR-001, ADR-005, ADR-006 |

## Auftragsregeln

Keine implizite Freigabe eines Arbeitspakets durch die Existenz der jeweiligen Promptdatei. Jede Umsetzung erzeugt einen Bericht in `docs/reports/` mit SHA, diffs, Umgebung, ausgeführten Befehlen und Exitcodes. Erst nach geprüfter Abnahme `status` in `project-manifest.json` und dieser Matrix aktualisieren. Nicht blockierende Aufgaben dürfen parallel bearbeitet werden; gemeinsame Dateien nur über koordinierten Branch/PR-Prozess.
