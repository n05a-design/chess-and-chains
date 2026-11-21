# Rätselpakete lokal erzeugen

## In der App verwenden

Im Puzzle Lab **Rätselpakete… → Paketordner importieren…** wählen und den
Ordner mit `manifest.json` und `puzzles.jsonl` angeben. Die App prüft
Prüfsumme, Paketkennung, Rating und spielbare Zugfolgen im Hintergrund.
Anschließend speichert sie beide Dateien unter
`puzzle_packs/<pack_id>` im [Nutzerdatenordner](../../docs/architecture/DATA_CONTRACTS.md)
und öffnet das Paket.

Über dieselbe Auswahl lässt sich zwischen installierten Paketen und der
mitgelieferten Demo wechseln. Die App öffnet beim Neustart die letzte
Auswahl und speichert Fortschritt je Paket. Bei einem nicht verfügbaren
Paket bleibt die Demo nutzbar. Ein Import mit bereits installierter oder
reservierter Kennung meldet einen Fehler. Installierte Daten und der
Quellordner bleiben dabei erhalten.

Der Desktop-Import liest bis zu 64 KiB Manifest und 64 MiB Rätseldaten.
Die optionale Prüfdatei `import_report.json` bleibt im Build-Ordner.

## Offline-Builder

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
| `--limit` | Höchstens so viele Rätsel in das Paket übernehmen. |
| `--seed` | Ganzzahliger Seed für eine reproduzierbare Auswahl aus der gesamten Quelle. Erfordert ein positives `--limit`. |

Die drei Qualitätsgrenzen sind optional. Alle angegebenen Grenzen müssen
erfüllt sein. Fehlt ein dafür benötigter Wert, weist der Import diese Zeile
als `missing_quality_value` aus. Die Beispielwerte gelten für die Testdatei.
Qualitätsgrenzen für künftige Produktpakete folgen
dem Datenprofil und der Entscheidung des Inhabers.

Das Paket enthält `puzzles.jsonl`, `manifest.json` und beim Builder
zusätzlich `import_report.json`. `--source` steht im Manifest und pro
Aufgabe. Der Bericht nennt die Grenzwerte, gelesene und akzeptierte Zeilen
sowie einen Ausschlussgrund pro abgelehnter Zeile. Sein SHA-256 bezieht
sich auf die CSV-Bytes nach einer eventuellen Dekompression. Das Manifest
enthält separat die Prüfsumme der erzeugten JSONL-Datei.

Fehlerhafte UTF-8-Bytes in einem Datensatz führen zu `unreadable_row`.
Die gültigen Datensätze davor und danach bleiben im Import. Ein
fehlerhafter Header bricht den Import vor der Paketerstellung ab.

## Auswahl mit Seed

Der folgende Aufruf erzeugt aus den projekteigenen Demo-Daten eine
Stichprobe mit bis zu zwei Rätseln im temporären Verzeichnis.

```powershell
python scripts/build_puzzle_pack.py data/source/demo_puzzles.csv "$env:TEMP/chess-chains-seed-pack" --pack-id seed-fixture --version 1 --source "Project fixtures" --license "MPL-2.0" --limit 2 --seed 17
```

Mit Seed liest der Importer die ganze Quelle. Er berechnet für jede
zulässige Kennung den SHA-256-Rang von `seed:id` und übernimmt die
kleinsten Ränge. Dieselben gültigen, eindeutigen Datensätze, Filter und
Parameter ergeben dieselbe Reihenfolge und bytegleiche JSONL-Daten.
Die Auswahl hält höchstens `--limit` Rätsel im Speicher. Für die
Duplikatprüfung merkt sich der Importer weiterhin die gelesenen IDs.
Manifest und Bericht führen Zeitstempel des jeweiligen Laufs.

In `selection` zeichnet der Bericht Strategie, Seed, Limit und
Stichprobengröße auf. `accepted` zählt alle passenden, validierten Zeilen.
Ohne Seed nimmt der Builder Aufgaben in Quellreihenfolge und stoppt beim
gesetzten Limit. In diesem Fall kennzeichnet der Bericht den vorzeitigen
Abbruch und enthält keine Prüfsumme für die gesamte Quelle.
