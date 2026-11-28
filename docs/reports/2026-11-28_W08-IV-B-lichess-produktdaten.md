# IV-B – Lichess-Produktdaten, Katalog und Offline-Abnahme

## Repository und Freigabe

Q-022 wurde am 28.11.2026 durch den Inhaber für den lokalen IV-B-Auftrag
freigegeben. Der Scope erfasst Download, Profilierung, lokale Verarbeitung,
Paketbau und isolierte Abnahme. Veröffentlichungs-, Release- und
Engine-Freigaben sind eigenständige Entscheidungen. [Q-022](../questions/OPEN_QUESTIONS.md)

`origin/main` stand beim Abgleich auf `6dcd12f187d19a878a6ad0ae81de37c251c00991`.
Der Merge-Lauf für PR #26 meldete 14 erfolgreiche Jobs. IV-B verwendet den
neueren lokalen Stand von Auftrag III bei `a7cd330` in einem separaten
Worktree auf `codex/lichess-product-data`. Dieser Stand wurde in Auftrag III
lokal geprüft. [Merge-CI](https://github.com/n05a-design/chess-and-chains/actions/runs/46084335806)

## Quellprovenienz

- Offizielle Lichess Open Database, CC0 1.0 Universal. Die Anbieterseite
  nennt 6.193.530 Rätsel und den 11.11.2026 als Stand. Die heruntergeladene
  CSV hat dieselbe Zeilenzahl. [Lichess-Puzzledaten](https://database.lichess.org/#puzzles)
- Download am 28.11.2026 über den offiziellen Dateilink, HTTP 200,
  309.751.173 Byte, 31,94 Sekunden. Der HTTP-Dateizeitstempel war
  `2026-11-01T07:57:40Z`, ETag `"6ae6f0f4-12766d85"`. Beide
  Angaben wurden als separate Herkunftsmerkmale festgehalten.
  [Originalexport](https://database.lichess.org/lichess_db_puzzle.csv.zst)
- Komprimierte SHA-256
  `7b0d235fa40cfd7fdb7df1fec56a96b3b6ee1496b32ed2eb05be90d0ebf94253`.
  Die Prüfsumme wurde vor dem Build lokal berechnet. `zstd -t`
  endete mit Exit 0 und meldete 1.177.486.537 entpackte Byte.
- Der lokale Datenträger hatte vor dem Download 57 GiB freien Platz.

## Auswahl und Datenqualität

Der gesamte Zstandard-Stream wurde ohne entpackte Zwischendatei gelesen.
Eine temporäre SQLite-Tabelle prüfte Quell-IDs exakt. Die Vorauswahl
hielt höchstens das Doppelte der Zielquote je Band im Speicher.
Der Builder verwendet SHA-256 über `Seed:PuzzleId` mit Seed `20261128`.
Kandidaten ab Rating 1000 müssen Popularität ≥ 60, Ratingabweichung ≤ 125,
mindestens 10 Versuche sowie die benötigten Positionsmetadaten haben.
Jeder berücksichtigte Kandidat wird im bestehenden Schachkern geprüft.
Die erste UCI-Aktion ist der Aufbauzug des Gegners. Doppelte spielbare
Stellungen mit gleicher Lösungsfolge werden innerhalb der Auswahl
ausgeschlossen. Zählerstände der FEN bilden dabei keinen Unterschied.

Die Schicht ab 3000 umfasst 1.555 nach Metadatenfilter verfügbare Zeilen.
Die Produktquote gewichtet höhere Ratingbereiche bewusst stärker als
der vollständige Export. Die Auswahl deckt Schwierigkeitsstufen ab.
Sie beschreibt keine repräsentative Stichprobe für statistische Aussagen
über den Lichess-Bestand. Qualitätsfilter können geringe Spielzahlen
oder hohe Unsicherheit systematisch unterrepräsentieren.

| Puzzle-Rating | Geeignet nach Metadatenfiltern | Zuggeprüft | Aufgenommen |
| --- | ---: | ---: | ---: |
| 1000–1299 | 1.113.964 | 2.500 | 2.500 |
| 1300–1599 | 1.031.945 | 4.000 | 4.000 |
| 1600–1899 | 892.687 | 4.500 | 4.500 |
| 1900–2199 | 724.805 | 3.800 | 3.800 |
| 2200–2499 | 443.329 | 2.700 | 2.700 |
| 2500–2999 | 224.440 | 1.800 | 1.800 |
| 3000+ | 1.555 | 701 | 700 |
| **Gesamt** | **4.432.725** | **20.001** | **20.000** |

- Im Gesamtprofil waren Rätsel-IDs eindeutig. Es gab keine ungültigen
  numerischen Werte, fehlenden Pflichtwerte für FEN/Züge/Themen oder
  abweichenden Game-URL-Präfixe. 4.961.821 Zeilen enthielten keine
  Eröffnungs-Tags. Das Feld ist laut Lichess optional.
- 1.415.234 Zeilen lagen unter Rating 1000, 309.868 unter Popularität 60,
  216.872 über Ratingabweichung 125 und 62.572 unter zehn Versuchen.
  Mehrere Gründe können bei derselben Zeile auftreten.
- Die Quartile des Quellratings lagen bei 1038, 1411 und 1870, nach
  Metadatenfiltern bei 1298, 1620 und 2002. Das Produktpaket reicht von
  Rating 1000 bis 3330, der Median ist 1818.
- Der 3000+-Auswahl fiel ein Duplikat aus gleicher spielbarer Stellung
  und Lösung heraus. Der Nachrücker wurde aus demselben Band geprüft.
  Der Lauf fand unter den 20.001 untersuchten Zeilen keinen illegalen
  Zug. Ein eigener Regressionstest belegt den Nachrücker auch bei einem
  illegalen Zug.
- Das Paket enthält 20.000 eindeutige IDs, 73 Themen, 9.731 Endspiele,
  9.466 Mittelspiele, 3.606 Einträge mit Eröffnungs-Tags und 743
  Zugfolgen mit mindestens einer Umwandlung. Mehrfachthemen sind möglich.
  Zugfolgen einschließlich Aufbauzug reichen von 2 bis 24 Halbzügen.
- Die entpackte SHA-256 des exakt 1.177.486.537 Byte langen CSV-Streams
  lautet `8ce98180bcb7cb60f3f51f12afdbe6a4fd294d8aaf4f1410e8c25e85ac78fdc9`.

## Lokale Lieferartefakte

Basisordner
`/Users/shaye/.local/share/chess-and-chains-iv-b/2026-11-28`.
Produktpaket `lichess-core-20k`, Revision `2026-11-28-7b0d235fa40c`,
Pack-Schema 1. Der Build-Bericht enthält das vollständige strukturierte
Profil mit Häufigkeiten pro Rating, Themen und Qualitätsmerkmal.

| Datei im Basisordner | Bytes | SHA-256 |
| --- | ---: | --- |
| `lichess_db_puzzle.csv.zst` | 309.751.173 | `7b0d235fa40cfd7fdb7df1fec56a96b3b6ee1496b32ed2eb05be90d0ebf94253` |
| `lichess-core-20k/puzzles.jsonl` | 10.818.647 | `2ebc99d811d159e42a39ae33acb280c2e6a410826d9c67f24386924343b338a6` |
| `lichess-core-20k/manifest.json` | 533 | `b7fb664de2a74492b202657d48f17d24cf05d436c709f35b03d4a87217573147` |
| `lichess-core-20k/import_report.json` | 116.412 | `f4b351620cbd2673ccb21d5b031166b0dd298dd3d31e622dbe6933c2d84cec60` |

`download.headers` und `download.result` halten Transportmetadaten fest.
Das Build-Protokoll liegt in `build.log`.
Die vollständige Profilierung dauerte 54,332 Sekunden, die geschichtete
Regelprüfung 197,484 Sekunden und die Paketpublikation 0,165 Sekunden.

## Index und Offline-Abnahme

Das Standardprofil liegt getrennt. Die tatsächliche isolierte Installation
steht im Basisordner unter `test-profile/puzzle_packs/lichess-core-20k`.
Der geprüfte Index
`test-profile/puzzle_packs-catalogs/lichess-core-20k/eacede1d861a23ab06035fbcc58c7ad60e7ce34b485329d93dc38a395379d0e2.sqlite3`
ist 15.495.168 Byte groß. Sein Dateiname enthält die verifizierte
SHA-256. `validated.json` bindet Manifest, Nutzdaten und Index aneinander.

Der native Realdatenlauf endete mit Exit 0. Er prüfte die Installation der
20.000 Aufgaben, kombinierte Themen- und Ratingfilter, den Aufbauzug,
einen Fehlversuch mit zwei Hinweisen, einmaliges Speichern einer Lösung,
die Filter für ungelöste und zu wiederholende Aufgaben, eine anschließende
saubere Lösung und das Anzeigen einer Lösung als ungelösten Versuch.
Der Wiederholungsplan erkannte beide Datensätze. Der Fortschritt blieb
vom Demo-Paket getrennt. Backup, Zwischenänderung, Rücksicherung und
erneuter Start stellten die ursprünglichen Versuche wieder her. In
einem zweiten Ziel ohne installierten Katalog meldete Restore die
fehlende Paketreferenz und erhielt die Versuche.

| Messung | 20.000 Realdaten IV-B | 20.000 synthetische F13-Fixtures |
| --- | ---: | ---: |
| Lokaler Erstimport mit vollständiger Regelprüfung | 190,34 s | 64,28 s vollständige Regelprüfung |
| Index veröffentlichen | 1.224,78 ms | 1.056,70 ms |
| Vorvalidierten Index öffnen | 35,66 ms | 19,56 ms |
| Kombinierter Rating-/Themenfilter | 5,47 ms | 6,28 ms |
| Abruf per ID | 0,160 ms | 0,197 ms |
| 20 IDs mit festem Seed ziehen | 0,034 ms | 0,031 ms |
| Nächste PuzzleSession | 1,83 ms | 3,08 ms |

Die reale Messung lief auf macOS arm64 mit Python 3.14.5 und Tk 9.0.
Der F13-Vergleich verwendet die frühere 20.000er-Messung. Die Daten
haben unterschiedliche Zuglängen und Themen. Installationsmessung
und frühere reine Regelprüfung enthalten unterschiedliche Arbeitsschritte.
Die reale kombinierte Suche für Mittelspiel und Rating 1350–2050 fand
4.920 Aufgaben. Der Zeitwert von 1.169,09 ms für den Desktop-Neustart
enthält App-Aufbau und Katalogwahl. Der Spitzen-RSS des kombinierten
Installations- und Tk-Prozesses war 294.404.096 Byte. Backup und Restore
benötigten 4,05 beziehungsweise 9,65 ms im kleinen Testprofil.
[Frühere synthetische Messungen](2026-11-27_F13-F26-functional-completion.md#rätsellastprobe)

### Regression und Reproduktion

Geprüfter Produktcode `a40f820c5398942d23e1629fed0e57c24383aa74`.
Die Prozessausgaben liegen als `acceptance.log` und `reproduction.log`
im lokalen Basisordner.

| Prüfung | Ergebnis |
| --- | --- |
| `PYTHONPATH=src python3 scripts/ci_tests.py inventory` | 487 Tests erfasst, Exit 0 |
| `PYTHONPATH=src python3 scripts/ci_tests.py headless` | 316 erfolgreich, Exit 0 |
| `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1 PYTHONPATH=src python3 scripts/ci_tests.py gui` | 160 native Tests erfolgreich, Exit 0 |
| `PYTHONPATH=src python3 scripts/ci_tests.py pytest` | 11 Figurensatztests, Exit 0 |
| `sandbox-exec` mit gesperrtem Netzwerk, `tests.test_puzzles tests.test_training` | 53 erfolgreich, Exit 0 |
| Standard- und optimierter Glide-Selbsttest | Je 13/13, Exit 0 |
| Starter-, Link-, Richtlinien-, Kompilierungs- und CLI-Prüfungen | Exit 0 |
| `python3 -B scripts/build_brand_assets.py --check` | 41 korrekte Ausgaben, Exit 0 |
| Vollständiger Zweitbuild und JSONL-Prüfsummenvergleich | Bytegleiche JSONL-Datei, Exit 0, 258,81 Sekunden, 124.977.152 Byte Spitzen-RSS |

Für diesen Branch liegt eine lokale macOS-Abnahme vor. Linux und Windows
gehören zur späteren Branch-CI. Verwaltete Glide Shell, Branding,
Figurensets und Versionsdatei wurden gegen den Ausgangsstand geprüft.


## Befehle

Die Pfade beziehen sich auf die tatsächliche lokale Ablage. Profilierung,
Validierung, Reproduktion und Realdaten-Abnahme nutzten auf macOS die
Netzwerksperre von `sandbox-exec` mit `(deny network*)`.

```bash
IVB_DATA=/Users/shaye/.local/share/chess-and-chains-iv-b/2026-11-28
RAW_SHA=7b0d235fa40cfd7fdb7df1fec56a96b3b6ee1496b32ed2eb05be90d0ebf94253

curl --fail --location --retry 3 --silent --show-error \
  --dump-header "$IVB_DATA/download.headers" \
  --output "$IVB_DATA/lichess_db_puzzle.csv.zst.partial" \
  --write-out '%{url_effective} %{http_code} %{size_download} %{time_total}\n' \
  https://database.lichess.org/lichess_db_puzzle.csv.zst > "$IVB_DATA/download.result"
test "$(stat -f %z "$IVB_DATA/lichess_db_puzzle.csv.zst.partial")" = 309751173
mv "$IVB_DATA/lichess_db_puzzle.csv.zst.partial" "$IVB_DATA/lichess_db_puzzle.csv.zst"
shasum -a 256 "$IVB_DATA/lichess_db_puzzle.csv.zst"
zstd -t "$IVB_DATA/lichess_db_puzzle.csv.zst"

PYTHONPATH=src sandbox-exec -p '(version 1) (allow default) (deny network*)' \
  python3 scripts/build_lichess_core_pack.py "$IVB_DATA/lichess_db_puzzle.csv.zst" \
  "$IVB_DATA/lichess-core-20k" --expected-sha256 "$RAW_SHA" --snapshot 2026-11-28
CHESS_AND_CHAINS_REQUIRE_DISPLAY=1 PYTHONPATH=src \
  sandbox-exec -p '(version 1) (allow default) (deny network*)' \
  python3 -u scripts/verify_lichess_core_pack.py "$IVB_DATA/lichess-core-20k" "$IVB_DATA/test-profile"
```

Build und Abnahme erwarten jeweils ein frisches Zielverzeichnis. Für den
zweiten Build wurde ein separater temporärer Ordner im Basisordner
verwendet. Die Reproduktion vergleicht die vollständigen JSONL-Bytes.
Manifest und Build-Bericht enthalten eigene Zeitangaben.

## Übergabe für Auftrag V – Connected Learning

1. Den lokal installierten Katalog über `PackLibrary.open_catalog("lichess-core-20k")`
   öffnen. Rätselfilter und ID-Seiten liefert `IndexedPuzzlePack.catalog`.
   Seed, Revision und Quell-SHA bei vergleichenden Läufen festhalten.
2. Wiederholpfade aus `Database.puzzle_training_ids()` und
   `Database.due_puzzle_ids()` aufbauen. Versuche bleiben unter
   `lichess-core-20k` und der ursprünglichen `PuzzleId` adressierbar.
3. Für Themenpfade das geprüfte Katalog-Thema mit Ratingband und
   Fortschrittsstatus kombinieren. Erst wenige IDs materialisieren,
   damit die reguläre Ansicht bei 20.000 Aufgaben schnell bleibt.
4. Persönliche Analyse-Trainingskandidaten aus Auftrag III separat
   bewerten. Kandidaten tragen ihre eigene Herkunft und werden erst nach
   fachlicher Prüfung zu bewerteten Übungen.
5. Für einen späteren kompatiblen Paketwechsel bestehende IDs und
   Ausgangsstellung samt Lösung stabil halten und das vorhandene
   Revisionsverfahren verwenden. Die Produktverteilung bleibt getrennt
   von der lokalen Trainingsintegration.
