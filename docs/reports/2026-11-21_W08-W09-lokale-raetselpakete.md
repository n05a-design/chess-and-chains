# W08/W09 – Lokale Rätselpakete im Puzzle Lab

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Lokaler Branch
`codex/chess-chains-w08-w09-lokale-raetselpakete` auf dem W06-Stand
`7ba2cd1`. GitHub-`main` stand beim Abgleich auf
`d2fe5f790de1aff2b11cc6faedc3b3967aa8fae5`. Der lokale Paketimport steht
in `bc75d392ffe3b49494f3b2ba36ca923e4401eade`. Die Tk-Integration und
der geprüfte Code-Stand lauten `9b3d68d74f97cc8971add597eee606bade274084`,
Tree `b3e37c2ab5458949c49c56d5461c2804595790ef`.

## Zusammenhängender Ablauf

- Der Button „Rätselpakete…“ öffnet die vorhandene, tastaturbedienbare
  Dialogkomponente. Dort stehen die Demo, installierte Pakete und
  „Paketordner importieren…“ zur Verfügung.
- Die App liest Manifest und Rätseldaten aus dem gewählten Ordner. Sie
  prüft Typen, Prüfsumme, Rating, Duplikate und die komplette Zugfolge
  mit denselben Abbruchregeln wie eine Trainingseinheit. Ein gültiger
  Stand wird atomar unter `puzzle_packs/<pack_id>` übernommen.
  Paket-ID und Originalbytes bleiben erhalten. `demo` ist reserviert.
  Eine vorhandene Paket-ID wird abgewiesen.
- Die Validierung läuft in einem Hintergrundthread. Bis zum erfolgreichen
  Abschluss bleibt die bisherige Aufgabe spielbar. Bei einem Fehler
  zeigt der Paketbereich den Grund, und die Auswahl und der Fortschritt
  bleiben erhalten. Aktive Paketversion und Quelle stehen bei den
  Rätselinformationen. Der Titel zeigt die aktive Paketkennung.
- Beim Wechsel stellt die App Thema und Rating zurück und beginnt mit
  dem ersten Rätsel des gewählten Pakets. Dieselbe Rätsel-ID in zwei
  Paketen hat zwei getrennte SQLite-Fortschritte. Die bestehende
  Einstellung `last_pack_id` stellt beim Start die letzte Paketwahl
  wieder her. Fehlt sie oder ist der zugehörige Ordner beschädigt, bleibt
  die Demo verfügbar. Beim Fehler bleibt die gespeicherte Kennung zur
  späteren Wiederaufnahme erhalten.
