# W11 – Verifikation und Synchronisation gegen GitHub-Stand PR #22

**23.11.2026 · KI-gestützt (Gemini 3.8 Flash) · macOS 27.2.1, Python 3.14.5, Aqua Tk 9.0 · Branch `codex/chess-chains-w11-github-synchronisation` · Basis `origin/main` = `6044d7993322e7cc5a92b6421feb955dd8fdf066` (PR #22)**

Vollständige, nachweisbasierte Überprüfung und Abgleich der lokalen Projektablage, Codebasis, Dokumentation und Abnahmenachweise gegen den verbindlichen Remote-Referenzstand auf GitHub (`n05a-design/chess-and-chains`).

## 1. Referenzstand auf GitHub (Single Source of Truth)

| Eigenschaft | Wert |
| --- | --- |
| Repository URL | `https://github.com/n05a-design/chess-and-chains.git` |
| Default-Branch | `main` |
| Remote-HEAD Commit | `6044d7993322e7cc5a92b6421feb955dd8fdf066` |
| Commit-Titel | `Merge pull request #22 from n05a-design/codex/chess-chains-w10-w11-bedienabnahme` |
| Commit-Datum | Sun Nov 22 11:13:22 2026 +0100 |
| GitHub Releases | Keine (`gh release list`: `no releases found`) |
| Pull Requests | 22 PRs insgesamt (#1 bis #22), alle 22 erfolgreich gemerged und geschlossen |
| Remote Branches | Ausschließlich `origin/main` (alle Featurebranches nach Merge auf Remote bereinigt) |
| CI Status Remote-HEAD | Workflow `Checks` Lauf [45011373147](https://github.com/n05a-design/chess-and-chains/actions/runs/45011373147): 14 von 14 Jobs erfolgreich (Status: `✓`) |

## 2. Inventar und Analyse der lokalen Ablage

| Lokale Komponente | Zustand vor Abgleich | Ursache & Bewertung |
| --- | --- | --- |
| Lokaler Branch `main` | Stand auf `e50494a151576caad9d37dd4f62903d782846bb3` (F0-Initialcommit, 132 Commits hinter `origin/main`) | Lokaler Branch wurde nach Remote-Merges noch nicht nachgeführt. Per Fast-Forward verlustfrei auf `6044d7993322e7cc5a92b6421feb955dd8fdf066` aktualisiert. |
| Hauptcheckout `.../OneDrive/Github/chess-and-chains` | Ausgecheckt auf historischem Branch `codex/chess-and-chains-n02-functional-core` (`f8c3005`, 90 Commits hinter `main`). 15 modifizierte/gestagte Dateien, unversionierte Dateien. | **Verifiziert:** Die 6 uncommitteten Arbeitsdateien (`ADR-005`, `ASSET_REGISTER.csv`, `OPEN_QUESTIONS.md`, `N02-connected-system.md`, `app.py`, `test_app_integration.py`) sind byteidentisch mit den in PR #10/#18 archivierten Snapshots unter `docs/archive/onedrive-2026-11-21/snapshots/` (Prüfsummen in `SOURCES.csv` exakt übereinstimmend). Sie stellen keinen unveröffentlichten Code dar. |
| Unversionierte Dateien im Hauptcheckout | `design/source/connected-system`, `app/marble_3d`, `docs/design/...`, `atlas.py`, etc. | Alle Dateien existieren bereits vollständig getrackt in `origin/main`. Sie erschienen nur als untracked, weil der Checkout auf einem alten Branch vor PR #5 stand. |
| Lokale Design-SVG `V.02-Schachfiguren-Vorderansicht-Masspruefung.svg` | Stand ungetrackt in `design/brand_exploration/` (SHA-256 `e0a6733c...`) | Bytegleich bereits in `origin/main:design/source/chess_pieces/V.02-Schachfiguren-Vorderansicht-Masspruefung.svg` archiviert. |
| OneDrive-Konfliktdateien | `docs/questions/OPEN_QUESTIONS-MacBook Pro Max Ultra.md`, `src/.../app-MacBook Pro Max Ultra.py`, `tests/.../test_app_integration-MacBook Pro Max Ultra.py` | Veraltete Synchronisationskonflikte vom 20.11.2026. Bleiben bis zur Beantwortung von Q-025 unverändert gesichert. |
| Lokale Branches | 25 lokale Branches; 24 davon sind vollständig in `origin/main` enthalten. Der einzige nicht-gemergte Branch `codex/sicherung-w08-w09-vor-github-abgleich` war eine Vorab-Sicherung, deren Commits in PR #20 und #21 eingeflossen sind. |
| Saubere Prüfkopie | Erstellt als Git-Worktree `/tmp/chess-and-chains-verify` auf `main` (`6044d79`). Frei von OneDrive-Konflikten und Phantom-Dateimodus-Änderungen. |

## 3. Durchgeführte technische Prüfungen (alle reproduziert auf `6044d79`)

Umgebung: macOS 27.2.1, Python 3.14.5, Aqua Tk 9.0.3/9.0.5, Clang 17, x86_64/arm64.

| Prüfung / Befehl | Umfang | Exitcode | Ergebnis |
| --- | --- | --- | --- |
| `python3 scripts/verify_starter.py` | Statusmodell, Dokumentenstruktur und Assetregister | 0 | PASS. Keine fehlenden Pfade, Prüfsummen intakt. |
| `python3 scripts/verify_document_links.py` | Markdown-Relativlinks über alle Dokumente | 0 | PASS. Alle Zieldateien existieren. |
| `python3 scripts/check_policy.py` | Sicherheits- und Lizenz-Policy | 0 | PASS. Kein `shell=True`, keine verbotenen Netzwerk-Imports, keine Binärare-Engines. |
| `python3 -m compileall -q src app scripts tests` | Statische Kompilierung aller Python-Quellen | 0 | PASS. Keine Syntax- oder Bytecodefehler. |
| `node --check app/marble_3d/scene.js app/marble_3d/game.js` | JavaScript-Syntaxprüfung WebGL-Marmorbrett | 0 | PASS. Syntaktisch fehlerfrei. |
| `python3 -m unittest tests.test_i18n tests.test_foundation -v` | Lokalisierung & Foundation-Statusprüfungen | 0 | 23 von 23 Tests OK (0.137s). |
| `python3 -m unittest tests.test_chess_core tests.test_chess_golden tests.test_uci_engine tests.test_bot_presets tests.test_game_controller tests.test_puzzles tests.test_storage tests.test_marble_3d -v` | Headless Domain-Tests (Schachkern, Perft, UCI, Puzzles, Storage, 3D-Marmor) | 0 | 159 von 159 Tests OK (86.055s). |
| `python3 -c "..." tests.test_board_ui tests.test_app_integration -v` | Tk-GUI-Tests (mit Display, Timeouts und Fault Handler) | 0 | 71 von 71 Tests OK (16.371s). |
| `python3 scripts/probe_macos_file_dialogs.py` | Native macOS-AppKit-Dateidialoge (NSOpenPanel, NSSavePanel) | 0 | PASS. Dialoge geöffnet und abgebrochen, Grab und Draft erhalten. |
| `python3 -m unittest discover -s tests -q` | Vollständige Gesamtsuite mit Display-Zwang (`CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`) | 0 | **253 von 253 Tests OK** (65.759s). |

## 4. Bisherige Abnahmeergebnisse im Soll-Ist-Vergleich

| Abnahmedokument | Bezugsstand | Status | Begründung |
| --- | --- | --- | --- |
| `docs/reports/2026-11-22_W10-W11-bedienabnahme.md` | PR #21/PR #22 (`6044d79`) | **VERIFIZIERT** (automatisiert) / **OFFEN** (manuell) | Layoutanpassung und beide GUI-Regressionen für große Schrift und Marmorbrett lokal und in Remote-CI mit 253 Tests erfolgreich reproduziert. Die manuelle Abnahme auf physischen Zielgeräten (NVDA/VoiceOver, Ziffernblock) steht wie dokumentiert noch aus. |
| `docs/reports/2026-11-21_W09-W10-marmorbrett-dateien-wiedergabe.md` | PR #21 (`8d5bcc6`) | **VERIFIZIERT** | PGN/FEN-Dateiaustausch und Tastaturwiedergabe am Marmorbrett vollständig im Code vorhanden und durch 10 Tests in `tests/test_marble_3d.py` belegt. |
| `docs/reports/2026-11-21_W06-marmoransicht-tk.md` | PR #19/PR #21 | **VERIFIZIERT** | Umschaltung der Marmoransicht in der Tk-App vorhanden und verifiziert (`test_marble_switch_preserves_game_and_uses_projected_move_targets`). |
| `docs/reports/2026-11-21_W08-W09-wiederholtraining.md` | PR #20 (`6238724`) | **VERIFIZIERT** | Wiederholtraining im Puzzle Lab, gestufte Hinweise und Aufgaben-Neustart durch `PuzzleUiTests` erfolgreich getestet. |
| `docs/reports/2026-11-21_W11-dokumentations-und-ablageaudit.md` | PR #18 (`3407b33`) | **VERIFIZIERT** | Dokumentationsprüfung und Foundation-Fix für macOS-Pfade intakt. Archivierte Snapshots vollständig verifiziert. |
| Historische Berichte (F0, N02, W00–W07 vom 20.11.2026) | F0/N02 (< PR #8) | **HISTORISCH** | Bilden die Entstehungsgeschichte ab; funktionale Aussagen sind durch Folgereports überholt/erweitert. |

## 5. Nicht ausgeführte Prüfungen und Begründung

1. **Physische Screenreader-Abnahme (NVDA unter Windows, VoiceOver unter macOS):** Erfordert manuelle akustische und interaktive Verifikation durch einen menschlichen Prüfer. Im automatisierten CI/CLI-Agentenkontext nicht prüfbar.
2. **Eingabe mit physischem Ziffernblock:** Erfordert reale Hardware. Nicht im automatisierten Testbett abbildbar.
3. **Reale UCI-Engine / Stockfish-Offline-Bot:** W07 ist absichtlich nur mit Mock-Engine implementiert und getestet. Echte Engines sind bis zur Inhaberentscheidung ADR-001 (Lizenzgate) gesperrt.

## 6. Verbleibende Risiken und offene Maßnahmen

1. **Q-025 (Arbeitsrepository in OneDrive):** OneDrive verursacht weiterhin Phantom-Modusänderungen (`100644 → 100755`), Konfliktkopien und `index.lock`-Dateien. Empfehlung bleibt: Klon außerhalb von OneDrive anlegen (z. B. `~/Developer/chess-and-chains`).
2. **ADR-001 (Engine-Lizenz):** Bleibt der primäre Blocker für W02, W07, W12 und reale Bot-Spiele.
3. **ROADMAP.md Nachführung:** Die Roadmap endete tabellarisch bei PR #21; PR #22 wurde im aktuellen Branch nachgetragen.

## 7. Bewertung des Abnahmestatus

**BEDINGT ABGENOMMEN (V.0.0.1)**

Die technische Codebasis, alle 22 PRs und die CI auf GitHub (`6044d7993322e7cc5a92b6421feb955dd8fdf066`) sind zu 100 % nachweisbasiert verifiziert. Sämtliche 253 automatisierten Tests sowie alle Policy-, Link-, Starter- und Plattformprüfungen laufen fehlerfrei mit Exitcode 0. Die Einschränkung „bedingt“ ergibt sich zwingend aus den planmäßig noch offenen Inhaberentscheidungen (ADR-001 Lizenzgate) und den ausstehenden manuellen Hardware-/Screenreader-Prüfungen auf physischen Zielgeräten.
