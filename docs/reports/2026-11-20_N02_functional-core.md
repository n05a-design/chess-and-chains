# N02 – Functional Core: Controller, Mock-Bot, Puzzle Lab, Storage

**Datum:** 2026-11-20 13:49 CET · **Agent:** Claude Code (Claude Opus 5.5), AI-assistiert, menschliche Prüfung erforderlich ·
**Gerät:** macOS 27.2.1 arm64, Python 3.14.5, Tk 9.0 · **Branch:** `claude/chess-chains-codex-n02-237372` (Git-Worktree) ·
**Basis:** `origin/main` = `cf84659c8e3f3ea0551fd7d933b65d3aabebe0f8`

## A. Ausgangsstand

- `git fetch origin`: lokaler Worktree-HEAD war identisch mit `origin/main` (`cf84659`, PR #1 gemergt), Arbeitsbaum sauber – kein Überschreiben nötig.
- Lokaler `main`-Branch im Haupt-Checkout steht noch auf `e50494a` (9 Commits hinter `origin/main`); nicht verändert (anderer Checkout).
- Ausgangsbefund: 39 Tests grün; `project-manifest.json` erzwang über `tests/test_foundation.py` alle W00–W12 = `NOT_STARTED` trotz implementiertem W05–W07-Code; README nannte Engine-Anbindung „Not implemented“, obwohl `engines/uci.py` existierte.

### Abweichungsmatrix (priorisiert, Stand vor N02 → Behandlung)

| Prio | Abweichung | Behandlung |
| --- | --- | --- |
| P0 | Manifest/Foundation-Test erzwingen NOT_STARTED | Evidenzbasiertes Statusmodell, Baseline erhalten (`docs/governance/STATUS_MODEL.md`) |
| P0 | README/PRODUCT: „keine Engine“ vs. vorhandener UCI-Adapter | Differenziert: Adapter vorhanden, nur Mock getestet, keine echte Engine |
| P0 | Keine Verbindung UCI ↔ Spiel ↔ UI | `game/controller.py` + UI-Integration |
| P1 | TEST_PLAN listet Bot/Puzzle/Storage als NICHT IMPLEMENTIERT | Nach Umsetzung aktualisiert |
| P1 | CI: nur Ubuntu/3.11, GUI-Tests werden ohne Display stillschweigend übersprungen | Matrix + Xvfb + Skip→Fehler |
| P2 | ARCHITECTURE-Zielbild (`application/`, `persistence/`) vs. Ist | Tabelle der Ist-Schichten ergänzt |

## B. Tatsächliche Implementierung

| Modul | Inhalt |
| --- | --- |
| `scripts/verify_starter.py`, `tests/test_foundation.py` | Statusmodell NOT_STARTED…RELEASED, Pflichtnachweise, Abhängigkeitsregeln, F0-Baseline |
| `chess/notation.py` | Struktureller SAN-Parser (Messung: 150-Halbzug-PGN 5,7 s → ~0,4 s), PGN-Ergebnis-Konsistenz (Matt/Patt/automatisches Remis), `e8Q` ohne `=` |
| `chess/game.py` | `can_undo`/`can_redo` |
| `engines/uci.py` | `kill()` (erzwungenes Beenden ohne Transaktionssperre) |
| `engines/mock_engine.py` | Projekteigene Mock-UCI-Engine (Matt-in-1 > Schlagen > Zufall, Seed); Fehlermodi crash/stall/illegal/garbage. **Keine Schach-KI.** |
| `engines/presets.py`, `bot_presets.json` | 6 Presets, Validierung, `plan_options` nur für angekündigte Optionen im Bereich |
| `engines/bot.py` | `UCIBot`, `EngineConfig`, `resolve_engine_config` (Settings-Pfad / `CHESS_AND_CHAINS_ENGINE` / Mock) |
| `game/controller.py` | `GameController`: Modi Mensch–Mensch, Bot Weiß/Schwarz; Worker-Thread, Generation-IDs, Fehlerzustand + Retry, Undo bis zum menschlichen Zug, Shutdown mit Kill-Fallback, inkrementelle SAN-Liste (behebt O(n)-Neuaufbau je Refresh, gemessen 0,2 s bei 120 Halbzügen) |
| `puzzles/` | Modell, Streaming-Importer (SHA-256, Rating ≥ 1000, Duplikate filterunabhängig, legale Vollvalidierung, Report), Packs (JSONL + Manifest + Prüfsumme), `PuzzleSession` (Setup-Zug zuerst, Antworten, Hinweis, Lösung, alternatives Matt im Schlusszug), 5 projekteigene Demo-Rätsel (Eindeutigkeit per Brute-Force geprüft) |
| `storage/` | OS-Datenpfade (Repo/Paket/site-packages verweigert), SQLite v2 mit Migrationen, Backup vor Migration, Quarantäne bei Korruption, Backup/Restore, Partien/Puzzle-Fortschritt/Statistik, Settings-JSON atomar + Quarantäne |
| `i18n/` | DE/EN-Kataloge, Systemsprache, Notation bleibt international |
| `ui/app.py` | App über Controller; Modus-Auswahl, Bot-Stufe, Bot-Status mit Mock-Hinweis, Retry, Engine-Dialog (lokale Datei, Test im Thread), Aufgeben, Speichern, PGN kopieren, Strg/Cmd-Z/Y/N, Puzzle-Tab auf demselben `BoardCanvas` |
| `ui/pieces.py`, `ui/board.py` | Austauschbares `PieceRenderer`-Protokoll (Default: geometrische Testfiguren), Hint-Markierung, SVG-Asset-Vertragsprüfung (keine Darstellung/Bündelung) |
| `scripts/check_policy.py`, `scripts/build_puzzle_pack.py` | Policy-Scan; Pack-Build aus lokaler CSV |
| `.github/workflows/checks.yml` | Jobs: foundation-docs, static-security, headless (Ubuntu/Windows/macOS × 3.11/3.14), gui-linux (Xvfb), gui-native |

## C. Qualitätsnachweise (lokal ausgeführt)

| Befehl | Umgebung | Exit | Ergebnis |
| --- | --- | ---: | --- |
| `PYTHONPATH=src CHESS_AND_CHAINS_REQUIRE_DISPLAY=1 python3 -W error::ResourceWarning -m unittest discover -s tests` | macOS, Py 3.14.5, Tk 9.0 | 0 | **141 Tests, 0 Fehler, 0 Skips** (49 s) |
| gleiche Suite mit Homebrew Python 3.13.18 / 3.12.16 | macOS | 1 | 115 Tests ok, 2 Importfehler: GUI-Module, da diese Python-Builds kein `_tkinter` haben (Umgebung, kein Codefehler) |
| Headless-Module einzeln mit Python 3.13.18 | macOS | 0 | 99 Tests ok |
| `python3 scripts/verify_starter.py && python3 scripts/verify_document_links.py && python3 scripts/check_policy.py && python3 -m compileall -q src app scripts tests && git diff --check && PYTHONPATH=src python3 -m chess_and_chains --headless-check` | macOS | 0 | alle PASS |
| Native Sichtprüfung: App gestartet, Bot-Modus (e4/d4, Mock antwortet) und Puzzle-Modus (Qg8+ Rxg8) per Bildschirmaufnahme | macOS | – | Funktion sichtbar korrekt; eine macOS-Berechtigungsabfrage für Bildschirmaufnahme erschien, wurde **nicht** bestätigt; keine Screenshots eingecheckt |

Während der Arbeit gefundene und per Regressionstest abgesicherte Fehler: (1) PGN-Import quadratisch langsam, (2) Ergebnis widerspricht Matt/Patt wurde akzeptiert, (3) Promotion ohne `=` abgelehnt, (4) Duplikat-ID wurde akzeptiert, wenn das erste Vorkommen durch den Ratingfilter fiel.

Nicht geprüft: Python 3.11 lokal (nicht installiert; CI-Matrix vorgesehen), Windows/Linux nativ, High-DPI/Retina-Skalierung systematisch, Screenreader, echte UCI-Engine, realer Lichess-Export, CI-Lauf dieses Branches (nicht gepusht).

## D. Projektfortschritt – was funktioniert wirklich (lokal, macOS)

1. Zwei Personen spielen eine regelkonforme Partie mit Undo/Redo, Drehen, Zugliste, Aufgeben, PGN-Kopie, Speichern in SQLite.
2. Mensch gegen **Mock-Bot** (Weiß oder Schwarz): UI bleibt bedienbar (Event-Loop-Lücke < 250 ms gemessen bei 600 ms Bedenkzeit), veraltete Bot-Züge werden verworfen, Engine-Absturz/Timeout erscheint als Fehlerzustand mit Retry, Schließen beendet den Engine-Prozess.
3. Puzzle Lab mit 5 Demo-Rätseln: Lösen, Hinweis, Lösung zeigen, Fortschritt in SQLite.
4. Eine selbst installierte UCI-Engine kann konfiguriert werden – **ungetestet**; kein reales Offline-Bot-Spiel nachgewiesen.

## E. Lizenz und Drittkomponenten

Keine neuen Laufzeit-Abhängigkeiten, keine Engine-Binaries, keine GPL-Komponenten, keine Fremd-Assets. Demo-Rätsel sind projekteigen (MPL-2.0, Test-Wertungen). Der Lichess-Importer liest nur vom Nutzer bereitgestellte Dateien. Offene Gates: ADR-001 (Engine/Vertrieb), ADR-005 (SVG/Brand), Q-003. CairoSVG bleibt gesperrt; offene Prüfpunkte (native cairo/pango-Bibliotheken je OS, Offline-Packaging, LGPL-Bedingungen der nativen Libs, SVG-Sicherheitsgrenzen, Cache, Leistung) wurden nicht weiter untersucht, da keine Owner-SVGs vorliegen; der SVG-Vertrag (`ui/pieces.py`) definiert die Sicherheitsgrenzen vorab. XML-Prüfung nutzt stdlib ElementTree mit vorheriger Ablehnung von DOCTYPE/ENTITY (kein `defusedxml`, um keine ungeprüfte Abhängigkeit einzuführen).

## F. Dokumentationskonsistenz

Aktualisiert: `project-manifest.json` (Status + Nachweise, Baseline), `MANIFEST.md`, `README.md`, `README.de.md`, `PRODUCT.md`, `CHANGELOG.md`, `docs/roadmap/WORK_PACKAGES.md`, `docs/qa/TEST_PLAN.md`, `docs/architecture/{ARCHITECTURE,UCI_CONTRACT,DATA_CONTRACTS}.md`, `docs/questions/OPEN_QUESTIONS.md` (Q-021–Q-024), `integrations/glide_shell/INTEGRATION_GATE.md`, `data/source/README.md`; neu `docs/governance/STATUS_MODEL.md`, `docs/qa/BOT_CALIBRATION_PLAN.md`. `docs/roadmap/ROADMAP.md` und ADRs inhaltlich unverändert (keine Owner-Entscheidungen erfunden).

## G. GitHub-Stand

- Commits: lokal auf `claude/chess-chains-codex-n02-237372` (siehe `git log cf84659..HEAD`). **LOCAL – nicht gepusht, kein PR, kein Merge, keine CI-Ausführung.**
- Push/PR nur nach ausdrücklicher Owner-Freigabe (Q-019/Q-024). Nach einem Push den Remote-SHA mit `git ls-remote origin <branch>` gegen lokalen HEAD prüfen.
- Glide/Steps nur lesend geprüft: glide-to-do `4b6bce0`, steps `47af953`; keine Änderungen an anderen Repositories.

## H. Offene Owner-Fragen (priorisiert)

1. Q-024/Q-019: Push + PR dieses Branches erlauben?
2. Q-001/ADR-001: Engine-/Vertriebsweg (A: GPL-konformer Gesamtvertrieb) – blockiert echtes Bot-Spiel.
3. Q-021: Mock-Bot in Vorschau-Builds sichtbar oder ausblenden?
4. Q-003/Q-004: Owner-SVG-Figuren und Brand-Assets mit Lizenz bereitstellen.
5. Q-022: Lichess-CC0-Export lokal für Importtest herunterladen?
6. Q-008/Q-009: Ratingobergrenze und Paketgröße.
7. Q-023: Bot-Stufen mit gemessenen Elo-Spannen beschriften?
8. Q-012: Ein Profil oder mehrere?

## I. Nächste Entwicklungsrunde (priorisiert)

| # | Aufgabe | Abhängigkeit | Ziel | Tests |
| ---: | --- | --- | --- | --- |
| 1 | Branch pushen, PR öffnen, CI-Matrix grün bekommen | Q-024 | Erster CI-Nachweis für Windows/Linux/3.11 | CI-Jobs, Remote-SHA-Check |
| 2 | Echte Engine lokal testen (vom Owner installiert, Pfad via `CHESS_AND_CHAINS_ENGINE`) | Owner-Engine | Handshake/Optionsplan/Partie gegen reale Engine dokumentieren | opt-in Integrationstest, der ohne Env-Var skippt |
| 3 | Partiebibliothek-UI (Liste, Laden, Löschen, PGN-Import/-Export per Datei) | W09 | Save/Load-Gate | Tk-Integrationstests mit Temp-Layout |
| 4 | Remis-Anspruch (3-fach/50 Züge) in der UI anbieten | – | Regel-UI vollständig | App-Test mit Wiederholungsstellung |
| 5 | Puzzle-Auswahl nach Rating/Thema, ungelöste zuerst, Statistik-Anzeige | W08/W09 | Trainingsablauf | Session-/DB-Tests |
| 6 | Turnier-Runner für Bot-Kalibrierung (Skript, Seeds, Report) | ADR-001, Aufgabe 2 | `BOT_CALIBRATION_PLAN` ausführbar | Mock-Lauf in CI (kurz) |
| 7 | Zugliste klickbar (Stellung ansehen, „zurück zur Partie“) | – | Analyse-Grundlage | App-Test |
| 8 | High-DPI/Skalierung + Kontrastprüfung, Fokus-Reihenfolge, Screenreader-Notiz | W10 | Accessibility-Gate | Messbericht je OS |
| 9 | Theme-Tokens aus `ui/theme.py` in Designsystem-Datei auslagern, Theme-Wechsel | Q-004 | modulare Themes | Token-Vollständigkeitstest |
| 10 | Owner-SVG-Pipeline: Renderer-Implementierung nach CairoSVG-/Alternativprüfung | Q-003, ADR-005 | Original-Figuren | SVG-Vertrag + Pixel-Smoke-Test |
| 11 | Performance: Bitboard/Zobrist nur falls Profiling Engpässe zeigt (aktuell 1 Halbzug ≈ 4 ms) | – | Skalierung lange Partien | Benchmark-Skript mit Budget |
| 12 | PGN-Varianten/Kommentare erhalten (statt verwerfen), falls MVP es verlangt | MVP-Entscheid | Import ohne Datenverlust | Golden-PGNs |

## J. Übergabe – Einstieg für den nächsten Agenten

1. `git log --oneline cf84659..HEAD` lesen; jede Welle ist ein eigener Commit.
2. `PYTHONPATH=src python -m unittest discover -s tests` (mit Tk) – erwartet 141 grüne Tests.
3. Statusquelle: `project-manifest.json` + `docs/governance/STATUS_MODEL.md`; nie ACCEPTED/RELEASED setzen.
4. Architektur-Ist: `docs/architecture/ARCHITECTURE.md` (Tabelle „Implementierte Schichten“).
5. Nicht auf GitHub: alle N02-Commits (Stand dieses Berichts).

## Rollback

Jede Welle einzeln per `git revert <sha>` rücknehmbar. Statusmodell-Rollback setzt `foundation_baseline` außer Kraft – dann auch `tests/test_foundation.py` revertieren. Keine Datenmigrationen auf Nutzerrechnern ausgeführt (Tests nur in Temp-Verzeichnissen; Sichtprüfung nutzte ein Scratch-Datenverzeichnis außerhalb des Repos).