- Die App liest das Manifest bis 64 KiB und die JSONL-Datei bis 64 MiB.
  Die optionale Datei `import_report.json` bleibt beim Build. Es wurden
  keine Abhängigkeiten, Kontakte zum Netz oder Datenmigrationen
  eingeführt.
  [Anleitung](../../data/puzzle_packs/README.md#in-der-app-verwenden)

## Prüfungen

Windows 11 Pro x64 (10.0.26300), Tk 9.0.4. Unittest-Läufe mit
`CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`,
`PYTHONWARNINGS=error::ResourceWarning` und `PYTHONFAULTHANDLER=1`.

| Prüfung | Ergebnis |
| --- | --- |
| `python -m unittest tests.test_puzzles tests.test_i18n tests.test_app_integration.PuzzleUiTests -q` und derselbe Lauf mit `py -3.14` | Je 42 Tests, Exitcode 0, Python 3.15.1 und 3.14.7. Darunter parallele Importe, reservierte Kennung, leeres Paket, abgebrochene Zugfolge, fehlendes Startpaket und getrennte Speicherstände. |
| `python -m unittest discover -s tests -q` | Python 3.15.1, 223 Tests bestanden, Exitcode 0 (111,826 s). |
| Tk-Dialogprobe und Sichtprüfung | Native Windows-Tk-Oberfläche, echter Auswahldialog per Enter, isolierte Daten, Fokus zurück auf „Rätselpakete“. DE bei 96 Tk-DPI/1180 × 820 px, EN bei 192 Tk-DPI/860 × 700 px. Darstellungsproben zeigten Paketwahl und Aufgabe. Bei doppelter Textskalierung brachte die Fokussierung den Hinweisbutton ins Sichtfeld. Die Tests ersetzen den nativen Ordnerpicker durch lokale Pfade. |
| Synthetischer Import mit 2.000 Aufgaben | 665.600 Byte JSONL, 10,518 s bis zum geladenen Paket. Währenddessen 116 Tk-Callbacks mit 78,7 ms medianem und 560,6 ms maximalem Abstand. Die installierten Dateien stimmten byteweise mit ihren Quellen überein. Exitcode 0. Einzelmessung mit wiederholten projekteigenen Stellungen. |
| Statische Prüfungen | `verify_starter.py`, `verify_document_links.py`, `check_policy.py`, `python -m compileall -q src app scripts tests` und `git diff --check` jeweils Exitcode 0. |

### Plattformfehler im ersten GitHub-Lauf

Der [Push-Lauf](https://github.com/n05a-design/chess-and-chains/actions/runs/44907999017)
zu `d18a55e0a904e2a0ab96554200f8f3fb2aacbaa5` endete mit 10 von
14 erfolgreichen Jobs. Die Puzzle-Pipeline auf macOS und Windows
meldete je zwei Fehlschläge und einen Fehler. Die Pfadprüfung verglich den
aufgelösten Paketpfad mit dem ursprünglichen Pfad. Dadurch bewertete sie
auch einen abweichend aufgelösten übergeordneten Datenpfad als Umleitung.
Die Korrektur kanonisiert zuerst den Datenstamm und vergleicht erst
darunter die Bibliothek und das Paket. Verlinkte Bibliotheks- und
Paketordner werden weiterhin abgewiesen.

Der neue Aliastest reproduzierte den Fehler lokal auf Windows mit Exitcode 1.
Mit der Korrektur liefen `py -3.14 -m unittest tests.test_puzzles -v`
(29 Tests, einschließlich der beiden Verzeichnislinks) und
`python -m unittest tests.test_app_integration.PuzzleUiTests -q`
(7 Tests mit Python 3.15.1 und Tk 9.0.4) mit Exitcode 0. Der
[PR #13](https://github.com/n05a-design/chess-and-chains/pull/13)
enthält die Plattformprüfung des Korrekturstands.

Für `dd47f2238c992906ce34302dfef5d1c1e24187d4` schlossen sowohl der
[Push-Lauf](https://github.com/n05a-design/chess-and-chains/actions/runs/44908406125)
als auch der
[PR-Lauf](https://github.com/n05a-design/chess-and-chains/actions/runs/44908410466)
alle 14 Jobs erfolgreich ab. Auf macOS liefen in der PR-Matrix je 60
native Tk-Tests und 142 Kern-, UCI-, Puzzle- und Speichertests mit
Python 3.11 und 3.14. Die Tests für umgeleitete Paketordner liefen auf
macOS ohne Skip.

Der [Merge-Lauf für `main`](https://github.com/n05a-design/chess-and-chains/actions/runs/44908853250)
zum anschließenden Merge `12a86e0e225955c73a828efb70941aa231c8d72e`
bestand ebenfalls alle 14 Jobs einschließlich der vier macOS-Jobs.

## Übergabe

1. Nativen Ordnerdialog und Screenreader auf den Zielsystemen prüfen.
2. Nach Freigabe Q-022 einen produktiven Export verarbeiten und Größe,
   Laufzeit, Validierungsfehler und Zusammensetzung messen. Die synthetische
   Messung belegt keinen Produktionsdatensatz.
3. Paketumfang und Ratingbereich über Q-008/Q-009 abnehmen. Profilmodell
   und Datenvertrag stehen weiter zur Inhaberentscheidung.

Für den Rollback lassen sich Code, Tests und Dokumentation zurücknehmen.
Die neuen Paketordner sind von bestehenden SQLite- und Einstellungsdateien
getrennt. Eine Schemamigration ist dafür nicht erforderlich.
