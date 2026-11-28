# Integrationsgate III / IV-B

## Git-Abgleich

GitHub-`main` steht auf `6dcd12f187d19a878a6ad0ae81de37c251c00991`.
Der Merge-Workflow von PR #26 war mit 14 erfolgreichen Jobs abgeschlossen.
Beide Entwicklungsworktrees waren sauber. Der OneDrive-Checkout enthielt
die lokale Affinity-Datei und drei SVG-Dateien mit eigenen Namen. Dieser
Checkout blieb unberührt. [Referenz-CI](https://github.com/n05a-design/chess-and-chains/actions/runs/46084335806)

`git merge-base a7cd330 72766a7` lieferte `a7cd330`.
`git rev-list --left-right --count a7cd330...72766a7` lieferte `0 2`.
Somit enthält `72766a7ba3ace990ffb921d0f2a7a3e1cd6d88b0` alle acht
Commits von Auftrag III und die zwei Folgecommits aus IV-B. Der separate
Worktree `/Users/shaye/.codex/worktrees/chess-and-chains-integration-iii-ivb`
und der Branch `codex/integration-iii-ivb` übernehmen diese Historie
linear. Die beiden Ausgangsbranches behalten ihre Standpunkte.
Geplant ist ein gemeinsamer PR des Integrationsbranches gegen `main`.

Vorbereitung der Review-Unterlagen und Abnahme erfolgten lokal. Die Daten
und Rohdateien bleiben außerhalb von Git und OneDrive. Der Diff wurde
gegen `main` geprüft. Glide Shell, Logo-Master, Figurensätze, Version und
Workflow-Matrix entsprechen dem Ausgangsstand.

## Konsolidierte Prüfungen

Erneute Ausführung auf dem gemeinsamen Produktstand `72766a7` im neuen
Integrationsworktree, macOS arm64 27.2.1 (26B131), Python 3.14.5,
SQLite 3.50.4 und Tk 9.0. Der zusätzliche gemeinsame Ablauf ist separat
nachgewiesen. Er erstellt nur ein kurzlebiges isoliertes Profil.
Die Originaldaten des bestehenden Testprofils wurden für den
Nachweis lesend geöffnet.

| Befehl | Beobachtung |
| --- | --- |
| `PYTHONPATH=src python3 scripts/ci_tests.py inventory` | 487 Tests erfasst, Exit 0 |
| `PYTHONPATH=src python3 scripts/ci_tests.py headless` | 316 bestanden, 74,20 s, Exit 0 |
| `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1 PYTHONPATH=src python3 scripts/ci_tests.py gui` | 160 bestanden, 89,07 s, Exit 0 |
| `PYTHONPATH=src python3 scripts/ci_tests.py pytest` | 11 Figurensatztests bestanden, Exit 0 |
| `python3 -B scripts/build_brand_assets.py --check` | 41 geprüfte Ausgaben, Exit 0 |
| `python3 scripts/verify_starter.py`, `verify_document_links.py`, `check_policy.py` | Je Exit 0 |
| `PYTHONPATH=src python3 -m glide_shell.selftest` sowie `python3 -O -m glide_shell.selftest` | Je 13/13, Exit 0 |
| `python3 -m compileall -q src app scripts tests`, CLI-Version und Headless-Einstieg | Je Exit 0 |
| Gemeinsamer Offline-Ablauf mit lokalem Katalog und UCI-Fixture | Exit 0 |

Die Headless-Suite prüfte alle Migrationen v1–v7 nach v8, ältere
SQLite-Sicherungen, ZIP-Kompatibilität, fehlerhafte Daten und den Abbruch
während Restore oder Journal-Rücksetzung. Die nativen Tests prüften
unter anderem zeitgesteuerte Partiewiederaufnahme, Sichtbarkeit
historischer Uhrstände und bestätigte Gegnersubstitution.
Die GitHub-Matrix für Windows, macOS und Linux mit Python 3.11 und 3.14
bleibt erhalten. Ein Lauf auf dem Integrationsbranch steht aus.

## Offline-Ablauf und Datenprovenienz

Bei gesperrtem Netzwerk lud der gemeinsame Prozess ein bereits geprüftes
Registry-Profil neu, analysierte eine Partie in drei Positionen und
startete anschließend den Analysedienst erneut. Die Protokoll-Fixture
registrierte insgesamt drei reguläre Suchbefehle und vier begrenzte
`searchmoves`-Befehle. Der zweite Dienst bediente alle drei Positionen
aus dem Cache. Der daraus gespeicherte Kandidat blieb nach Löschen der
Quellpartie und des Quellberichts für freies Training abrufbar. Im selben
Profil wurden reale Puzzle-Lab-Filter, Hinweise, Versuche, Wiederholungen
und die Rücksicherung geprüft. Der Kandidat ließ sich anschließend in
der Desktop-App öffnen. Das Backup meldete beim Einspielen in ein
Ziel ohne Katalog die fehlende Paketreferenz und erhielt die Lernversuche.

Der gültige Index öffnete in 13,44 ms. Aus den vorhandenen Daten wurden
20.000 Rätsel und 20.000 eindeutige IDs bei Rating 1000–3330 bestätigt.
700 Aufgaben haben Rating mindestens 3000. Das ursprüngliche
Testprofil enthielt drei persistierte Versuche zu zwei Rätseln und einen
sauberen Abschluss. Seine Datenbank-Prüfsumme blieb unverändert.
Das Gate überprüfte die vorhandene Reproduktionsaufzeichnung aus dem
unabhängigen IV-B-Zweitbuild sowie die tatsächlichen Paketbytes.
Es verwendete die vorhandene lokale Quelle für die Prüfsumme.

| Bestandteil | SHA-256 |
| --- | --- |
| Komprimierter Originalexport | `7b0d235fa40cfd7fdb7df1fec56a96b3b6ee1496b32ed2eb05be90d0ebf94253` |
| Reproduzierter und installierter JSONL-Payload | `2ebc99d811d159e42a39ae33acb280c2e6a410826d9c67f24386924343b338a6` |
| Vorhandener SQLite-Katalog | `eacede1d861a23ab06035fbcc58c7ad60e7ce34b485329d93dc38a395379d0e2` |

- Downloadarchiv und Reproduktionsprotokoll liegen in
  `/Users/shaye/.local/share/chess-and-chains-iv-b/2026-11-28`.
- Produktpack und vollständiges Importprofil liegen darin unter
  `lichess-core-20k`.
- Das nutzbare Testprofil liegt darin unter `test-profile`.
  Der Index liegt im Profil unter `puzzle_packs-catalogs/lichess-core-20k`.
- Protokolle und vorbereitete PR-Unterlagen liegen separat in
  `/Users/shaye/.local/share/chess-and-chains-integration-gate/2026-11-28`.
- Q-022 ist erteilt und lokal umgesetzt. Die öffentliche Distribution
  ist ausdrücklich nicht freigegeben.
  [Q-022](../questions/OPEN_QUESTIONS.md) · [Vollständige IV-B-Provenienz](2026-11-28_W08-IV-B-lichess-produktdaten.md)

```bash
IVB_DATA=/Users/shaye/.local/share/chess-and-chains-iv-b/2026-11-28
CHESS_AND_CHAINS_REQUIRE_DISPLAY=1 PYTHONPATH=src \
  sandbox-exec -p '(version 1) (allow default) (deny network*)' \
  python3 scripts/verify_integration_gate.py "$IVB_DATA"
```

## Übergabe

### IV-A – Stockfish Integration & Compliance

- Die gemeinsame Engine-Grenze besteht aus `EngineRegistry`,
  `EngineConfig`, dem vor Start erneut geprüften Freigabebeleg und
  `UCIEngine`. Spiel, Archiv-Referenz, Analyse und Benchmark verwenden
  dieselbe registrierte Identität.
- Den Fixture-Referenzlauf mit
  `python3 scripts/benchmark_engines.py --smoke --max-plies 4 --nodes 128`
  ausführen. Für eine freigegebene reale Engine Binary- und
  Ressourcenherkunft, Version, Prüfsummen, wirksame Optionen und
  Zielplattformen separat nachweisen. Q-001, Q-002, Q-023 und ADR-001
  gelten für Auslieferung, Offline-Bot und Kalibrierung.
- [Engine-Vertrag](../architecture/UCI_CONTRACT.md) · [III-Prüfnachweis](2026-11-28_phase-a-completion-phase-b-engine-analysis.md)

### V – Connected Learning, F19–F21

- Das bestehende Produktpack über `PackLibrary.open_catalog("lichess-core-20k")`
  im lokalen Profil verwenden. Realdaten laufen über den geprüften
  Index, ohne einen erneuten Download. Übungen über die stabile
  Kombination aus Pack-ID und Rätsel-ID mit dem Versuchsspeicher
  verbinden.
- `Database.analysis_training_candidates()` liefert eigenständige
  Kandidaten aus Analysen. Ihre Legalitätsprüfung und Provenienz
  stehen zur Verfügung. Bewerten, Kuratieren und Einreihen in
  mehrere fortsetzbare Lernketten gehören in den Auftrag V.
- `Database.puzzle_training_ids()` und `due_puzzle_ids()` bilden
  Review und Fälligkeit ab. Themenschwerpunkte aus echten Versuchen
  ableiten. Die gewählten Ratingquoten eignen sich für
  Trainingsabdeckung. Für Aussagen über die Häufigkeit im
  Originalexport die dokumentierte Quellverteilung verwenden.
