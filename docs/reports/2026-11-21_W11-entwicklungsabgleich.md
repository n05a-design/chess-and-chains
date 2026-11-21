# W11 – Lokale Folgecommits, Projektablage und GitHub

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Arbeitsbranch
`codex/chess-chains-entwicklungsabgleich`. Ziel ist GitHub-`main`
bei `e84ad181f0c1ce25e792f96164fb47f5580f499b` nach PR #10.
Die Übernahme begann auf dem lokalen Stand
`660204388da72db00e8d1af6ed5befc4a14341af`. Der Prüfcommit für Code und
Verifikation ist `5e59383f0029b572c23399a8c60302ba11acfcb1`,
Tree `502d0124ebdf3abd070ebf1273a6501a3eb6c817`.

## Lokale Projektstände

| Bereich | Befund |
| --- | --- |
| Aktiver Worktree und Branches | Vor neuen Änderungen sauber. Acht lokale Folgecommits seit PR #10 enthalten W10-Rätselthemen, W08-Import und Seed-Auswahl sowie W05-Pattfolgen. Alle 17 lokalen Branchspitzen sind in `main` oder im ursprünglichen Kandidaten erreichbar. Der ältere abgelöste Mac-Worktree mit `dd09fe6` ist ebenfalls in `main` erreichbar. |
| OneDrive-Arbeitsdateien | 95 geänderte oder unversionierte Pfade gegen die veröffentlichte History geprüft. 93 passen bytegleich oder nach Zeilenendennormalisierung. Ein Bericht ist mit gekürztem Rechnerpfad bereits im Archiv vertreten. Seine aktuelle Original-Prüfsumme entspricht der dokumentierten Quelle. Eine 98-Byte-Affinity-Sperrdatei ist ein lokaler Arbeitsmarker. |
| OneDrive-Index | Alle sechs gestagten Dateiinhalte sind über GitHub-`main` erreichbar. Index und Arbeitsdateien der OneDrive-Ablage blieben erhalten. |
| Älterer Claude-Worktree | Alle 168 lesbaren Projektdateien sind in `main` nachgewiesen. Die zwei anderen Mac-Arbeitsverzeichnisse aus der Git-Registrierung sind auf diesem Rechner unerreichbar. Ihre gespeicherten Commitstände sind in `main` enthalten. |
| SVGs, Design und Quellen | Die bisherigen Master, Vorschauen, Fonts, Lizenzhinweise und Archivstände sind hinter GitHub-`main` bereits erreichbar. Im Wheel befinden sich die ausgewählten Laufzeitdateien. |

Der Inhaltsabgleich verwendete `git diff --name-only HEAD`,
`git ls-files --others --exclude-standard`, `git diff --cached --name-only`
und `git rev-list --objects origin/main HEAD`. Es wurde der Git-Blob
je Datei und Index-Version verglichen. Vorübergehende Dateien, Caches,
Buildausgaben und Werkzeugzustand verblieben in den lokalen Ablagen.
[Früherer Ablageabgleich](2026-11-21_W11-ablageabgleich.md) ·
[Archivquellen](../archive/onedrive-2026-11-21/SOURCES.csv)

## Geschlossene Lücken

- W08. Die gepufferte UTF-8-Dekodierung konnte bei einem ungültigen Byte
  in einem Datensatz sogar das Lesen des gültigen Headers abbrechen.
  Der Import ordnet ungültige Bytes jetzt ihrem Datensatz zu, verwirft
  ihn als `unreadable_row` und erhält Nachbarzeilen sowie mehrzeilige
  CSV-Felder. Die Prüfsumme bleibt auf die Originalbytes bezogen.
  [Importvertrag](../../data/puzzle_packs/README.md)
- W11. Foundation prüft nun die sechs archivierten Snapshots mit den
  abgelegten SHA-256-Werten. Davor war die Prüfdatei vorhanden, die
  Prüfung hing jedoch am einmaligen manuellen Abgleich. Beschädigte
  und fehlende Dateien werden mit der Regression belegt.
  [Archiv](../archive/onedrive-2026-11-21/README.md)
- W00–W12. Code, aktive Paketübersicht, Roadmap, Versionsmarker und
  belegte Teilabnahmen sind abgeglichen. Acht Pakete bleiben `TESTED`,
  vier `IN_PROGRESS` und eines `BLOCKED`. `V.0.0.1` bleibt die
  Entwicklungsfassung. Die [offenen Fragen](../questions/OPEN_QUESTIONS.md)
  und [Paket-Gates](../roadmap/WORK_PACKAGES.md) führen die ausstehenden
  Inhaberentscheidungen.

## Prüfungen

Windows 11 Pro x64 (10.0.26300). Unittest-Läufe mit
`PYTHONWARNINGS=error::ResourceWarning`. Der Gesamtlauf nutzte zusätzlich
`CHESS_AND_CHAINS_REQUIRE_DISPLAY=1` und `PYTHONFAULTHANDLER=1`.

| Prüfung | Ergebnis |
| --- | --- |
| UTF-8-Regression vor der Korrektur | Exitcode 1. Das fehlerhafte Byte der zweiten Zeile führte zum Abbruch beim Einlesen des Headers. |
| `python -m unittest tests.test_puzzles tests.test_foundation -q` und `py -3.14 -m unittest tests.test_puzzles tests.test_foundation -q` | Python 3.15.1 und 3.14.7, je 39 Tests, Exitcode 0. |
| `python -m unittest discover -s tests -q` | Python 3.15.1/Tk 9.0.4, 216 Tests bestanden, Exitcode 0 (90,810 s). |
| Offline-Wheel aus `git archive 5e59383` | `pip wheel --no-deps --no-index --no-build-isolation` und `pip install --no-index --no-deps --target` bestanden. 24 Figuren-SVGs, zwei Figurenatlanten, Marken-SVGs und Fallbacks, Demo-Paket und Paketgrenzen geprüft. `--version` und `--headless-check --board-design` mit der SVG-Vorlage bestanden. Der erste Artefaktprüfer erwartete vier statt der tatsächlich vorgesehenen zwei Figurenatlanten und endete mit Exitcode 1. Der korrigierte Lauf desselben Git-Stands endete mit Exitcode 0. |
| Konsistenz | `verify_starter.py`, `verify_document_links.py`, `check_policy.py`, `python -m compileall -q src app scripts tests` und `git diff --check` jeweils Exitcode 0. |

SHA-256 des lokal installierten Wheels
`27d56a2312473e560c62e60272174e2d2385b047a0724a82f4ab7637fb83f717`.
Der Remote-Head und die endgültigen CI-Ergebnisse werden am Pull Request
protokolliert. [CI-Basis nach PR #10](https://github.com/n05a-design/chess-and-chains/actions/runs/44901076786)

## Verbleibende Arbeit

1. Wiedergabe mit Screenreadern und native Skalierung auf den Zielsystemen.
2. Inhaber-Brettmotive sowie echte Engine, Realdaten und Installer nach den
   dokumentierten Freigaben prüfen.
3. Die fehlerhafte lokale Referenz in der gemeinsamen OneDrive-Git-Ablage
   bleibt aus dem [vorherigen Prüfbericht](2026-11-21_W08-puzzle-seed.md#github-abgleich)
   bekannt. Der Abgleich nutzt den direkt verifizierten Remote-Head.

Für einen Rückweg können die Code-, Test- und Dokucommits des Abgleichs
gemeinsam rückgängig gemacht werden. Datenbanken und Paketformate brauchen
dabei keine Migration.
