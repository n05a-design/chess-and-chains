# W10 – Auswahldialoge per Tastatur bedienen

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Lokaler Branch
`codex/chess-chains-w10-dialogtastatur`, Basis ist der GitHub-Merge von
PR #11 auf `16133e464e6652d127ad7f50827703943a5f2fd1`. Code und
Teständerung stehen in `1ecce50f74125b0343291b2f96982979d8e60f01`,
Tree `65248994b4feb22fac2a2f2f6657809d62f1837c`.

## Befund und Änderung

Auf Windows/Tk 9.0.4 aktiviert die Leertaste ein fokussiertes
`ttk.Button`-Widget. Enter ist dort standardmäßig keiner
Schaltflächenaktion zugewiesen. In der Bibliothek blieben fokussierte
Import- und Exportbuttons deshalb bei Enter ohne Aktion. Der allgemeine
Auswahldialog wird auch für Remisansprüche verwendet.

Die Dialogbuttons verwenden nun dieselben Bindungen für Enter und
Ziffernblock-Enter wie andere App-Buttons. Native Leertasten- und
Mausbedienung behalten ihre bisherigen Bindungen. Ein Dialog mit
Einträgen fokussiert die Auswahl. Ohne Einträge bekommt die erste
verfügbare Aktion den Fokus, ersatzweise „Abbrechen“. Beim Schließen
kehrt der Tastaturfokus zum vorherigen, weiterhin sichtbaren Element
zurück. Der Datenbestand und das Dialoglayout bleiben kompatibel.

## Prüfungen

Windows 11 Pro x64 (10.0.26300). Für die positiven Unittest-Läufe galten
`CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`,
`PYTHONWARNINGS=error::ResourceWarning` und `PYTHONFAULTHANDLER=1`.

| Prüfung | Ergebnis |
| --- | --- |
| Tastaturregression vor dem Codefix | Python 3.15.1/Tk 9.0.4, Exitcode 1. Der fokussierte Importbutton erhielt Enter. Die Importaktion wurde nicht ausgelöst. |
| `python -m unittest tests.test_app_integration.StorageAndLocaleUiTests tests.test_app_integration.DrawClaimTests tests.test_app_integration.PromotionUiTests -q` | 17 Tests bestanden, Exitcode 0. PGN-Import in eine leere Bibliothek und Export eines ausgewählten Spiels über Enter. Escape schließt den Dialog. Alle drei Wege geben den Fokus an die Bibliotheks-Schaltfläche zurück. System-Dateiauswahl durch lokale Testdateien ersetzt. |
| `python -m unittest discover -s tests -q` | Python 3.15.1/Tk 9.0.4, 216 Tests bestanden, Exitcode 0 (87,212 s), Commit `1ecce50`. |
| `py -3.14 -m unittest tests.test_app_integration.StorageAndLocaleUiTests.test_library_keyboard_import_and_export_restore_focus -q` | Ein Test bestanden, Exitcode 0. Die abschließende Probe stellt zusätzlich sicher, dass keine Zeitüberschreitung den Dialog geschlossen hat. Sie bestand auch unter Python 3.15.1 mit dem gleichen Testpfad. |
| Struktur, Links und Policy | `verify_starter.py`, `verify_document_links.py`, `check_policy.py`, `python -m compileall -q src app scripts tests` und `git diff --check` jeweils Exitcode 0. |

Der Test prüft auch die Ziffernblock-Bindung. Windows-Tk synthetisierte
`KP_Enter` in der Gegenprobe als Tastencode 0. Eine physische
Ziffernblocktaste ist mit dieser Probe daher nicht belegt.

## GitHub-Abgleich und nächste Abnahmen

- Der Merge-Tree von PR #11 ist bytegleich zum letzten PR-Head
  `c0868a0`. Nach dem Abgleich von Eltern und Tree wurde der lokale
  Tracking-Verweis auf `main` aktualisiert. Der normale Fetch meldete
  weiterhin die bekannte fehlerhafte OneDrive-Git-Referenz.
  [Vorheriger Befund](2026-11-21_W08-puzzle-seed.md#github-abgleich)
- Der Merge-Lauf bestand 14 von 14 Jobs, einschließlich nativer
  macOS-Tk-Jobs mit Python 3.11 und 3.14. Der lokale Dialogfix hat eigene
  Windows-Nachweise. [Merge-Lauf](https://github.com/n05a-design/chess-and-chains/actions/runs/44904083668)
- Als nächste Abnahmen folgen GUI-CI für den lokalen Folgebranch,
  Tastaturbedienung bei nativer Systemskalierung und die Prüfung mit
  Screenreadern. W10/W11 bleiben entsprechend ihrem belegten Umfang
  `TESTED`. [QA-Matrix](../qa/TEST_PLAN.md)

Ein Rollback besteht aus der Rücknahme des Code- und Dokucommits. Es
gibt keine Migration oder neue Laufzeitabhängigkeit.
