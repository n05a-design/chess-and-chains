# W06 – Perspektivwechsel in der SVG-Brettvorschau

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Lokaler Branch
`codex/chess-chains-w06-svg-brettcache` auf GitHub-`main` bei
`d2fe5f790de1aff2b11cc6faedc3b3967aa8fae5`. Implementierung und Tests
stehen in `6424ec48cde4c23ac15eb253119fdd237f965e42`, Tree
`968f536a7b141d0f91e7bd30ab0ab98e093cce80`.

## Umsetzung

Die Vorschau hält die beiden fertig gerenderten Hintergründe für die
aktuelle Feldgröße und den aktiven Tk-Interpreter vor. Vorher hielt sie
nur die zuletzt gerenderte Perspektive. Bei Feld-SVGs kopiert die
Vorschau für die andere Perspektive die bereits gezeichneten Felder in
umgekehrter Brettreihenfolge. Die Motive bleiben aufrecht, und Transparenz
und Schachkoordinate bleiben erhalten. Bei einem Gesamt-SVG rendert
Tk jede Perspektive bei der ersten Anfrage mit ihrer bisherigen
Transformation. Der nächste Wechsel benutzt das vorhandene Bild.

Der Cache umfasst je Brettvorschau höchstens zwei Hintergrundbilder.
Ein Größen- oder Interpreterwechsel verwirft die Cache-Einträge.
Die SVG-Dateien und ihre vorherigen Lieferformate bleiben erhalten.
[SVG-Lieferanleitung](../../assets/boards/source/README.md)

## Prüfungen

Windows 11 Pro x64, Python 3.15.1/Tk 9.0.4. Positive Unittest-Läufe mit
`CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`,
`PYTHONWARNINGS=error::ResourceWarning` und `PYTHONFAULTHANDLER=1`.

| Prüfung | Ergebnis |
| --- | --- |
| `python -m unittest tests.test_board_ui.BoardArtworkUiTests -q` vor der Änderung | Exitcode 1. Beide Fälle erzeugten für die Rückkehr zur ersten Perspektive ein neues Bild. |
| `python -m unittest tests.test_board_ui tests.test_app_integration -q` | 57 Tests bestanden, Exitcode 0. Feldzuordnung, aufrechtes asymmetrisches Akzentmotiv, Transparenz, Zugmarkierungen und Cache-Wechsel bei neuen Größen geprüft. |
| `python -m unittest discover -s tests -q` | 217 Tests bestanden, Exitcode 0 (93,311 s). |
| `py -3.14 -m unittest tests.test_board_ui -q` | Python 3.14.7 mit Tk 9.0.4, 17 Tests bestanden, Exitcode 0. |
| `python -m chess_and_chains --headless-check --board-design assets/boards/source/board-template.svg` mit `PYTHONPATH=src` | Exitcode 0, SVG-Vorlage aus dem Entwicklerstart geladen. |
| Struktur und Policy | `verify_starter.py`, `verify_document_links.py`, `check_policy.py`, `python -m compileall -q src app scripts tests` und `git diff --check` jeweils Exitcode 0. |

### Tk-Messung

15 Wiederholungen je Format, Größe und Implementierung. Zeiten sind
Mediane für den Aufbau des Hintergrundbilds bei erster Drehung und
Rückkehr zur vorherigen Ansicht. Die gepaarten Pixel- und
Transparenzproben stimmten für beide Perspektiven an jeweils drei
Messpunkten pro Feld mit der Basis überein. Der Vorlagen-Hash blieb
gleich. Die Messung beschreibt diesen Windows-Rechner und zwei
Testmotive. Sie umfasst weder die komplette Fensterneuzeichnung noch
die nativen macOS- oder High-DPI-Messungen.

| Motiv und Feldgröße | Erste Drehung vorher → jetzt | Rückkehr vorher → jetzt |
| --- | --- | --- |
| 64 Test-SVGs, 48 px | 22,955 → 7,721 ms | 25,874 → 0,001 ms |
| 64 Test-SVGs, 72 px | 38,838 → 14,159 ms | 38,453 → 0,002 ms |
| Gesamtbrett-Vorlage, 48 px | 3,746 → 5,192 ms | 3,784 → 0,001 ms |
| Gesamtbrett-Vorlage, 72 px | 7,922 → 7,258 ms | 7,755 → 0,002 ms |

## GitHub und Übergabe

PR #12 wurde extern gemergt. Der erste PR-Head hatte rote Aqua-Tests
bei der Fokusrückkehr. Mit `3716faa` bestanden Push und PR jeweils
14 von 14 Jobs und danach der Merge-Lauf auf `main` ebenfalls 14 von 14.
Auf dem korrigierten PR-Head führten die nativen macOS-Jobs in beiden
Läufen jeweils 56 GUI-Tests erfolgreich aus. Der lokale W06-Folgebranch
ist auf dem verifizierten Merge-Tree aufgebaut.
[PR #12](https://github.com/n05a-design/chess-and-chains/pull/12) ·
[Merge-Lauf](https://github.com/n05a-design/chess-and-chains/actions/runs/44905214890)

1. Plattform-CI für den W06-Folgebranch ausführen, sobald der Push
   beauftragt ist.
2. Finale Inhaber-Bretter nach Eingang mit V.02, Draufsicht,
   Tastaturfokus, Partie und Rätseln prüfen. Die geplante Abnahme umfasst
   beide Perspektiven, Kontrast und native Skalierung.
3. W10/W11 mit physischem Ziffernblock und Screenreadern abnehmen.
   [QA-Matrix](../qa/TEST_PLAN.md)

Der Rollback nimmt die Code- und Dokucommits zurück. Er benötigt keine
Datenmigration und berührt keine SVG-Master.
