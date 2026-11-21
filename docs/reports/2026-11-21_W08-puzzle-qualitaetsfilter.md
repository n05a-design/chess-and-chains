# W08 – Qualitätsfilter und Herkunft der Rätselpakete

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Lokaler Branch
`codex/chess-chains-w08-puzzle-import` auf dem W10-Stand
`326fd02f45c64a9bee73da1417a3aef23836b1d5`. Implementierungscommit
`cb33b2ee1d415be72695e5c590d88ac0b267f293`, Tree
`ca70db34ff239960371e90bfc73dec69b7bb26be`.
GitHub-`main` stand beim Abgleich auf `6bcd9ada580be10f289c34dd0040be62297597d2`.

## Umsetzung

- Der lokale Paket-Builder filtert optional nach maximaler Ratingabweichung,
  minimaler Popularität und minimaler Spielzahl. Die Grenzen sind inklusiv
  und kombinierbar. Der Importbericht erfasst die Grenzen und die Anzahl
  der Ausschlüsse je Grund. Benötigte, fehlende Messwerte führen bei
  aktivem Filter zur expliziten Ablehnung. Ohne Qualitätsgrenzen bleibt
  die bisherige Auswahl erhalten.
- Der Wert von `--source` wird in das Manifest und jeden Datensatz
  übernommen. Das alte Demo enthielt den vom CSV-Layout geerbten
  Herkunftswert `lichess-puzzle-db` in allen fünf Aufgaben.
- Die neu erzeugte Demo-Paketversion 2 enthält fünf projekteigene
  Aufgaben mit derselben Paket-ID `demo` und denselben Aufgaben-IDs,
  Stellungen, Zügen und Testwertungen. Pack-Schema 1, Spielregeln und
  Projektversion bleiben kompatibel. SQLite verknüpft den Fortschritt
  über Paket-ID und Aufgaben-ID.
- Die Herkunftsprüfung verglich die fünf JSONL-Datensätze mit
  `git show 326fd02:src/chess_and_chains/puzzles/data/demo/puzzles.jsonl`.
  Nur `source` unterschied sich. Das neue Manifest enthält SHA-256
  `99af40743130c691e204070c6c44b0940181b09c84e810ac6182884b09dc0eeb`.
  [Manifest](../../src/chess_and_chains/puzzles/data/demo/manifest.json)

## Lokale Prüfungen

Windows 11 Pro x64 (10.0.26300). Die Unittest-Läufe verwendeten
`PYTHONWARNINGS=error::ResourceWarning`. Für den Gesamtlauf waren außerdem
`CHESS_AND_CHAINS_REQUIRE_DISPLAY=1` und `PYTHONFAULTHANDLER=1` gesetzt.

| Prüfung | Ergebnis |
| --- | --- |
| Zwei neue bzw. erweiterte Regressionen auf der Basis `326fd02` | Exitcode 1. Das neue Filterargument fehlte, und Demo-Datensätze trugen fälschlich den Lichess-Herkunftswert. |
| `python -m unittest tests.test_puzzles tests.test_i18n -q` | Python 3.15.1, 29 Tests bestanden, Exitcode 0. |
| `py -3.14 -m unittest tests.test_puzzles -q` | Python 3.14.7, 21 Tests bestanden, Exitcode 0. |
| Offline-Build mit `scripts/build_puzzle_pack.py` | Die [Beispielparameter](../../data/puzzle_packs/README.md) auf CSV und selbst komprimierte Zstandard-Testdatei angewendet, Python 3.14.7. Je 15 gelesen, 1 akzeptiert, 14 abgelehnt. Beide Ausgaben hatten bytegleiche JSONL-Daten und stimmige Prüfsummen des CSV-Inhalts. Exitcode 0. Ein Folgelauf mit Popularität 101 brach mit Exitcode 2 ab und erhielt die bestehende JSONL-Datei. |
| `python -m unittest discover -s tests -q` | Python 3.15.1/Tk 9.0.4, 209 Tests bestanden, Exitcode 0 (79,045 s). |
| Dokumentation und Policy | `verify_starter.py`, `verify_document_links.py`, `check_policy.py`, `python -m compileall -q src app scripts tests` sowie `git diff --check` jeweils Exitcode 0. `python -m unittest tests.test_foundation -q` bestand 14 Tests, Exitcode 0. |

## Übergabe

1. Plattform-CI für den lokalen Folgebranch ausführen, sobald die
   Veröffentlichung des Branchs freigegeben ist.
2. Nach Q-022 den realen Export lokal prüfen, Datensatzstand, Prüfsumme,
   Fehlerrate und Paketgröße belegen. Bis dahin gilt der Nachweis für
   die projekteigenen Fixtures.
3. Mit dem Datenprofil geeignete Schwellenwerte, Seed-Auswahl und
   Veröffentlichungsgröße bestimmen. Q-008 und Q-009 bleiben offen.
   [Entscheidungsregister](../questions/OPEN_QUESTIONS.md)

W08 bleibt `TESTED` für den Fixture-Umfang. Für einen Rollback können
Code, Paketdateien und zugehörige Dokumentation gemeinsam zurückgenommen
werden. Eine SQLite-Migration ist dafür nicht erforderlich.
