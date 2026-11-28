# IV-A · Stockfish 19 und lokale Abnahme

**Status: TESTED für die lokale technische IV-A-Abnahme auf Apple Silicon.**
Der IV-A-Branch bleibt lokal. ADR-001 und Q-001 sind offen. Die
Vertriebsfreigabe und native Stockfish-Prüfungen auf weiteren Plattformen
sind ausstehend.

## Basis und Ablage

PR #27 wurde als `13b27f659f5c6b7cb24c156653bb316dc6c6adf7` gemergt.
[Main-CI](https://github.com/n05a-design/chess-and-chains/actions/runs/46107871105)
bestand mit 14/14 Jobs auf macOS, Windows und Linux. Die Prüfung von IV-A
erfolgte auf macOS 27.2.1, Apple M2, Python 3.14.5. Der Branch
`codex/stockfish-iv-a` liegt im frischen Clone
`/Users/shaye/.codex/worktrees/chess-and-chains-iv-a-clean`.
Die Wiederaufnahme erfolgte auf
`f06d8b70ddc725055dd7c6890783c438694396a9`. Die Analysekorrektur liegt in
`823fb3c37118571e2fbf4e9d2e2699e4afe6008b`. Ein lesender Remote-Abgleich
bestätigte den angegebenen Main-Commit. Der reguläre OneDrive-Checkout
mit lokalen Designänderungen wurde für die Arbeit nicht verwendet.

Lokale Ablage `/Users/shaye/.local/share/chess-and-chains-iv-a/2026-11-28/stockfish-19`.
Unter `binary/` liegen `stockfish` und `exported.nnue`, unter `test-profile/learning/`
das isolierte SQLite-v8-Profil und die lokale UCI-Registry. `reports/` enthält
die Prüfskripte und Ergebnisse, `benchmarks/` die JSON- und PGN-Nachweise.
Der Katalog verweilt unter
`/Users/shaye/.local/share/chess-and-chains-iv-b/2026-11-28/lichess-core-20k`.
Die QA verwendet eine Kopie des vorhandenen Index und des Pakets.
`reports/resume/` enthält die zusätzlichen Prüfungen und Exitcodes der
Wiederaufnahme. Die lokal gespeicherten Main-CI-Metadaten liegen in
`provenance/main-actions.json`.

## Herkunft und Freigabe

[Offizieller stabiler Stockfish-19-Release](https://github.com/official-stockfish/Stockfish/releases/tag/sf_19),
Commit `edb0d9db6731067ec50ce619ff372b463bc4dd5d`. Der Download über
`curl --fail --location` und die Prüfung mit `shasum -a 256 -c`
bestätigten den veröffentlichten Archivdigest. `tar` extrahierte
Binary, Lizenz und Notices. `file`, `lipo -archs` und `otool -L`
bestätigten Mach-O arm64/x86_64 mit Systembibliotheken. Die Laufzeitprüfung
erfolgte nativ auf arm64.

| Artefakt | SHA-256 |
| --- | --- |
| stockfish-macos-universal.tar.gz | `a1f0e3bcc5a6927a11fe6fc8e54a779754645f3c2bae2cf13420fd1957adaa77` |
| stockfish | `8eed61129d1493c5d1f2fd9323f0c54c47ac49319911fbde18c6b9c87e8b13c5` |
| eingebettetes und über `export_net` exportiertes NNUE | `1a298aa575a085434d29027978dc36867fe9c5bcea9376654b7a8eba1e52dfc2` |

Die Registry verwendet die ID `9d52cd79-33d4-4a41-9ee8-3f3eac50319f` und
den Konfigurationsfingerabdruck `69ab7b1a1df264fbe2ae76a5b81ea7358063d95393bfbe2a5ef46cc120b2ce2e`.
`EvalFile` verweist auf das gehashte lokale Netz. UCI meldet Version 19
im Namen. Ein separates `id version` fehlt. Archiv, Binary, Netz und Lizenzdateien
liegen außerhalb von Git. [ADR-001](../decisions/ADR-001_ENGINE_LICENSE.md)
und Q-001 bleiben für die öffentliche Distribution offen. Beim
Wiederaufnehmen stimmten Archiv, Binary, Netz und Lizenzdateien mit den
vorhandenen SHA-256-Werten überein. Die Release-Metadaten nennen denselben
Archivdigest. Das vorhandene Archiv wurde weiterverwendet.

## Reale UCI- und Spielprüfung

`reports/uci-direct.log` erfasst alle beworbenen Optionen und `uciok` /
`readyok`. Unter anderem bietet die Version Threads 1–1024, Hash
1–33.554.432 MiB, Skill Level 0–20, MultiPV 1–256, UCI_Elo 1320–3190
und UCI_LimitStrength (Standard false). Diese Bereiche sind Angaben
der Engine. Abnahme und Benchmark nutzen kleine Budgets.

`reports/run-offline.sh` startet den bestehenden Adaptertest unter macOS
`sandbox-exec` mit `(deny network*)`. Der Test prüft den Netzblock per
Socket. Die Phase `uci` prüfte reale Zugfolgen, Startposition, FEN,
`ucinewgame`, Movetime, Fischer-Parameter, MultiPV, Abbruch, Timeout und
Quit. Der Adapter verwarf eine unbekannte und eine ungültige Option.
An isolierten Kopien verweigerte die Registry fehlende oder veränderte
Ressourcen sowie eine fehlende oder veränderte Binary. Nach Rückkehr der
identischen Binary war die Engine wieder bereit. Die wieder geöffnete
Registry lieferte denselben Fingerabdruck und dieselben Ressourcenhashes.
Alle 19 Optionen stehen in `reports/resume/registry-and-scores.json`. Die
erneute UCI-Prüfung auf einer isolierten Registry-Kopie endete mit Exitcode
0. Ihr Transkript steht in `reports/resume/uci-commands.json`. Sie ersetzt
den früheren Importfehler des Prüfskripts in `reports/uci.err`.
`reports/resume/verify_process_abort.py` beendete einen eigenen
Stockfish-Prozess mitten in der Suche. Der Adapter meldete einen
Protokollfehler und räumte den aktiven Suchzustand auf. Der Neustart
über dieselbe freigegebene Konfiguration lieferte einen legalen Zug.
`reports/resume/process-abort.log` hält den Befund fest (Exitcode 0).
Die Phase `play` prüfte beide Menschenfarben, Uhr und Fischer-Inkrement,
Uhrpause, Undo/Redo, Autosave, Neustart, archivierte Engine-Metadaten und
eine Partie aus eigener FEN. Jeder gespielte Zug wurde im Regelkern geprüft.
`verify_engine_switch.py` entfernte eine reale Registrierung im Testprofil.
Nach Ablehnung blieb die alte Herkunft bestehen. Nach Bestätigung spielte
Stockfish mit der neuen freigegebenen Registrierung weiter. Der Wechsel
wurde aufgezeichnet. Die Partie Mensch gegen Stockfish aus eigener FEN
endete mit Matt. Stockfish gegen Stockfish lief über den vorgesehenen
Headless-Runner. Die Desktop-App bietet Mensch gegen Bot als Spielmodus.

## Analyse und Lernkreislauf

Bei Realanalysen kann Stockfish am Zeitlimit nach einer exakten Bewertung
einen gebundenen Wert aus einem tieferen Suchlauf melden. Die
Stellungsvergleiche erhalten jetzt den tiefsten exakten Wert. Liegt nur
eine Grenze vor, bleibt sie erhalten. Der Cache-Schlüssel für
Stellungsvergleiche wurde angepasst. Der Fixture-Regressionstest sendet
gezielt eine tiefere obere Grenze nach einem exakten Wert.

In der Bot-Partie wurde das erlaubte Matt als kritischer Moment erkannt.
Partieanalyse und Einzelstellung lieferten MultiPV; Centipawn und Matt
wurden nach Perspektive ausgewertet. Die ergänzende Einzelstellungsprobe
lieferte aus der Startstellung +25 cp für Weiß und −25 cp für Schwarz.
Bei Schwarz am Zug in der Mattstellung ergab sie Matt −1 für Weiß und
+1 für Schwarz. Alle sechs MultiPV-Linien dieser beiden Proben wurden Zug
für Zug im Chess-Core nachgespielt. Der Analyseabbruch sendete `stop`.
Die erneute Partieanalyse in einem neuen Python-Prozess benötigte
**0 statt 4 UCI-Suchen**; zwei aktive Positionen kamen aus dem persistenten
Cache. Der resultierende Kandidat war nach Neustart und Restore in der
App verfügbar. Fortschritt und Engine-Freigabe blieben erhalten.
`learning-first.json` und `learning-restart.json` enthalten die Befehlsfolgen
und Prüfergebnisse.

Der vorhandene CC0-Katalog enthält 20.000 eindeutige Aufgaben mit Ratings
1000–3330, darunter 700 ab 3000. Der kanonische JSONL-Hash lautet
`2ebc99d811d159e42a39ae33acb280c2e6a410826d9c67f24386924343b338a6`,
der Indexhash
`eacede1d861a23ab06035fbcc58c7ad60e7ce34b485329d93dc38a395379d0e2`.
Die geschichtete Stichprobe umfasste 12 Aufgaben (zwei je Ratingband).
Alle vollständigen Züge waren legal. Die erwartete erste Lösung war
bei 11 Aufgaben der erste Stockfish-Zug und einmal unter den ersten drei.
Suchlimit 120 ms, MultiPV 3. Diese Stichprobe bewertet den ersten Lösungszug
und trifft keine Aussage über die Eindeutigkeit vollständiger Varianten.
Der ursprüngliche JSONL- und Indexhash wurden vor und nach der Probe
geprüft. Der native Offline-Lauf prüfte Filter, Versuche, Hinweise,
Fälligkeit, Neustart und Restore mit vorhandenem und fehlendem Katalog.

## Begrenzter Benchmark

`scripts/benchmark_engines.py` verglich benachbarte Stufen 1–6 paarweise
mit Farbtausch an zwei Startstellungen. Seed 17, 8.000 Knoten pro Zug,
8 Halbzüge und höchstens 8 s pro Partie. 20 Partien und 160 Halbzüge
ohne technische Verluste. Alle Partien erreichten das Halbzuglimit.
Die summierte Partiedauer betrug 6,307 s. Skill 0/3/6/10/15/20,
1–2 Threads, 16–128 MiB Hash. UCI_LimitStrength und UCI_Elo waren
im Handshake verfügbar. Die Presets nutzten Skill Level. Der JSON-Wert `version: null` folgt aus
dem fehlenden separaten UCI-Feld `id version`. Name und Binary-Hash
identifizieren den Lauf als Stockfish 19. Die Startstellungen waren
Standard und die Stellung nach `1. e4 e5`. Die effektiven Optionen pro
Preset stehen in den JSON-Nachweisen. Für alle galt das genehmigte
`EvalFile`. `UCI_LimitStrength` blieb auf dem Standardwert `false`.

Die Wiederaufnahme begrenzte sich auf höchstens acht weitere Partien
mit Farbtausch, 8.000 Knoten pro Suche, vier Halbzügen und acht Sekunden
je Partie. Die Zeitmessung umfasste den UCI-Suchaufruf einschließlich
der Kommunikation mit dem lokalen Prozess. Engine-Start und
Brettvalidierung liegen außerhalb dieser Einzelzugmessung.

| Presets | Stellung | Halbzüge | Minimum / Median / Maximum je Suche | Ergebnis |
| --- | --- | ---: | --- | --- |
| 1 / 2 | Standard | 8 | 4,48 / 5,63 / 6,95 ms | 2 Halbzuglimits |
| 3 / 4 | Standard | 8 | 5,30 / 5,95 / 6,58 ms | 2 Halbzuglimits |
| 5 / 6 | Standard | 8 | 2,25 / 3,55 / 4,83 ms | 2 Halbzuglimits |
| 5 / 6 | Nach `1. f3 e5 2. g4` | 2 | 0,96 / 2,35 / 3,73 ms | 2 schwarze Matts durch `d8h4` |

Der Zusatzlauf endete mit Exitcode 0, ohne technische Verluste oder
Abbrüche. `reports/resume/timed-1.json` bis `timed-4.json` enthalten die
26 Einzelzugzeiten, Farbzuordnung, Optionen und Ergebnisdetails. Daneben
liegen die PGN-Dateien. Beide Läufe prüfen die technische Einsatzfähigkeit.
Suchzeiten und kurze Partien erlauben weder eine Spielstärkerangfolge
noch eine Elo-Zuordnung. Q-023 bleibt offen.

## Reproduktion der ergänzenden Real-Engine-Prüfung

Im separaten IV-A-Clone ausführen. Das Stockfish-Artefakt bleibt an seinem
bestehenden Pfad. Das Skript erzeugt eine temporäre Registry, verweigert
den Start bei fehlender Binary-Kopie, prüft beide Perspektiven und nutzt
den bestehenden JSON-/PGN-Benchmark. Es prüft die Netzsperre per Socket.

```sh
iva="$HOME/.local/share/chess-and-chains-iv-a/2026-11-28/stockfish-19"
PYTHONPATH="src:.:$iva/reports" PYTHONWARNINGS=error::ResourceWarning \
  sandbox-exec -p '(version 1) (allow default) (deny network*)' \
  python3 "$iva/reports/resume/verify_supplement.py" "$iva"
```

Die ergänzende Adapterprüfung verwendet denselben Sandbox- und
`PYTHONPATH=src:.`-Aufruf für
`reports/verify_stockfish.py <isolierte-IV-A-Ablage> <IV-B-Ablage> uci`.
Die isolierte Ablage benötigt eine SQLite-Kopie der Lernprofil-Registry
unter `test-profile/learning/engine_registry.sqlite3`, die vorhandene
`provenance/engine-id.txt` und einen leeren `reports/`-Ordner. Die
Phase legt selbst das Unterverzeichnis `test-profile/approval/` an.

## Abschließende QA

Die lokale Regression lief auf `f06d8b70ddc725055dd7c6890783c438694396a9`
mit macOS 27.2.1 (26B131), arm64 und Python 3.14.5. Die Wiederaufnahme
ergänzt Dokumentation und separate lokale Prüfartefakte. Der getestete
Anwendungsdiff stammt aus `823fb3c`. Für die App- und QA-Aufrufe wurde
`CHESS_AND_CHAINS_DATA_DIR` auf ein temporäres Profil gesetzt.

| Prüfkommando | Ergebnis | Exitcode |
| --- | --- | ---: |
| `python3 scripts/ci_tests.py inventory` | 487 Tests erfasst und den Runnern zugeordnet | 0 |
| `python3 scripts/ci_tests.py headless` | 316 Tests, einschließlich Branding, Storage und Recovery | 0 |
| `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1 python3 scripts/ci_tests.py gui` | 160 native Tk-Tests, einschließlich Branding und Restore | 0 |
| `python3 scripts/ci_tests.py pytest` | 11 Figurensatztests | 0 |
| `PYTHONPATH=src python3 -m glide_shell.selftest` und `PYTHONPATH=src python3 -O -m glide_shell.selftest` | je 13/13 | 0 |
| `python3 scripts/verify_starter.py`, `python3 scripts/verify_document_links.py`, `python3 scripts/check_policy.py` | Struktur, Links und Policy geprüft | 0 |
| `python3 -m compileall -q src app scripts tests` | Python-Quellen kompiliert | 0 |
| `PYTHONPATH=src python3 -m chess_and_chains --version` und `--headless-check` | V.0.3.0 und Headless-Startcheck | 0 |

Ausgaben und Exitcodes liegen unter `reports/resume/qa-*.log`. Der
Main-Lauf wurde zusätzlich mit `gh run view 46107871105` auf Commit und
14 erfolgreiche Jobs geprüft.

Die automatisierten UCI-Tests verwenden Fixtures. Die vorstehenden
Offline-Protokolle weisen davon unabhängig Stockfish 19 nach.
Die Main-CI mit 14/14 Jobs auf dem Merge-Commit vor IV-A deckt Headless
auf macOS, Windows und Linux sowie native Tk-Tests auf macOS/Windows
und Linux unter Xvfb ab, jeweils für Python 3.11 und 3.14. Der
IV-A-Branch hat lokale native macOS-Nachweise. Native Stockfish-Läufe auf
Windows, Intel-Mac und Linux sowie Installer-Tests sind ausstehend.
Glide Shell, Workflow-Dateien, UI, Design und Assets haben gegenüber
dem Main-Commit keinen Diff.

## Übergabe V · Connected Learning (F19–F21)

1. Im separaten Clone am lokalen IV-A-Branch ansetzen. Die
   Analysekorrektur `823fb3c` und die dokumentierte Baseline
   `13b27f65` beim Abgleich mit Main berücksichtigen. Den Stand
   nach `docs/governance/AGENT_HANDOFF_TEMPLATE.md` erfassen.
2. **F19:** `AnalysisTrainingCandidate`,
   `Database.save_analysis_training_candidate` und
   `Database.analysis_training_candidates` als Ausgangspunkt verwenden.
   Die freie Übung bleibt verfügbar. Für bewertete persönliche Rätsel
   Lösungsregel, Herkunft und Namensraum festlegen. Deduplizierung,
   Legalität und Verfügbarkeit nach Löschen der Quellpartie,
   Neustart und Restore prüfen.
3. **F20:** `TrainingCheckpoint`, `ActivePuzzleCheckpoint` sowie
   `Database.save_training_checkpoint` und `load_training_checkpoint`
   für mehrere verknüpfte Ketten weiterverwenden. Wiederaufnahme,
   transaktionale Speicherung, Pack-Namensräume und kontrollierte Anzeige
   bei fehlendem Pack prüfen.
4. **F21:** Auf `Database.record_puzzle_attempt`, `puzzle_progress`,
   `latest_puzzle_attempt` und `due_puzzle_ids` aufbauen. Themen- und
   Langzeitverlauf mit vorhandenen Pack-IDs abgleichen. Zeitzone,
   Mehrfachversuche, Fälligkeit, Neustart und Backup/Restore mit
   vorhandenem sowie vorübergehend fehlendem Pack abnehmen.
5. **Abnahme:** Das bestehende IV-B-Pack samt validiertem Index in ein
   frisches Testprofil kopieren. Die bestehende Stockfish-Registry und
   den lokalen Netzblock verwenden. `play` und `restart` in separaten
   Prozessen ausführen. Die Phasen brauchen zu Beginn einen frischen
   Cache und dieselbe Registry sowie dasselbe Profil zwischen den
   Prozessen. Aus `learning-first.json` und `learning-restart.json`
   lassen sich Suchzählung, Kandidaten-ID und Katalogwerte vergleichen.
   Fixture-, Native-GUI- und Realdatennachweise getrennt protokollieren.

Q-001/ADR-001, Q-021 und Q-023 sind weiterhin Owner-Entscheidungen.
Q-022 deckt die lokale Verwendung des Katalogs ab. Der Rückweg bei
Problemen mit dem Analyse-Fix ist ein gezielter Revert von `823fb3c`.
Er betrifft den Vergleichscache-Schlüssel und den dazugehörigen Test.
Das Profil- und Archivschema wurde in IV-A nicht migriert.

Die IV-A-Ergänzungen wurden mit KI-Unterstützung erstellt.
