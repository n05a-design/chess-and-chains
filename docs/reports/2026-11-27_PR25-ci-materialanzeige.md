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
