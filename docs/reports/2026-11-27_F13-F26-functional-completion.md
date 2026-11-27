# Functional Completion und Product Readiness

**27.–28.11.2026 · V.0.3.0 · Zwischenstand der Phase A**

## Ausgangsstand und Arbeitsbranch

Der GitHub-Abgleich bestätigte den Merge von PR #25 in `main` bei
`67903148794aeb81c4bde312cb41f3b33f598bb4`. Alle 14 Jobs des zugehörigen
Merge-Laufs waren erfolgreich. Der lokale OneDrive-Checkout stand auf
`9209e3d`. Die Umsetzung begann vom abgeglichenen `origin/main` im
separaten Worktree `~/.codex/worktrees/chess-and-chains-functional-completion`
auf `codex/functional-completion-product-readiness`.
[PR #25](https://github.com/n05a-design/chess-and-chains/pull/25) · [CI des Merge-Commits](https://github.com/n05a-design/chess-and-chains/actions/runs/46074571237)

Geprüfter Code-Commit der Phase A ist `1f60696669395410e65281fba37d2451f0cf90bf`.
Der Branch enthält KI-unterstützte Implementierung und Dokumentation.
Der zusätzliche Rücksicherungstest nach Prozessabbruch steht in `25276cf`.
GitHub-Schreibaktionen und Release-Freigaben sind in diesem Auftrag separat zu erteilen.

## Umsetzung

- **F13.** `puzzles/catalog.py` verwaltet das separate SQLite-Katalogschema 1.
  `PackLibrary.open_catalog()`, `install_catalog()` und `install_revision()`
  verbinden es mit dem vorhandenen Pack-Vertrag und dem Puzzle Lab. Ein lokaler
  Validierungsbeleg bindet Paketquelle und Index per Prüfsummen. Datenbankabfragen
  kombinieren Rating und Thema. Die Auswahl hält IDs und lädt Rätseldaten in
  Seiten zu 48 Einträgen. Explizite Paketrevisionen behalten die Identität und
  den Fortschritt vorhandener Aufgaben.
- **F14.** Der Controller trennt Remisangebote und ausdrückliche Annahme von
  Regelbeanspruchung und Zeitablauf. Ein Zug oder Partiewechsel beendet ein
  offenes Angebot. Die automatische Partiekopie besitzt atomaren
  Schreibkonfliktschutz. Gleichlautende Abschluss-Snapshots mit identischem
  PGN erzeugen beim wiederholten Speichern dieselbe Archiv-ID. Ersetzen einer
  laufenden Partie mit Uhr löst auch vor dem ersten Zug eine Rückfrage aus.
- **F15.** SQLite v6 ergänzt das optionale Sitzungs-JSON im Partiearchiv.
  Die native Wiedergabe zeigt die Uhr je Halbzug und bei Abweichung den
  eingefrorenen Stand am Archivende. Fortsetzen erhält Ausgangsstellung,
  Modus, Zeitkontrolle und Redo-Historie, mit pausierter Uhr. SQLite v7 ergänzt
  Favoriten und referenzielle Tags. Die Bibliotheksabfrage unterstützt Zeitraum,
  Modus, Ergebnis, Engine-Referenz, Preset, Zeitkontrolle, Verknüpfungen,
  Favoriten und Tags. Das PGN-`TimeControl`-Tag deckt ganzzahlige Sekundendauern ab.
  Altdaten und PGN-Importe enthalten weiterhin nur ihre überlieferten Informationen.
- **F17.** `storage/backup_bundle.py` sowie `--create-backup` und
  `--restore-backup` sichern und restaurieren SQLite mit Settings und
  Paketverweisen. Bestehende SQLite-Sicherungen bleiben verwendbar. Ein
  Backup wird vor der Übernahme fachlich validiert. Ein separat geschriebenes
  Wiederherstellungsarchiv hält den vorherigen Datenstand einschließlich
  Settings fest. Fehler beim Settings-Austausch lösen eine Rücksetzung aus.
  Die Engine-Pfade des Zielsystems behalten ihre lokale Freigabe.
  [Datenverträge](../architecture/DATA_CONTRACTS.md)

## Statusmatrix

| Paket | Implementierung | Automatisierte Tests | Realdaten | Native Abnahme | Blocker oder verbleibende Arbeit |
| --- | --- | --- | --- | --- | --- |
| F13 Katalog | Implementiert | Index, Filter, Identität, Korruption, ältere Packs | Synthetisch bis 50.000 | macOS/Tk | Q-022 für offiziellen Lichess-Datensatz. Q-008/Q-009 für Produktkonfiguration |
| F14 Lebenszyklus | Teilweise implementiert | Remis, wiederholte Archivierung, zwei Datenbankverbindungen | Lokale Partien und projektinterner Mock | macOS/Tk | Eigenständige persistierte Lebenszyklusphasen, ausdrücklich protokollierter Engine-Wechsel und unabhängige zusätzliche Regelreferenzen offen |
| F15 Partiearchiv | Teilweise implementiert | Uhr, Timeout, Replay, Migration, Filter und Tags | Lokale Partien, PGN-Fixtures | macOS/Tk | Engine-Version und stabile Engine-ID aus F16, PGN-Uhrannotationen und UI für Archivlabels offen |
| F16 Engine-Verwaltung | Offen | Altstand und Mock | Ausstehend | Ausstehend | Persistenz und Runner technisch offen. Reale Kalibrierung und Vertrieb folgen Q-001/Q-023 |
| F17 Datenintegrität | Teilweise implementiert | ZIP, Prüfsummen, Pfade, Schema, ältere Sicherung, Rücksetzung und Prozessabbruch | Temporäre lokale Profile | CLI auf macOS | Abbruch während des Austauschs ist über das vorherige ZIP manuell rückrollbar. Mehrprofilverwaltung wartet auf Q-012. Weitere Datentypen folgen F16/F18/F19 |
| F18 Analysis Lab | Offen | Altstand | Ausstehend | Ausstehend | Persistenter Cache und Analyseausbau |
| F19 Persönliche Rätsel | Offen | Altstand | Ausstehend | Ausstehend | Generator, Validierung und Lebenszyklus |
| F20 Kettentraining | Offen | Altstand | Ausstehend | Ausstehend | Mehrere fortsetzbare Ketten |
| F21 Fortschritt | Offen | Altstand | Ausstehend | Ausstehend | Wiederholungs- und Themenstatistiken |
| F22 Positionseditor | Offen | Altstand | Ausstehend | Ausstehend | Editor und Validierung |
| F23 PGN und Study | Offen | Altstand | Ausstehend | Ausstehend | Varianten, Annotationen und Studien |
| F24 Opening und Endgame | Offen | Altstand | Ausstehend | Ausstehend | Begrenzte, freigegebene Datenquellen |
| F25 Anwendungsintegration | Offen | Altstand | Ausstehend | Ausstehend | Gemeinsam nutzbare Commands und ViewModels |
| F26 Qualität | Teilweise geprüft | Siehe Prüfnachweise | Synthetische Rätsel, eigene PGN-Fixtures, UCI-Mock | macOS/Tk | Windows/Linux für diesen Branch, native Langzeit- und Release-Abnahme, lizenzierte Engine-Sitzung |

Gate A bleibt bis zu den dokumentierten offenen Teilen von F14/F15/F17 offen.
Die Lizenzentscheidung und der Offline-Bot für den Vertrieb bleiben
Release-Voraussetzungen aus Q-001/Q-002 und ADR-001. Der Mock-Bot dient
Entwicklungstests. Q-007 und Q-016 betreffen die Plattform- und Release-Abnahme,
Q-011 die Produktauswahl der Zeitmodi. Q-019 gilt für GitHub-Schreibfreigaben.
[Owner-Entscheidungen](../questions/OPEN_QUESTIONS.md)

## Rätsellastprobe

macOS arm64, Python 3.14.5, jeweils ein separater Prozess mit synthetisch aus
fünf projekteeigenen Vorlagen erzeugten Paketdaten. Beide Läufe endeten mit
Exitcode 0. Der alte Bericht maß vollständiges Laden und Validieren. Die
Fixtures der Läufe sind nicht byte-identisch. Das neue reguläre Öffnen prüft
Manifest, JSONL und Index, während die erstmalige fachliche Validierung
weiterhin in der Größenordnung der früheren Läufe liegt.

| Metrik | 20.000 Aufgaben | 50.000 Aufgaben |
| --- | ---: | ---: |
| Früheres Laden mit vollständiger Regelprüfung | 68,90 s | 161,27 s |
| Neue vollständige Regelprüfung | 64,28 s | 160,44 s |
| Erzeugen des synthetischen JSONL | 153,29 ms | 403,06 ms |
| Index veröffentlichen | 1.056,70 ms | 2.572,32 ms |
| Vorvalidierten Index regulär öffnen | 19,56 ms | 32,68 ms |
| Kombinierter Rating-/Themenfilter | 6,28 ms | 14,35 ms |
| ID-Abruf | 0,197 ms | 0,200 ms |
| 20 IDs mit festem Seed ziehen | 0,031 ms | 0,039 ms |
| Nächste PuzzleSession einschließlich initialem Seitenabruf | 3,08 ms | 3,22 ms |
| Prozess-Spitzen-RSS über alle Phasen | 52,0 MiB | 75,7 MiB |

Der Benchmark misst den JSONL-Laufzeitkatalog und die dazu nötige flache
Testdatengenerierung. Die früheren CSV-Importmessungen stehen separat im
F01–F12-Bericht. [Frühere Rätsellastprobe](2026-11-27_F01-F12-functional-core.md)

```bash
python3 scripts/benchmark_puzzle_catalog.py 20000
python3 scripts/benchmark_puzzle_catalog.py 50000
```

## Prüfnachweise

macOS 27.2.1 (26B131) auf arm64, Python 3.14.5, SQLite 3.50.4, Tk 9.0.
Für die GUI-Suite wurde `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1` gesetzt.
Datenbank-, Profil- und Katalogtests schreiben in temporäre Testverzeichnisse.

| Befehl | Ergebnis |
| --- | --- |
| `PYTHONPATH=src python3 scripts/ci_tests.py inventory` | 467 Tests erfasst, Exit 0 |
| `PYTHONPATH=src python3 scripts/ci_tests.py headless` | 303 Tests, Exit 0 |
| `PYTHONPATH=src python3 scripts/ci_tests.py pytest` | 11 Figurensatztests, Exit 0 |
| `PYTHONPATH=src python3 scripts/ci_tests.py gui` | 153 native Tests auf macOS, Exit 0 |
| `python3 scripts/verify_starter.py` | Exit 0 |
| `python3 scripts/verify_document_links.py` | Relative Markdown-Ziele gültig, Exit 0 |
| `python3 scripts/check_policy.py` | Exit 0 |
| `python3 -B scripts/build_brand_assets.py --check` | 41 Ausgaben stimmen mit den Logo-Mastern überein, Exit 0 |
| `PYTHONPATH=src python3 -m glide_shell.selftest` | 13/13, Exit 0 |
| `PYTHONPATH=src python3 -O -m glide_shell.selftest` | 13/13, Exit 0 |
| `PYTHONPATH=src python3 -m compileall -q src/chess_and_chains` | Exit 0 |
| `PYTHONPATH=src python3 -m chess_and_chains --headless-check` | V.0.3.0, Exit 0 |
| `PYTHONPATH=src python3 -m chess_and_chains --create-backup …` und `--restore-backup …` | CLI-Rundlauf mit temporärem Datenordner, je Exit 0 |

Ein separater macOS-Lauf mit vom Betriebssystem blockiertem Netzwerk
(`sandbox-exec` mit `(deny network*)`) prüfte Sitzungswiederherstellung,
Puzzle Lab, Analysearchiv und Backup. 25 Tests, Exit 0. Der Prozessabbruchtest
prüfte die manuelle Wiederherstellung aus dem vor dem Datentausch gesicherten ZIP.

Die GitHub-Matrix gehört für diesen Branch zur ausstehenden Abnahme.
Der zitierte GitHub-Lauf prüfte den Ausgangscommit aus PR #25.

## Übergabe

1. Für Gate A zuerst F14 abschließen. Engine-Wiederherstellung an binären
   Fingerabdruck und validierte UCI-Metadaten koppeln. Ausstehende
   Lebenszyklusübergänge und unabhängige Schach-Referenztests ergänzen.
2. F15 mit PGN-Uhrannotationen und Bedienung der Archivlabels fortsetzen.
   Für F17 die künftigen persönlichen Übungen von der Löschung der Ursprungspartie
   entkoppeln. Die Wiederaufnahme nach einem Prozessabbruch kann weiter automatisiert
   werden.
3. Nach Gate A die Engine-Profile und den Benchmark-Runner (F16) sowie den
   persistenten Analyse-Cache (F18) umsetzen. Q-022 erst nach ausdrücklicher
   Freigabe für Tests am offiziellen Puzzle-Export verwenden.
4. Für Glide/Bento die vorhandenen Fachgrenzen übernehmen.
   `GameController` verwaltet Zugfolge, Rücknahme, Zeit und Remis.
   `PackLibrary` und `PuzzleSelection` bieten Katalogzugriff.
   `Database` liefert Archivoperationen und Verknüpfungen.
   `ChessApp` und `ReplayDialog` bleiben Adapter der bestehenden Oberfläche.
   [Integrationsvertrag](../architecture/BENTO_INTEGRATION_READINESS.md)

Glide Shell 0.6.2, Logo-Master, Originalfigurensets und Startdateien entsprechen
dem Ausgangsstand. Brand- und Shell-Prüfungen werden separat ausgewiesen.
