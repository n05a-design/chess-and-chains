# W05 – Mehrzügige tote Stellungen

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Lokaler Branch
`codex/chess-chains-w05-zwangsfolgen`, Basis
`a28599a` aus dem lokalen W08-Folgepaket. Code und Regressionen
stehen in `e9dd8cb11f8cb478e525e90edabb4f0297442050`,
Tree `34a83d3848bfe8c3ac73a6547f80f3940d4aa73b`.
GitHub-`main` stand beim Abgleich auf
`6bcd9ada580be10f289c34dd0040be62297597d2`.

## Regelfall

Art. 5.2.2 beendet eine Partie, sobald keine legale Zugfolge mehr zum
Matt für eine der beiden Seiten führen kann. Die European Chess Union
dokumentiert eine Stellung nach `48. Nc2+`, in der nur
`48... Qxc2+ 49. Kxc2` möglich ist. Die letzte Stellung ist Patt.
Die Regression verwendet die numerische Position aus dem Diagramm,
ihre Farbspiegelung und zwei abgeleitete Gegenbeispiele.
[FIDE-Regelwerk](https://handbook.fide.com/chapter/e012023) ·
[Beispiel der European Chess Union](https://www.europechess.org/dead-position/)

Der Kern prüft bis zu vier Halbzüge voraus, solange jeweils ein Zug
legal ist. Patt und ungenügendes Material belegen ein Remis. Sobald
Zugwahl besteht, greift weiterhin die bereits vorhandene Prüfung,
ob alle Züge unmittelbar durch Schlag in ein Materialremis führen.
Bei einem möglichen Matt oder einer ungeklärten Fortsetzung bleibt
die Partie spielbar. Die feste Tiefe begrenzt den Aufwand beim Auswerten
eines Zuges. Allgemeine verblockte Stellungen und längere oder
verzweigte Folgen bleiben offen.

Die Probe simuliert Züge auf lokalen Brettzuständen. Erst der tatsächlich
gespielte Zug steht in der Partieliste. Historische PGN- und
SQLite-Aufzeichnungen können ihre gespeicherte Fortsetzung mit
`Qxc2+ Kxc2` weiterhin vollständig wiedergeben. Nach Rückgängig zurück in
die tote Stellung greift der neue Live-Status. Puzzle-Sitzungen behalten
ihren früheren Prüfpfad für die vorgegebene Zugfolge.
[Datenvertrag](../architecture/DATA_CONTRACTS.md)

## Lokale Prüfnachweise

Windows 11 Pro x64 (10.0.26300). Für Unittest-Läufe galt
`PYTHONWARNINGS=error::ResourceWarning`. Für den Gesamtlauf galten
außerdem `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1` und
`PYTHONFAULTHANDLER=1`.

| Prüfung | Ergebnis |
| --- | --- |
| Regelfall und SQLite-Wiedergabe vor der Korrektur | Beide Tests schlugen auf der Basis fehl, Exitcode 1. Der Regelkern meldete `ACTIVE` nach `Nc2+` und nach Rückgängig zur selben Stellung. |
| `py -3.14 -m unittest tests.test_chess_golden.TerminationRuleTests tests.test_storage tests.test_puzzles -q` | Python 3.14.7, 60 Tests bestanden, Exitcode 0. Darunter Farbspiegelung, Matt bei erzwungenem Zug, offene Fortsetzung, PGN und SQLite. |
| `python -m unittest discover -s tests -q` | Python 3.15.1/Tk 9.0.4, 212 Tests bestanden, Exitcode 0 (79,822 s). |
| Tk-Probe und Regelmessung (`python -`) | Python 3.15.1/Tk 9.0.4, Exitcode 0. DE/EN-Remismeldung, gesperrte Zugeingabe sowie Rückgängig/Wiederholen geprüft. Bei je 500 alternierenden Aufrufen von `outcome()` lag der Median in der Ausgangsstellung bei 0,248 ms vorher und 0,250 ms nachher. Für den ECU-Regelfall waren es 0,291 ms vorher und 0,637 ms nachher. Die Messung gilt für diese zwei Stellungen auf diesem Rechner. |
| Dokumentation und Policy | `verify_starter.py`, `verify_document_links.py`, `check_policy.py`, `python -m compileall -q src app scripts tests` und `git diff --check` jeweils Exitcode 0. |

## Übergabe

1. Plattform-CI für den lokalen Folgebranch nach der Freigabe des Pushs
   ausführen.
2. Für weitere tote Stellungen prüfbare Beispiele erfassen. Änderungen
   am Suchraum gegen Matt, historische Wiedergabe und Laufzeit absichern.
3. Gesamtregelabnahme weiter nach dem [Paketstatus](../roadmap/WORK_PACKAGES.md)
   führen. W05 bleibt `TESTED` für den belegten Umfang.

Die lokale Änderung kann durch Rücknahme der Code- und Dokucommits
zurückgerollt werden. Datenbankschema und PGN-Format sind unverändert.
