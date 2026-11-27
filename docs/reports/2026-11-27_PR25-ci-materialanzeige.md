# PR #25 · Tk-Tests der Materialanzeige in der GUI-Suite

**27.11.2026 · Ausgangspunkt `5c5ba3d`.**

## Ursache und Korrektur

Der Linux-Headless-Job lief unter Python 3.11 und 3.14 mit Exitcode 1 aus. `tests.test_captured_material` enthielt vier Tests, die einen Tk-Root für die Materialanzeige und Partiewiedergabe anlegen. Auf dem Headless-Runner fehlte `DISPLAY`. Der CI-Runner meldete die vier unerwarteten Skips und beendete den Job. [Ursprünglicher PR-Lauf](https://github.com/n05a-design/chess-and-chains/actions/runs/46072490541)

Die vier Tests liegen jetzt bei `tests.test_app_integration.CapturedMaterialUiTests` und verwenden das gemeinsame Tk-Testsetup. Der Workflow führt diese Suite unter Linux mit Xvfb und auf macOS und Windows nativ aus. Die 13 Regel- und Controller-Tests verbleiben in `tests.test_captured_material`. Die Skip-Prüfung des CI-Runners bleibt aktiv.

## Nachweise

macOS arm64, Python 3.14.5, temporäre App-Daten, Tk-Anzeige für die GUI-Suite erforderlich.

- `python3 -m unittest tests.test_captured_material tests.test_app_integration.CapturedMaterialUiTests -q` — 17/17, Exitcode 0.
- `python3 scripts/ci_tests.py inventory` — 447 Tests erkannt. Die vier Tk-Fälle wurden im App-Integrationsmodul erfasst.
- `scripts/ci_tests.py headless` mit gesperrtem `tkinter.Tk` — 285/285, Exitcode 0.
- `python3 -X faulthandler -m unittest discover -s tests -v` mit aktiver Tk-Anzeige — 436/436, Exitcode 0. Beide Glide-Shell-Selbsttests meldeten 13/13.
- `python3 scripts/ci_tests.py pytest` — 11/11, Exitcode 0. Struktur-, Link-, Policy-, Compile- und Headless-CLI-Prüfungen ebenfalls mit Exitcode 0.

KI-unterstützte Korrektur. Der Patch betrifft ausschließlich Testzuordnung, Test-Fixture und Dokumentation.

## Zweiter Befund im Engine-Dialog

Der Push-Lauf für `fce085a` meldete unter macOS und Python 3.14 einen falschen Änderungsalarm beim UCI-Bereitschaftstest. Das GUI-Test-Fixture ersetzte vorübergehend die Klassenmethode `EngineConfig.from_path`. Der Hintergrundthread konnte dieselbe ersetzte Methode aufrufen und statt des aufgelösten Executable-Pfads den Python-Symlink aus dem Fixture erhalten. Die Korrektur ersetzt ausschließlich die Auswahl im Dialog. Der Worker verwendet die reguläre Auflösung und Fingerabdruckprüfung. [Fehlgeschlagener macOS-Job](https://github.com/n05a-design/chess-and-chains/actions/runs/46073138709/job/140754569607)

Elf gezielte Tk- und Registry-Tests sowie eine separate Wiederholung des Dialogtests mit einem temporären Python-Symlink bestanden lokal unter macOS mit Python 3.14.5.

## Abbruchprüfung unter Windows

Im PR-Lauf für `5ed1c04` bestanden 13 von 14 Jobs. Windows mit Python 3.11 überschritt im Integrationstest der unkooperativen UCI-Engine die fünf Sekunden Wartezeit auf die Worker- und Prozessbereinigung. Der separat geprüfte UCI-Stop-Timeout bleibt bei einer Sekunde. Eine kontrollierte Uhr prüft diese Frist unabhängig vom Runner. Der Subprozesstest behält die Prüfung des Stop-Kommandos und des erzwungenen Endes bei und erlaubt 15 Sekunden für die Bereinigung. [Windows-Job](https://github.com/n05a-design/chess-and-chains/actions/runs/46073389006/job/140755470333)

Die 31 UCI- und Analysetests liefen lokal mit Exitcode 0. Das CI-Inventar erkannte 448 Tests.
