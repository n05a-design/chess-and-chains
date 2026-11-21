# W08 – Reproduzierbare Auswahl der Rätsel

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Lokaler Branch
`codex/chess-chains-w08-seed-auswahl` auf dem W05-Stand
`dca174bdc855865bf693ab1a69a86dea44d122a6`. Code und Tests stehen im
Commit `daa38ea4127d858f6acfd671452eafa0ee5cd16b`, Tree
`86635fce63b28afd9b9ab3e43ec7a410d7a2b079`.

## Umsetzung

Der Offline-Builder akzeptiert `--seed` zusammen mit einem positiven
`--limit`. Er liest die ganze Quelle, prüft dieselben Qualitätsgrenzen
wie der bisherige Import und sortiert die ausgewählte Teilmenge nach
dem SHA-256-Rang von `seed:id`. Die Auswahlpufferung ist durch das
Limit begrenzt. Die bestehende Duplikatprüfung braucht weiterhin
Speicher proportional zur Anzahl der unterschiedlichen Quell-IDs.

Der Importbericht speichert Strategie, Seed, Limit, Stichprobengröße und
die Prüfsumme der vollständigen CSV. `accepted` bleibt die Zahl aller
validierten Aufgaben. Ohne Seed gilt weiter Quellreihenfolge und bei
erreichtem Limit der vorzeitige Abbruch. Die zusätzliche Berichtstruktur
verändert weder die JSONL-Datensätze des vorhandenen Demo-Pakets noch
Paket-Schema 1 und SQLite.
[Befehlsreferenz](../../data/puzzle_packs/README.md)

## Lokale Prüfungen

Windows 11 Pro x64 (10.0.26300). Die gezielten und vollständigen
Unittest-Läufe verwendeten `PYTHONWARNINGS=error::ResourceWarning`.
Der Gesamtlauf erzwang zusätzlich ein Tk-Display und aktivierte
`PYTHONFAULTHANDLER=1`.

| Prüfung | Ergebnis |
| --- | --- |
| Regression der Seed-Auswahl auf `dca174b` | Exitcode 1. Der bisherige Importer kannte das Seed-Argument noch nicht. |
| `python -m unittest tests.test_puzzles tests.test_i18n -q` | Python 3.15.1, 31 Tests bestanden, Exitcode 0. |
| `py -3.14 -m unittest tests.test_puzzles -q` | Python 3.14.7, 23 Tests bestanden, Exitcode 0. |
| `scripts/build_puzzle_pack.py` mit der Demo-CSV und einer lokalen Zstandard-Kopie | Seed 17, Limit 2, fünf gültige Zeilen. Beide Eingaben lieferten dieselben zwei Aufgaben `ccFM01` und `ccSM02` und die vollständige CSV-Prüfsumme. Die CSV lieferte unter Python 3.14.7 und 3.15.1 denselben JSONL-Hash `96856a0e8bf91851c1ca47f8e3c700494366813c9248d180c47d4381ae163d56`. Alle positiven Aufrufe Exitcode 0. Aufrufe ohne Limit endeten mit Exitcode 2 und erhielten die bestehende JSONL-Datei. |
| `python -m unittest discover -s tests -q` | Python 3.15.1/Tk 9.0.4, 214 Tests bestanden, Exitcode 0 (79,784 s). |
| Dokumentation und Policy | `verify_starter.py`, `verify_document_links.py`, `check_policy.py`, `python -m compileall -q src app scripts tests` und `git diff --check` jeweils Exitcode 0. `python -m unittest tests.test_foundation -q` bestand 14 Tests, Exitcode 0. |

## GitHub-Abgleich

GitHub meldete PR #10 als gemergt. `main` steht beim Abgleich auf
`e84ad181f0c1ce25e792f96164fb47f5580f499b`. Sein Tree ist mit dem
PR-Head `c0b9b20bb6c0bd0447bb50389df71a38c687e905` identisch.
Der [Merge-Lauf](https://github.com/n05a-design/chess-and-chains/actions/runs/44901076786)
bestand 14 von 14 Jobs, einschließlich nativer macOS-Tk-Jobs für Python
3.11 und 3.14. Dieser Nachweis gilt für `main`.

`git fetch` scheiterte an der lokalen Referenz
`refs/remotes/origin/main-MacBook Pro Max Ultra` in der gemeinsamen
OneDrive-Git-Ablage (Exitcode 1). Das Merge-Objekt war lokal lesbar.
Nach Abgleich von Commit, Eltern und Tree mit GitHub wurde der
Tracking-Verweis `origin/main` gezielt aktualisiert (Exitcode 0).
Die fehlerhafte Referenz bleibt separat zu bereinigen.

## Übergabe

1. Plattform-CI für die lokalen Folgecommits nach Freigabe des Pushs
   ausführen.
2. Nach Q-022 den realen Export lokal prüfen. Datenprofil, Fehlerrate,
   Laufzeit, Speicherbedarf und Zusammensetzung der Auswahl festhalten.
3. Grenzwerte, Seed und Größe eines Produktpakets anhand dieser Daten
   bestimmen. Q-008/Q-009 und ADR-003 bleiben offen.
   [Entscheidungsregister](../questions/OPEN_QUESTIONS.md)

W08 bleibt `TESTED` für die projekteigenen Fixtures. Code und
zugehörige Dokumentation lassen sich gemeinsam zurücknehmen. Der
Rollback erfordert keine Datenmigration.
