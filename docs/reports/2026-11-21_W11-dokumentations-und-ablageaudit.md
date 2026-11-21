# W11 – Dokumentations- und Ablageaudit

**21.11.2026 · Claude Code (KI-gestützt) · macOS 27.2.1, Python 3.14.5, Tk 9.0 · Branch `claude/lokale-ablage-dokumentation-2fe48f` · Basis `origin/main` = `1acd9bd` (PR #17)**

Auftrag des Inhabers im Chat: lokale Ablage und Dokumentation vollständig prüfen, Lücken schließen, danach GitHub korrigieren und verbessern, Roadmaps und Unterlagen überarbeiten. Push und PR sind für diesen Auftrag freigegeben. Ein Merge ist nicht beauftragt.

## Inventar vor der Arbeit

| Punkt | Befund |
| --- | --- |
| Remote | `https://github.com/n05a-design/chess-and-chains.git`, öffentlich, nur Branch `main` |
| Arbeitsbranch | lag 88 Commits hinter `origin/main` (Basis PR #1). Per Fast-Forward auf `1acd9bd` gebracht, keine eigenen Commits verloren |
| `git fetch` | scheiterte mit `bad object refs/remotes/origin/main-MacBook Pro Max Ultra` |
| CI auf `main` | Merge-Läufe von PR #9 bis #17 jeweils 14/14 Jobs erfolgreich ([PR #17](https://github.com/n05a-design/chess-and-chains/actions/runs/44932980772)) |
| Offene PRs, Issues, Releases | keine |

## Befunde zur lokalen Ablage

1. **OneDrive-Konfliktkopien in `.git`.** OneDrive legte Kopien mit Gerätenamen an: `refs/remotes/origin/main-MacBook Pro Max Ultra`, `config-…`, `index-…`, `FETCH_HEAD-…` und zwei Reflog-Kopien. Der Ref-Name mit Leerzeichen blockierte jeden `git fetch`. **Behoben:** nur diese eine Ref-Datei wurde nach `.git/onedrive-conflict-quarantine/refs/remotes/origin/` verschoben, nicht gelöscht. Danach lief `git fetch --prune` fehlerfrei. Die übrigen Kopien sind unverändert (Q-025).
2. **Phantom-Änderungen durch Dateirechte.** Im Worktree meldete Git 156 Dateien als geändert, ausschließlich Moduswechsel `100644 → 100755` ohne Inhaltsänderung. OneDrive setzt Ausführungsrechte. Diese Moduswechsel sind **nicht** Teil dieses PRs. Staging erfolgte mit `git -c core.fileMode=false`.
3. **Hauptcheckout im OneDrive-Ordner veraltet.** `…/Github/chess-and-chains` steht auf `codex/chess-and-chains-n02-functional-core` (`f8c3005`, 55 Commits hinter `main`) mit 12 geänderten und mehreren nicht versionierten Dateien. Die geänderten Dateien sind ältere Zwischenstände (gegenüber `main` überwiegend Löschungen), die nicht versionierten Designdateien sind bereits in `main` oder im [OneDrive-Archiv](../archive/onedrive-2026-11-21/README.md). Nichts davon wurde verändert.
4. **Nicht versionierter Bericht.** `docs/reports/2026-11-21_W04_plattenfiguren-svg.md` (7479 Byte, 21.11.2026 14:40) existiert nur im Hauptcheckout. Er beschreibt sechs Plattenfiguren-SVGs, die auf einem Windows-Rechner unter `Downloads` liegen und nicht im Repository sind. Bewusst **nicht** übernommen, weil Herkunft und Abschluss der Arbeit vom Inhaber zu bestätigen sind (Q-025).
5. **Konfliktkopien im Arbeitsbaum des Hauptcheckouts:** `src/chess_and_chains/ui/app-MacBook Pro Max Ultra.py`, `tests/test_app_integration-MacBook Pro Max Ultra.py`, `docs/questions/OPEN_QUESTIONS-MacBook Pro Max Ultra.md` und eine `.af~lock~`-Datei. Unverändert belassen.
6. **Lokale Branches.** 24 lokale Branches, alle vollständig in `origin/main` enthalten. Auf GitHub existiert nur noch `main`. Zusätzlich verwaiste Worktree-Einträge (`prunable`, Windows-Pfad) und zwei Copilot-Worktrees auf alten Ständen. Aufräumen nur nach Owner-Freigabe (Q-025).
7. **Lokaler `main`** stand 97 Commits hinter `origin/main`.

## Befunde zur Dokumentation und behobene Lücken

| Befund | Korrektur |
| --- | --- |
| Roadmap führte erledigte Arbeit (PR #13–#17) als offene Aufgaben; CI-Abschnitt endete bei PR #12 | [Roadmap](../roadmap/ROADMAP.md) neu gegliedert: Stand je Bereich, Owner-Entscheidungen nach Hebel, nur offene Aufgaben, Meilensteinvorschlag 0.1.0–1.0.0 mit Ausgangskriterien, Liste der abgeschlossenen PRs mit Merge-Läufen, Risiken |
| W06/W11 nannten „CI für den W06-Folgebranch“ als offen, obwohl PR #13 die Matrix bestand | Offene Punkte in [Work Packages](../roadmap/WORK_PACKAGES.md) und `project-manifest.json` entfernt, Belege ergänzt |
| W09/W10 ohne Bibliothekssuche (PR #16) und Brett als Text (PR #15) | Umfang und Belege ergänzt |
| Kein nächster Schritt je Paket | Tabelle „Nächster Schritt je Paket“ mit Wartegrund |
| MVP-Vertrag ohne Erfüllungsstand | Abschnitt „Erfüllungsstand V.0.0.1“ für P-01 bis P-10 im [MVP-Vertrag](../product/MVP_CONTRACT.md) |
| `START_HERE.md` bestand überwiegend aus der ZIP-Anleitung zur Neuanlage | Neuer Einstieg mit Schnellstart, Lesepfad, Arbeitsablauf und OneDrive-Hinweis. F0-Text [archiviert](../archive/f0-2026-11-19/START_HERE_F0.md) |
| 8 Berichte (W00–W07 vom 20.11.) fehlten im [Berichtsindex](README.md) | Index vollständig nach Paketen gegliedert |
| README: Zeile „Scaffolded / proposed“ veraltet, Bauernsperren fehlten (EN und DE) | Beide READMEs angeglichen |
| `CONTRIBUTING.md` und `SECURITY.md` nannten „Foundation stage“ | Auf Prototypstand gebracht, alle vier Prüfbefehle genannt |
| Keine GitHub-Issue- und PR-Vorlagen | `.github/ISSUE_TEMPLATE/` (Fehler, Idee, Owner-Entscheidung) und `.github/pull_request_template.md` |
| GitHub-Konfiguration nirgends dokumentiert | Tabelle mit Stand und Empfehlungen in [GITHUB_SETUP.md](../../GITHUB_SETUP.md) |
| Q-019 ohne Hinweis auf die gelebte Praxis der Einzelfreigaben | Ergänzt, bleibt OPEN. Neue Frage Q-025 zur Ablage außerhalb von OneDrive |

## Behobener Fehler

`tests.test_foundation.FoundationTests.test_asset_register_rejects_missing_paths_and_changed_bytes` schlug unter macOS fehl. `scripts/verify_starter.py` verglich einen aufgelösten Pfad (`/private/var/…`) mit dem nicht aufgelösten `ROOT` (`/var/…`). Korrektur: Vergleich gegen `ROOT.resolve()`. Die Foundation-Tests liefen in CI nur auf Ubuntu. Sie laufen jetzt zusätzlich in jeder Zelle der Plattformmatrix.

## GitHub

- Topics gesetzt: `chess`, `offline-first`, `python`, `desktop-app`, `chess-puzzles`, `tkinter`, `uci`, `open-source` (Vorschlag aus `GITHUB_SETUP.md`).
- Nicht geändert, da Owner-Entscheidung: Branch-Schutz, automatisches Löschen nach Merge, private Sicherheitsmeldungen, Wiki, Sichtbarkeit.

## Nachweise

Lokal auf macOS 27.2.1, Python 3.14.5, Tk 9.0, Arbeitsstand auf Basis `1acd9bd` mit den Änderungen dieses PRs, `PYTHONPATH=src`:

| Befehl | Exitcode | Ergebnis |
| --- | --- | --- |
| `python -m unittest discover -s tests` vor der Korrektur | 1 | 237 Tests, 1 Fehlschlag (Assetregister-Pfadprüfung, siehe oben) |
| `python -m unittest discover -s tests` nach der Korrektur | 0 | 237 Tests OK in 65 s, keine übersprungenen |
| `python scripts/verify_starter.py` | 0 | PASS |
| `python scripts/verify_document_links.py` | 0 | PASS |
| `python scripts/check_policy.py` | 0 | PASS |

Die CI-Ergebnisse des PRs werden im PR verlinkt. Native Sichtprüfungen gehörten nicht zu diesem Auftrag.

## Offene Punkte und nächste Schritte

1. Inhaber: Q-025 beantworten (Ablage außerhalb von OneDrive, Aufräumen der Konfliktkopien und Branches, Umgang mit dem W04-Plattenfiguren-Bericht).
2. Inhaber: GitHub-Schutzeinstellungen nach [GITHUB_SETUP.md](../../GITHUB_SETUP.md) prüfen.
3. Inhaber: Meilensteinvorschlag in der Roadmap bestätigen oder anpassen.
4. Entwicklung: Priorität 1 der Roadmap (native Bedienabnahme W10/W11).

## Rollback

Der PR ändert nur Dokumentation, Vorlagen, einen Prüfschritt im Workflow und eine Zeile in `scripts/verify_starter.py`. Rücknahme per Revert des Merge-Commits. Die verschobene Ref-Datei liegt unverändert in `.git/onedrive-conflict-quarantine/` und lässt sich zurückverschieben.
