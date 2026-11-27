# Functional Core und Anwendungsintegration

**27.11.2026 · V.0.3.0 · `codex/functional-core-application-integration` · Entwicklungsbranch.**

## GitHub-Abgleich

- Lokales Repository vor Arbeit war der OneDrive-Checkout mit `main` auf `9209e3de816ebde98746043ae61c34fdcbbdbfd1`. `origin` zeigte auf `n05a-design/chess-and-chains`. Die GitHub-Abfrage und `git fetch origin` identifizierten vier ausschließlich entfernte Commits bis `2c4a5940fda83f27bcfae68cb434fec6f7434859`. [PR #24](https://github.com/n05a-design/chess-and-chains/pull/24)
- Die geänderte Affinity-Datei und drei nicht versionierte V.2-SVGs waren per Bytevergleich identisch mit den GitHub-Fassungen. Die SVGs tragen im GitHub-Stand die kanonischen Namen. Agentenregeln, MPL-2.0, Markenprovenienz und der verwaltete Shell-Stand gehörten zur Ausgangsinventur. Vorhandene weitere Worktrees wurden per `git worktree list` erfasst.
- `gh run view 45899065995 -R n05a-design/chess-and-chains --json headSha,jobs` bestätigte für genau diesen Merge-Commit 14 erfolgreiche Jobs. Der neue lokale Worktree liegt außerhalb des OneDrive-Ordners und basiert direkt auf dem abgeglichenen Commit. [GitHub Actions](https://github.com/n05a-design/chess-and-chains/actions/runs/45899065995)
- Die README-Dateien von Glide und STEPS wurden über den GitHub-Connector gelesen. Der lokale Foundation-Vertrag verwendet die vorhandene Glide Shell und bindet Fachbefehle an Typen außerhalb der Präsentation. [Glide](https://github.com/n05a-design/glide-to-do/blob/main/README.md) · [STEPS](https://github.com/n05a-design/steps/blob/main/README.md)

## Änderungen und Status

Das [Funktionsinventar F01–F12](../roadmap/FUNCTIONAL_CORE.md) enthält fachliche Schnittstellen, Datenquellen, Teilnachweise und offene Gates. Die wichtigsten vertikalen Abläufe reichen von Partie und Uhr bis zur wiederhergestellten Anwendungssitzung, von gespeicherter Partie über UCI-Analyse zur Trainingsstellung sowie vom Rätselversuch zur fälligen Wiederholung.

Der fachliche Regelrahmen verwendet die FIDE-Ausgabe ab 1. Januar 2023. Der Schachkern beweist weitere tote Stellungen, wenn alle nachverfolgten Schlagvarianten in einem Patt oder einem Materialremis enden. Bei fehlendem Nachweis bleibt allgemeine Mattmöglichkeit offen. Der Zeitmodus ist als digitaler Freizeitmodus mit expliziter Pause und Entscheidung im Zweifelsfall ausgelegt. [Art. 5.2.2, 6.9 und 9.6](https://handbook.fide.com/chapter/E012023)

Die lokalen Engine-Pfade werden nur nach Benutzereingabe verwendet. UCI-Analysen verwenden einen eigenständigen Prozess. Engine-Bundles und Kalibrierung warten weiter auf ADR-001/ADR-007. Der Quell- und Lizenzrahmen der Rätsel-Feldstruktur wurde über die offizielle Lichess-Beschreibung geprüft. [Offizielle UCI-Dokumentation](https://official-stockfish.github.io/docs/stockfish-wiki/UCI-%26-Commands.html) · [Lichess-Datenbank](https://database.lichess.org/#puzzles)

### Rätsellastprobe

Werkbank macOS arm64, Python 3.14.5, synthetische Projekt-Fixtures mit eindeutigen IDs. Getrennte Prozesse, Ausführung mit weiterer lokaler Prüflast. Die Messung belegt die jeweilige Größenordnung.

| Größe | CSV-Import | Paketschreiben | Laden mit vollständiger Regelprüfung | Rating-/Themenfilter | Spitzen-RSS |
| --- | ---: | ---: | ---: | ---: | ---: |
| 20.000 | 70,48 s | 0,117 s | 68,90 s | 1,21 ms | 48,1 MiB |
| 50.000 | 170,05 s | 0,277 s | 161,27 s | 3,39 ms | 81,0 MiB |

Beide Läufe endeten mit Exitcode 0. Der 50.000er-Lauf maß 1,58 ms für eine lineare ID-Suche und im Mittel 1,33 ms zum Erzeugen einer PuzzleSession. Ein lokal komprimierter Zstandard-Demoexport wurde erfolgreich geprüft, inklusive Hash des dekomprimierten Inhalts und Manifest-Rundlauf. Die vollständige Regelprüfung beim Laden bleibt der größte Zeitfaktor. Q-022 und die Produktfilter Q-008/Q-009 bleiben offen.

## Ausgeführte Prüfungen

Darwin arm64, macOS 27.2.1 (26B131), Python 3.14.5, Tk 9.0, SQLite 3.50.4. Der Volltest lief auf `2c4a594` mit dem Entwicklungsdiff. Der geprüfte Python-Stand wurde in `6616895` und `7b9f5f9` versioniert. Daten liefen unter temporärem `CHESS_AND_CHAINS_DATA_DIR`. Native Tests verwendeten `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`.

| Befehl | Ergebnis |
| --- | --- |
| Basis: `python3 -X faulthandler -m unittest discover -s tests -v` vor den Änderungen | 364 Tests, Exit 0 |
| `python3 -X faulthandler -m unittest discover -s tests -v` mit allen Änderungen | 420 Tests, Exit 0 |
| `python3 -B scripts/build_brand_assets.py --check` | 41 abgeleitete Markenassets stimmen mit den drei Mastern überein, Exit 0 |
| `python3 scripts/ci_tests.py inventory` | 431 Tests erkannt, Exit 0 |
| `python3 scripts/ci_tests.py pytest` | 11 Figurensatztests, Exit 0 |
| `python3 scripts/ci_tests.py headless` und `python3 scripts/ci_tests.py gui` | 277 Headless- und 143 native Tk-Tests, jeweils Exit 0 |
| `python3 -m glide_shell.selftest` und `python3 -O -m glide_shell.selftest` | je 13/13, Exit 0 |
| `python3 scripts/probe_macos_file_dialogs.py` | Aqua Tk 9.0.3, Öffnen und Abbrechen von NSOpenPanel und NSSavePanel geprüft, Exit 0 |
| `python3 -m unittest tests.test_game_clock tests.test_game_session tests.test_app_integration.SessionRecoveryUiTests tests.test_app_integration.PuzzleUiTests.test_due_filter_reads_persisted_attempt_dates -q` | 16 Tests, Exit 0 |
| `python3 -m unittest tests.test_uci_engine tests.test_engine_analysis tests.test_game_clock -q` | 32 Tests zum Zeitpunkt dieses gezielten Laufs, Exit 0 |
| `python3 scripts/verify_starter.py`, `python3 scripts/verify_document_links.py`, `python3 scripts/check_policy.py`, `python3 -m compileall -q src app scripts tests` | Exit 0 im Lauf vor Fertigstellung dieses Berichts |
| `git archive 7b9f5f9` → `python3 -m pip wheel --no-index --no-build-isolation --no-deps` und Installationsprobe in Temp-Verzeichnis | Wheel 0.3.0 gebaut, lokal installiert, Headless-Start und Analyse-CLI-Hilfe geprüft, Exit 0 |
| `python3 -m chess_and_chains --version` und `--headless-check` | V.0.3.0, Exit 0 |

## QA-Matrix und Freigaben

Die CI trennt die zwölf ursprünglichen Headless-Module und neue Fachtests von den fünf nativen Tk-Modulen. Die GUI-Reihenfolge bleibt seriell. Das pytest-Inventar prüft neu hinzukommende Module und vergleicht einzelne Tests mit ihrer Runner-Zuordnung. Im CI-Runner werden unerwartete unittest-Skips als Fehler ausgegeben. Bekannte bedingte Ausnahmen sind fehlende Tk-SVG-Unterstützung im SVG-Falltest und fehlende Rechte für Symlinks in einem Windows-Test. Zwei Negativproben in einem temporären Archiv erkannten ein unzugeordnetes Testmodul und einen pytest-Test in einer unittest-Suite. Die native macOS-FEN-Panelprobe bleibt separat im Workflow. [Testplan](../qa/TEST_PLAN.md)

Die Projektversion bleibt V.0.3.0. ADR-004 bleibt PROPOSED. Mehrprofile, reale Engine, Release-Paketierung und die native Abnahme der Plattformmatrix bleiben offen. [Entscheidungsregister](../questions/OPEN_QUESTIONS.md)

## Übergabe und Rückkehr zur Basis

Der Branch entstand mit KI-Unterstützung und liegt lokal. Ein Rückwechsel zur Ausgangsversion benötigt bei migrierten Nutzerdaten die automatisch vor der Migration erstellte `.pre-v4-*.bak`-Kopie. Die Sicherung enthält den Stand vor dem Upgrade. Für eine Prüfung die vorhandenen Werkzeuge und ein getrenntes Datenverzeichnis verwenden. Die Reihenfolge für die Weiterführung steht im [Funktionsinventar](../roadmap/FUNCTIONAL_CORE.md).
