# W06 · Lokale Vorschau für SVG-Bretter

**20.11.2026 · KI-unterstützt · Windows 11 x64.**

## Basis und Umfang

Lokaler Branch `codex/chess-and-chains-owner-design` auf `b81cced92656521e3eb4ee699faf21964840fe5e`, beim Start mit `git ls-remote --symref origin HEAD` gegen GitHub-`main` abgeglichen. Die Originalfiguren und die früheren Inhaberentscheidungen lagen bereits im lokalen Arbeitsbaum. Die Brettablage enthielt die SVG-Vorlage. In den bereitgestellten Quellen wurde kein neuer Brettentwurf gefunden.

**IMPLEMENTED im lokalen Arbeitsbaum.** Der opt-in Aufruf `--board-design` zeigt ein lokales Gesamtbrett, zwei Grundfelder mit optionalen Sonderfeldern oder alle 64 benannten Feld-SVGs. Elemente werden mit Tk 9 aus Vektordaten gerendert. Ein Gesamtbrett rotiert beim Drehen um 180 Grad. Feld-SVGs bleiben aufrecht und folgen der benannten Schachkoordinate. Der vorberechnete Hintergrund wird zwischen den Standardfeldern und den Interaktionsmarkierungen gezeichnet und bei unveränderter Größe und Perspektive wiederverwendet.

Der normale Start nutzt weiterhin die bestehende Brettdarstellung. Die Vorschau übernimmt keine Dateien in ein Paket oder in Einstellungen und lässt die SVG-Quellen unverändert. Die Vorschau prüft die SVG-Struktur vor dem Zeichnen und erwartet für diesen ersten Umsetzungsschritt den in der [Lieferanleitung](../../assets/boards/source/README.md) beschriebenen SVG-Umfang. Es gibt keine zusätzliche Laufzeitbibliothek.

## Nachweise

| Stand bzw. Befehl | Ergebnis |
| --- | --- |
| Ausgangsstand mit Originalfiguren · gestarteter `python -m unittest discover -s tests -v` vor der Vorschau-Implementierung, Python 3.15.1 / Tk 9.0.4, `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`, `PYTHONWARNINGS=error::ResourceWarning` | 174 Tests in 90,663 s, Exitcode 0. |
| `python -m unittest tests.test_board_ui -v` in derselben Umgebung | 16 Tests in 0,883 s, Exitcode 0. Enthält die Formate, fehlerhafte Eingaben, Perspektive, Cache und Darstellungsebenen. |
| `python -m chess_and_chains --headless-check --board-design assets/boards/source/board-template.svg` mit `PYTHONPATH=src` | Exitcode 0. Der Startweg liest und prüft die SVG-Vorlage ohne Fenster. |
| `python %TEMP%/chess-chains-board-preview-smoke.py` · Tk 9.0.4 mit sichtbarem Fenster, isoliertem Testprofil und aus dem Entwicklerstart geöffneter App | Exitcode 0. Gesamtbrett, Grundfelder mit Sonderfeld und 64 Einzeldateien. Jeweils Stellungsaufbau, Zug e2–e4, Perspektivwechsel, Rätselmodus und Größenwechsel geprüft. Asymmetrisches Sonderfeld per Pixelprobe geprüft. Die Vorlage blieb bytegleich. Die Testmotive sind synthetische QA-Eingaben. |
| Gesamtlauf auf `b81cced` plus lokalen Änderungen · `python -m unittest discover -s tests -v`, Python 3.15.1 / Tk 9.0.4 mit denselben Umgebungsvariablen | 179 Tests in 98,072 s, keine Skips, Exitcode 0. |
| Zweite Python-Version · `py -3.14 -m unittest tests.test_board_ui tests.test_app_integration -q`, Python 3.14.7 / Tk 9.0.4 mit denselben Umgebungsvariablen | 45 Tests in 15,202 s, keine Skips, Exitcode 0. |
| Offline-Wheel · `python -m pip wheel --no-build-isolation --no-deps --no-index --wheel-dir <Temp> .`, `python -m pip install --no-index --no-deps --target <Temp> <Wheel>` | Exitcode 0. Installierte CLI prüfte die Vorlage mit `--headless-check --board-design`. Das installierte Paket zeichnete ihr Raster nativ in Tk 9, mit passenden Farben in der Pixelprobe. SHA-256 `2f9033c03f7873c3cdfbbe7de72b8899a7430f11bc95269c5dc78e78b079d45a`. |
| Ungültiger Pfad · `python -m chess_and_chains --board-design <fehlende-SVG-Datei>` | Erwarteter Exitcode 2 mit verständlicher Pfadmeldung vor Fensterstart. |
| Statische Prüfungen · `python scripts/verify_document_links.py`, `python scripts/verify_starter.py`, `python scripts/check_policy.py`, `python -m compileall -q src app scripts tests`, `git diff --check` | Jeweils Exitcode 0. |

## Übergabe

1. Sobald ein Brettentwurf vom Inhaber vorliegt, SVG-Export in der Vorschau prüfen und Auswahl, Lesbarkeit sowie Schachgebot mit den tatsächlichen Motiven beurteilen.
2. Nach Sichtprüfung des Entwurfs den Standardsatz bzw. die spätere Themenauswahl entscheiden und auf den Zielplattformen abnehmen.

Der Inhaber hat den Push des vollständigen lokalen Design-Branches und einen Pull Request gegen `main` mit CI-Prüfung beauftragt. Der Pull Request hält Commit, nachgelagerte CI-Ergebnisse und Review-Grenzen fest. Der optionale Aufruf lässt sich ohne Datenmigration zurückbauen. Die Masterdateien und Spielstände bleiben dabei erhalten.
