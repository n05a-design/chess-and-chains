# W10/W11 – Tastatur, Fokus und Textskalierung

**V.0.0.1 · 21.11.2026 · Windows 11 Pro x64 (10.0.26300) · Codex, KI-gestützt.**
Der Arbeitsbranch `codex/chess-chains-w10-usability` basiert auf
`d72c3f039ae32419233d30d0bca0001dbb04fd5f` (Merge von PR #8 in `main`).
Die Code- und Teständerungen stehen in `a235a9f7c743cce21976cf2ee8e7ce6bef260717`
(Tree `23969d1cb0c2bbbc5f8f7337d0b032693e4bd598`). Der Branch ist als
[PR #9 gegen main](https://github.com/n05a-design/chess-and-chains/pull/9) veröffentlicht.

## Befunde und Änderungen

| Befund | Umsetzung |
| --- | --- |
| Beim ersten Tab-Fokus zeigte das Brett vor einer weiteren Taste kein fokussiertes Feld. | Das Brett fokussiert sofort e2 bzw. e7 bei umgedrehter Perspektive. Beim erneuten Betreten bleibt die zuletzt verwendete Koordinate erhalten. Ein hell-dunkler gestrichelter Rahmen liegt über Brettmotiven, Figuren und Zugmarkierungen und verschwindet beim Verlassen des Bretts. |
| Deutsche UI zeigte englische Brettmeldungen. Vier Umwandlungsoptionen wurden als vier Zielfelder gezählt. | DE/EN-Kataloge liefern Koordinate, Farbe und Figur bzw. leeres Feld sowie die Anzahl unterschiedlicher legaler Zielfelder. Kompakte Statusmeldungen können umbrechen. SAN, PGN und die Zugprüfung verwenden weiterhin dieselben Fachfunktionen. |
| Die Eingabetaste funktionierte auf den Aktionsbuttons des Spiels und der Umwandlung nicht durchgängig. Die Zugliste hatte dieselbe Fokus- und Hintergrundkontur. | Aktionsbuttons unterstützen Enter und Ziffernblock-Enter. Aktionsbuttons und Zugliste erhalten einen blauen Fokusrahmen. Die Tableiste spart den rechten Abstand hinter dem letzten Tab. In der Vorprobe bei 200 % und englischem Rätseltab fehlte in jeder Tabzelle ein Pixel gegenüber der von Tk angeforderten Breite. |

## Prüfungen

| Prüfung | Umgebung und Ergebnis |
| --- | --- |
| `python -m unittest discover -s tests -v` | Python 3.15.1, Tk 9.0.4, verpflichtendes Tk-Display und `ResourceWarning` als Fehler. **191 bestanden**, keine Skips, Exitcode 0. |
| `py -3.14 -c "import faulthandler, unittest; faulthandler.dump_traceback_later(90, exit=True); unittest.main(module=None)" tests.test_board_ui tests.test_app_integration -q` | Python 3.14.7/Tk 9.0.4 mit denselben Prüfvariablen. **53 bestanden**, keine Skips, Exitcode 0. |
| Tk-Tastatur- und Fensterprobe | Python 3.15.1/Tk 9.0.4, DE und EN bei intern 96/144/192 px pro Zoll, festes Fenster 860 × 700 px. **6 Kombinationen bestanden**, Exitcode 0. |
| Installiertes Wheel und SVG-Brett (W06/W11) | Python 3.15.1/Tk 9.0.4, isolierte Installation aus dem eingefrorenen Tree, Exitcode 0. |
| `python scripts/verify_starter.py`, `python scripts/verify_document_links.py`, `python scripts/check_policy.py`, `python -m compileall -q src app scripts tests`, `git diff --check` | Versionskonsistenz, relative Dokumentpfade, Policy, Kompilierung und Diff-Format. Alle Exitcode 0. Der Nachlauf `python -m unittest tests.test_foundation tests.test_i18n -q` bestand **18 Tests**, Exitcode 0. |
| GitHub-CI der Merge-Basis | `gh run list` und `gh run view 44845219578`, Exitcode 0. Der [separate Lauf zu PR #8 auf main](https://github.com/n05a-design/chess-and-chains/actions/runs/44845219578) hatte **14/14 erfolgreiche Jobs**, einschließlich nativer macOS-GUI mit Python 3.11 und 3.14. Dieser Lauf gehört zum Merge-Commit auf `main`. |

Für den lokalen Gesamtlauf waren `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`,
`PYTHONWARNINGS=error::ResourceWarning` und `PYTHONFAULTHANDLER=1` gesetzt.
Die Dauerregressionen üben Feldfokus, Zugausführung und Tab-Wechsel sowie
`a7a8r` mit Eingabetaste und einem legalen Zielfeld aus.

Für die Fensterprobe wurde vor dem App-Aufbau `tk scaling` auf
`4/3`, `2` und `8/3` gesetzt. `winfo_fpixels("1i")` bestätigte
96, 144 und 192. Die Tk-Ereignisse deckten `e2e4`, Rückgängig,
Wiederholen, Bibliothek öffnen und Escape mit fokussierter Schaltfläche
nach der Rückkehr, Tab-Wechsel, Zugliste, die Lösung des ersten
Demo-Rätsels und die Sichtbarkeit des Ratingfilters ab. In allen sechs
Läufen war ein Standardbrettfeld 45,5 px groß. Tk meldete ausreichend
Breite für alle Tabs. Die Probe startete ausgewählte Pfade mit gesetztem
Fokus und verwendete für lokale Daten jeweils ein temporäres Verzeichnis.
Die absoluten DPI-Werte bezeichnen Tk-Textskalierung bei gleicher
Pixelgröße des Fensters. Native Systemskalierung und Bildschirmsicht
stehen zur Abnahme aus.

Aus dem Git-Tree wurde
`pip wheel --no-build-isolation --no-deps --no-index --wheel-dir <Temp> .`
ausgeführt. `pip install --no-deps --no-index --target <Temp> <Wheel>`
installierte `chess_and_chains-0.0.1-py3-none-any.whl` separat. Installierte
Metadaten und Laufzeitversion lieferten `0.0.1`. `--version` und
`--headless-check --board-design <SVG-Vorlage>` meldeten V.0.0.1.
Die installierte GUI lud die [projektinterne SVG-Brettvorlage](../../assets/boards/source/board-template.svg)
bei 200 % Tk-Textskalierung und zeigte Tastaturfokus, `e2e4`,
Perspektivwechsel und Rätsel sowohl mit Vorderansicht V.02 als auch mit
Draufsicht. SHA-256 des geprüften Wheels
`bb8d50962c713695cd5f313ace52cc8d68ff32cb8c0440d0f24b2ce1207dbdcb`.
Die erste Ausführung baute und installierte das Wheel erfolgreich und
brach im GUI-Prüfskript wegen eines falschen Konstruktorarguments ab.
Der korrigierte GUI-Aufruf bestand aus einem neuen Build desselben Trees.

## Native macOS-CI auf PR #9

Im ersten [Push-Job auf macOS mit Python 3.14.10](https://github.com/n05a-design/chess-and-chains/actions/runs/44861119209/job/136714495083)
scheiterte der neue Unterverwandlungstest. Der Test hatte nach einem
festen Timer ein synthetisches Enter gesendet und die Partie blieb beim
Ausgangsstand. Der [parallele PR-Lauf](https://github.com/n05a-design/chess-and-chains/actions/runs/44861165625)
bestand denselben macOS-GUI-Job. Der Korrekturlauf wartet im Test auf einen
sichtbaren Button mit tatsächlichem Tk-Fokus, stellt Enter in die
Ereigniswarteschlange und räumt die befristeten Callbacks auf. Die
Prüfung der Unterverwandlung und der Zielfeldanzahl bleibt bestehen.

## Gemessene Farbpaare

Die Werte sind berechnete sRGB-Kontrastverhältnisse aus der Standardpalette.
3:1 dient bei Fokusmarkierungen als Prüfreferenz. [W3C, Nicht-Text-Kontrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)

| Vordergrund und Hintergrund | Verhältnis |
| --- | --- |
| Dunkler Fokus / Papier `#171920` / `#FAF6EC` | 16,26:1 |
| Dunkler Fokus / helles Standardfeld `#171920` / `#ECE2CA` | 13,62:1 |
| Dunkler Fokus / dunkles Standardfeld `#171920` / `#8D7862` | 4,18:1 |
| Heller Fokus / dunkles Standardfeld `#FAF6EC` / `#8D7862` | 3,90:1 |
| Blauer Fokus / Papier und Gelb `#2447D8` / `#FAF6EC`, `#F4C400` | 6,56:1 / 4,29:1 |
| Text / Panel `#171920` / `#FFFCF4` | 17,12:1 |
| Status-/Sekundärtext / Panel `#514B44` / `#FFFCF4` | 8,40:1 |

## Nächste Abnahmen

1. W10/W11. Den neuen Code auf macOS und unter Linux in der GUI-CI prüfen.
   Auf den Zielsystemen bei nativer Skalierung Tab und Shift+Tab, Zugliste,
   Rätsel, Dialoge sowie Öffnen/Speichern über die Systemdialoge prüfen.
   Screenreader-Ausgaben für Brettkoordinate, Figur, Zugstatus, Liste und
   Modalfokus mit tatsächlichen Tools erfassen. Die sichtbare Tk-Statuszeile
   belegt noch keine Ansagen für einzelne Canvas-Felder.
2. W06. Finale Inhaber-SVGs nach Eingang mit beiden Figurensätzen testen.
   Kontrast, Auswahl, Orientierung und Feldzuordnung motivbezogen abnehmen.
3. W11/W12. Native Offline-Erstinstallation und Upgrade prüfen, sobald
   passende freigegebene Installer vorliegen. Weitere Voraussetzungen
   stehen in der [Roadmap](../roadmap/ROADMAP.md).

W10 bleibt `IN_PROGRESS`. W11 ist für die in der
[QA-Matrix](../qa/TEST_PLAN.md) belegten automatisierten Abläufe `TESTED`.
Die Änderungen führen keine Laufzeitabhängigkeiten, neuen Assets oder
Datenschemata ein. Für einen Rollback lässt sich der lokale Code-Commit
revertieren und der Stand in Roadmap und QA-Matrix zurückführen.
