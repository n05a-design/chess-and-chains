# IV-A · Stockfish 19 und lokale Abnahme

## Basis und Ablage

PR #27 wurde als `13b27f659f5c6b7cb24c156653bb316dc6c6adf7` gemergt.
[Main-CI](https://github.com/n05a-design/chess-and-chains/actions/runs/46107871105)
bestand mit 14/14 Jobs auf macOS, Windows und Linux. Die Prüfung von IV-A
erfolgte auf macOS 27.2.1, Apple M2, Python 3.14.5. Der Branch
`codex/stockfish-iv-a` liegt im frischen Clone
`/Users/shaye/.codex/worktrees/chess-and-chains-iv-a-clean`.
Der frühere OneDrive-Worktree blieb beim Wechsel unberührt. In seiner
Git-Historie fehlten nach dem Umbenennen weiterhin elf Objekte.

Lokale Ablage `/Users/shaye/.local/share/chess-and-chains-iv-a/2026-11-28/stockfish-19`.
Unter `binary/` liegen `stockfish` und `exported.nnue`, unter `test-profile/learning/`
das isolierte SQLite-v8-Profil und die lokale UCI-Registry. `reports/` enthält
die Prüfskripte und Ergebnisse, `benchmarks/` die JSON- und PGN-Nachweise.
Der Katalog verweilt unter
`/Users/shaye/.local/share/chess-and-chains-iv-b/2026-11-28/lichess-core-20k`.
Die QA verwendet eine Kopie des vorhandenen Index und des Pakets.

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
und Q-001 bleiben für die öffentliche Distribution offen.

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
Ressourcen und ein geändertes Binary. Befehlsfolge in `uci-commands.json`.
Die Phase `play` prüfte beide Menschenfarben, Uhr und Fischer-Inkrement,
Uhrpause, Undo/Redo, Autosave, Neustart, archivierte Engine-Metadaten und
eine Partie aus eigener FEN. Jeder gespielte Zug wurde im Regelkern geprüft.
`verify_engine_switch.py` entfernte eine reale Registrierung im Testprofil.
Nach Ablehnung blieb die alte Herkunft bestehen. Nach Bestätigung spielte
Stockfish mit der neuen freigegebenen Registrierung weiter. Der Wechsel
wurde aufgezeichnet.

## Analyse und Lernkreislauf

Bei Realanalysen kann Stockfish am Zeitlimit nach einer exakten Bewertung
einen gebundenen Wert aus einem tieferen Suchlauf melden. Die
Stellungsvergleiche erhalten jetzt den tiefsten exakten Wert. Liegt nur
eine Grenze vor, bleibt sie erhalten. Der Cache-Schlüssel für
Stellungsvergleiche wurde angepasst. Der Fixture-Regressionstest sendet
gezielt eine tiefere obere Grenze nach einem exakten Wert.

In der Bot-Partie wurde das erlaubte Matt als kritischer Moment erkannt.
Partieanalyse und Einzelstellung lieferten MultiPV; Centipawn und Matt
wurden nach Perspektive ausgewertet. Der Analyseabbruch sendete `stop`.
Die erneute Partieanalyse in einem neuen Python-Prozess benötigte
**0 statt 4 UCI-Suchen**; zwei aktive Positionen kamen aus dem persistenten
Cache. Der resultierende Kandidat war nach Neustart und Restore in der
App verfügbar. Fortschritt und Engine-Freigabe blieben erhalten.
`learning-first.json` und `learning-restart.json` enthalten die Befehlsfolgen
und Prüfergebnisse.

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
im Handshake verfügbar. Die Presets nutzten Skill Level. Q-023 bleibt
offen. Dieser Lauf liefert keine belastbaren Spielstärkerangfolgen.

## Regression

Auf dem endgültigen Anwendungsdiff bestanden `scripts/ci_tests.py headless`
mit 316 Tests, `gui` mit 160 nativen Tests und `pytest` mit 11 Tests.
Beide Glide-Selbsttests (normal und optimiert) meldeten 13/13.
Alle vier Runner-Befehle `inventory`, `headless`, `gui` und `pytest`
sowie die beiden realen Lernphasen wurden lokal ausgeführt.
Die GitHub-Matrix bezieht sich auf den Merge-Commit vor dem lokalen IV-A-Fix.

## Übergabe V · F19–F21

1. F19 verwendet `AnalysisTrainingCandidate` und die fortbestehende
   Inhaltsidentität. Den Übergang von freier Übung zu bewerteter persönlicher
   Aufgabe separat definieren und die Herkunft nach Löschen der Quelle testen.
2. F20 verwendet den existierenden Checkpoint-Vertrag. Verkettung mit
   Katalog-IDs, Unterbrechung, Wiederaufnahme und fehlendes Pack prüfen.
3. F21 baut auf persistenten Versuchen, Fälligkeit und Review auf.
   Themenhistorie mit bestehenden Pack-Namensräumen und Backup testen.
4. Realdatenprüfung mit dem bestehenden Katalog und der Engine-Registry
   im separaten Profil wiederholen. Die Phasen `play` und `restart`
   des lokalen Prüfskripts benötigen einen frischen Testcache für die
   Messung der vermiedenen Suchen. Produktivprofile bleiben unberührt.

Die realen Stockfish-Läufe gelten für Apple Silicon. Die Main-CI prüft
den plattformübergreifenden Anwendungsvertrag per Fixture. Native
Stockfish-Abnahme auf Windows und Linux sowie Installer und Vertrieb
bleiben offen.
