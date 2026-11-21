# W10 – Rätselthemen im Puzzle Lab

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Der lokale Branch
`codex/chess-chains-w10-raetselthemen` basiert auf
`c0b9b20bb6c0bd0447bb50389df71a38c687e905` aus PR #10.
Der Code- und Testcommit lautet `352f878ebb5f95dfcc197db37eec0563d70626b9`,
Tree `9cafdf596847ba66c5143588758abbdf566ba1ad`.

## Änderung

Die zehn Themenkennungen des mitgelieferten Demo-Pakets haben lesbare
DE/EN-Bezeichnungen im Filter und in den Details. Das Feld
`backRankMate` erscheint beispielsweise als „Grundreihenmatt“ oder
„Back-rank mate“. Zusätzliche Kennungen eines eigenen Pakets erscheinen
mit „Kennung“ bzw. „Tag“ und dem Originalwert. Die Oberfläche ordnet die
Filterposition weiterhin der ursprünglichen Themenkennung zu. Packdaten,
SQLite und Fortschritt bleiben kompatibel. Die Änderung verwendet den
bestehenden Sprachkatalog und benötigt keine neuen Abhängigkeiten.
[Sprachkatalog](../../src/chess_and_chains/i18n/catalog.py) ·
[Puzzle Lab](../../src/chess_and_chains/ui/app.py)

## Lokale Prüfungen

Windows 11 Pro x64 (10.0.26300), Python 3.15.1 und Tk 9.0.4.
Für die Unittest-Läufe galten `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`,
`PYTHONWARNINGS=error::ResourceWarning` und `PYTHONFAULTHANDLER=1`.

| Prüfung | Ergebnis |
| --- | --- |
| `python -m unittest tests.test_app_integration.PuzzleUiTests -q` vor dem Codefix | Fehler reproduziert, Exitcode 1. Die deutsche Detailzeile zeigte die Originalkennungen, im englischen Filter fehlte „Opening“. Im englischen Test blockierte anschließend die SQLite-Datei das Entfernen des Testordners. Die Testbereinigung schließt nun zuerst die App und danach den temporären Ordner. |
| `python -m unittest tests.test_i18n tests.test_app_integration.PuzzleUiTests -q` | 12 Tests bestanden, Exitcode 0. Abgedeckt sind Katalogparität, alle Demo-Themen, zusätzliche Kennungen, Themenwahl in DE und EN und der vorhandene Fortschritts-/Ratingfilter. |
| `python -m unittest discover -s tests -q` | 207 Tests bestanden, Exitcode 0 (93,307 s). |
| `py -3.14 -m unittest tests.test_i18n tests.test_app_integration.PuzzleUiTests -q` | Python 3.14.7, Tk 9.0.4. 12 Tests bestanden, Exitcode 0. |
| Lokale Tk-Geometrieprobe (`python -`) | DE und EN bei 860 × 700 px mit `tk scaling` von 96, 144 und 192 px pro Zoll. Die breiteste Beschriftung wurde ausgewählt und die Filteraktion ausgelöst. Ihre Tk-Schriftbreite lag in allen sechs Kombinationen innerhalb der per `ttk.Combobox.identify` ermittelten Textfläche. Exitcode 0. |

Die Geometrieprobe misst Tk-Textskalierung und Auswahl im Testfenster.
Die Abnahme der Systemskalierung und Screenreader stehen aus.

Für die aktualisierte Dokumentation bestanden `python scripts/verify_starter.py`,
`python scripts/verify_document_links.py`, `python scripts/check_policy.py`,
`python -m compileall -q src app scripts tests` und `git diff --check`.
`python -m unittest tests.test_foundation tests.test_i18n -q` bestand
22 Tests. Alle Befehle endeten mit Exitcode 0.

## Basis und Plattform-CI

Die GitHub-API meldete für den offenen [PR #10](https://github.com/n05a-design/chess-and-chains/pull/10)
im Push- und PR-Lauf je 14 von 14 erfolgreichen Jobs am Basiskommit
`c0b9b20bb6c0bd0447bb50389df71a38c687e905`. Beide Läufe enthalten je
einen erfolgreichen nativen macOS-Tk-Job für Python 3.11 und 3.14.
GitHub-`main` stand beim Abgleich auf
`6bcd9ada580be10f289c34dd0040be62297597d2`.
[Push-Lauf](https://github.com/n05a-design/chess-and-chains/actions/runs/44873594704) ·
[PR-Lauf](https://github.com/n05a-design/chess-and-chains/actions/runs/44873625858)

## Übergabe

1. Den lokalen Folgecommit in der Plattform-CI prüfen, einschließlich
   nativer macOS-GUI. Der CI-Nachweis oben gilt für die Basis.
2. W10/W11 bei nativer Systemskalierung und mit Screenreadern prüfen.
   Die Reihenfolge und Szenarien führt die [QA-Matrix](../qa/TEST_PLAN.md).
3. Für produktive Rätselpakete nach dem Import die tatsächlich gelieferten
   Themen gegen den Katalog prüfen. Der Import hängt weiter an Q-022.
   [Offene Fragen](../questions/OPEN_QUESTIONS.md)

W10 und W11 bleiben für ihre belegten Teilumfänge `TESTED`.
Für einen Rollback genügt die Rücknahme des Codecommits und seiner
Dokumentation. Es gibt keine Datenmigration.
