# Rätselpakete lokal erzeugen

Der Offline-Builder liest lokale CSV-Dateien im Lichess-Layout. Python ab
3.14 unterstützt im Builder auch `.csv.zst`. Aus der projekteigenen
[Demo-CSV](../source/demo_puzzles.csv) entstand die mitgelieferte
Paketversion 2. Ein produktiver Datensatz steht zur Prüfung nach
Owner-Opt-in Q-022 aus. [ADR-003](../../docs/decisions/ADR-003_PUZZLE_POLICY.md)

Beispiel mit den [projekteigenen Testdaten](../../tests/fixtures/puzzles_sample.csv).
Ein absolutes temporäres Ziel hält das Prüfartefakt außerhalb des Repos.

```powershell
python scripts/build_puzzle_pack.py tests/fixtures/puzzles_sample.csv "$env:TEMP/chess-chains-fixture-pack" --pack-id fixture-only --version 1 --source "Project fixtures" --license "MPL-2.0" --max-rating-deviation 80 --min-popularity 90 --min-plays 100
```

| Option | Auswahlkriterium |
| --- | --- |
| `--min-rating` und `--max-rating` | Inklusive Grenzen für das Puzzle-Rating. Die Untergrenze beträgt mindestens 1000. |
| `--max-rating-deviation` | Höchste zugelassene Ratingabweichung, ab 0. |
| `--min-popularity` | Niedrigste zugelassene Popularität von −100 bis 100. |
| `--min-plays` | Geringste zugelassene Anzahl bisheriger Versuche, ab 0. |

Die drei Qualitätsgrenzen sind optional. Alle angegebenen Grenzen müssen
erfüllt sein. Fehlt ein dafür benötigter Wert, weist der Import diese Zeile
als `missing_quality_value` aus. Die Beispielwerte gelten für die Testdatei.
Qualitätsgrenzen für künftige Produktpakete folgen
dem Datenprofil und der Entscheidung des Inhabers.

Das Paket enthält `puzzles.jsonl`, `manifest.json` und beim Builder
zusätzlich `import_report.json`. `--source` steht im Manifest und pro
Aufgabe. Der Bericht nennt die Grenzwerte, gelesene und akzeptierte Zeilen
sowie einen Ausschlussgrund pro abgelehnter Zeile. Sein SHA-256 bezieht
sich auf die CSV-Bytes nach einer eventuellen Dekompression. Endet der
Import am `--limit`, kennzeichnet der Bericht den vorzeitigen Abbruch.
Dann enthält er keine Prüfsumme für die gesamte Quelle. Das Manifest
enthält separat die Prüfsumme der erzeugten JSONL-Datei.
