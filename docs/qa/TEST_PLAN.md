# QA-Matrix – Foundation / Produkt

Stand **V.0.3.0**. Der [Merge-Lauf von PR #21](https://github.com/n05a-design/chess-and-chains/actions/runs/44972693793)
auf `main` bestand 14 von 14 Jobs. In beiden nativen macOS-Tk-Jobs
blieb die Partie beim Wechsel auf das Marmorbrett und zurück erhalten.
Der Entwicklungsabgleich belegt die Prüfung der
Folgecommits, das installierte Wheel und den Vergleich mit OneDrive.
Die native Windows-Probe für PGN-Dateidialoge, Backup/Restore und
Brettfokus ist separat dokumentiert.
[Entwicklungsabgleich](../reports/2026-11-21_W11-entwicklungsabgleich.md) ·
[W10-Dialogtastatur](../reports/2026-11-21_W10-dialogtastatur.md) ·
[W06-SVG-Brettvorschau](../reports/2026-11-21_W06-svg-brettcache.md)

| Bereich | Testmodul | Umfang des automatisierten Nachweises |
| --- | --- | --- |
| Foundation/Status | `test_foundation`, `scripts/verify_starter.py` | Struktur, Status-Evidenz und Versionskonsistenz über Laufzeit, Paketquelle, Manifest und Einstiegsdokumente. Pfade und Prüfsummen des Assetregisters und OneDrive-Archivs |
| Chess Core | `test_chess_core`, `test_chess_golden` | Perft (Start d4, CPW 2–6), Spiegel-Symmetrie, SAN, PGN-Fehlerfälle, Roundtrips, deklarierte Remisansprüche, Aufgabe gegen blanken König, Matt mit zwei Springern, Wiederholungszähler nach Undo/Redo und Abzweigung, Performance-Budget. Tote Stellungen in kurzen Zwangsfolgen zum Patt oder Materialremis mit Matt und Zugwahl als Gegenproben. [W05-Nachweis](../reports/2026-11-21_W05-mehrzuegige-tote-stellungen.md) |
| UCI | `test_uci_engine` | Nur Mock-Engine; echte Engine NICHT getestet |
| Schachuhr und Zeitablauf | `test_game_clock`, `test_app_integration` | Fischer-Inkrement, Zeitgrenze, kurze beweisbare Mattwege, erzwungener Schlag zum Remis, automatische Remisgrenzen, individuelle Eingabe und PGN-Zeitablauf. [Prüfbericht](../reports/2026-11-27_F03-F06-zeitablauf.md) |
| Bot/Controller | `test_game_controller`, `test_bot_presets` | Vertical Slice, Crash, Timeout, verworfene Suchaufträge, UCI-Partiewechsel, Undo, Shutdown mit Mock-Engine |
| Analyse und Trainingskette | `test_engine_analysis`, `test_training`, `test_app_integration` | Archivieren, offline erneut öffnen, beschädigte Sicherung abweisen. Mattkette nach Hinweis fortsetzen und Lösung genau einmal werten. [Prüfbericht](../reports/2026-11-27_F07-F10-analysearchiv-mattkette.md) |
| Puzzle | `test_puzzles`, `test_app_integration` | Rating ≥ 1000, Setup-Zug-Regression, Importgrenzen, Seed-Auswahl und Demo-Herkunft. Lokale Paketinstallation mit Prüfung von Zugfolgen, parallelen Importen, Fortschrittszuordnung und Neustart. [W08/W09-Prüfnachweis](../reports/2026-11-21_W08-W09-lokale-raetselpakete.md) |
| Storage | `test_storage` | Migration älterer Bibliotheken auf v5, automatische Sitzung, Uhrzustände und Trainingskandidaten, gespeicherte Partieenden, PGN- und FEN-Dateiaustausch, Importgrenzen und atomare Einstellungen. Rücksicherung prüft widersprüchliche Partien vor dem Austausch. Simulierte Schreibfehler und abgebrochener SQLite-Transfer erhalten den aktiven Stand. [FEN-Prüfnachweis](../reports/2026-11-21_W05-W09-fen-austausch.md) · [Rücksicherung](../reports/2026-11-21_W09-sichere-wiederherstellung.md) |
| Windows-Dateiaustausch | Native Dialogprobe und `test_app_integration` | PGN importiert und exportiert, Züge und Event-Tag erneut geprüft, SQLite-Sicherung in ein zweites Testprofil wiederhergestellt. FEN aus isolierten Testdateien geöffnet und gespeichert, Zwischenablage, Bestätigungsabbruch und Spielfortsetzung geprüft. Die FEN-Tests ersetzen die Systemdialoge durch Dateipfade. |
| Materialanzeige | `test_captured_material`, `test_app_integration.CapturedMaterialUiTests` | Regel- und Controller-Tests laufen headless. Brettausrichtung, Undo/Redo und Materialverlauf im Replay laufen in der Tk-Suite. [CI-Korrektur](../reports/2026-11-27_PR25-ci-materialanzeige.md) |
| UI | `test_board_ui`, `test_app_integration` | Brett, Umwandlung, Tastaturfokus, Partie/Rätsel, Original V.06, Draufsicht V.04.2, Klassisch V.05.1, PNG-Fallback sowie UCI-Dialog. Nativ auf Windows/macOS und unter Xvfb auf Linux, jeweils Python 3.11 und 3.14 |
| Marke und Logos | `test_brand_assets`, `scripts/build_brand_assets.py --check`, `test_app_integration.BrandingUiTests`, `test_final_audit`, `test_glide_shell_integration` (Test 26, 31) | Drei Logo-Master unverändert (SHA-256, LF), Rollenzuordnung, Pixelvergleich aller 41 Ableitungen, ICO/ICNS/Favicon vollständig, sichtbare Begrenzung von Logo 01, transparente Aussparungen, Einfärbung in allen Themes und Themenfarben, Logo 02/03 in Originalfarben, Apple-Icon-Raster. Negativfälle: fehlender, geänderter oder beschädigter Master, nicht unterstützte SVG-Funktionen, veraltete, fehlende und unerwartete Ausgaben. [Bericht](../reports/2026-11-26_logo-integration.md) |
| i18n | `test_i18n` | Schlüssel-/Platzhalter-Parität, UI-Abdeckung, eindeutige DE/EN-Bezeichnungen aller Demo-Themen und Fallback für zusätzliche Kennungen |
| Security | `scripts/check_policy.py` | Kein `shell=True`, keine Netzwerk-Imports, keine Engine-Binaries |
| Bedienqualität | `test_app_integration` und Windows-Tk-Probe | Feldfokus, Zug, Unterverwandlung per Eingabetaste und Tab-Wechsel als Regressionen. PGN-Import, Export und Abbruch über den Tastaturdialog samt Fokusrückkehr geprüft. Zugliste, Bibliotheksdialog und Puzzle mit Tk-Textskalierung 100/150/200 % geprüft. Sichtprobe mit 96 nativen Fenster-DPI. Weitere native DPI-/Screenreader-Prüfungen offen. |
| Release | – | NICHT IMPLEMENTIERT |

Lokale Gesamtläufe und Abgrenzung zur CI der Merge-Basis stehen in der [N02-Übergabe](../reports/2026-11-20_N02-follow-up.md).

Nächste QA-Stufe für W10/W11:

Die GUI-Suite enthält Regressionen für erreichbare Spielaktionen bei
200 % Tk-Textskalierung (DE) sowie Tastaturzüge und Tab-Wechsel auf dem
Marmorbrett bei 150 % (EN). Für die native Abnahme gilt das
[Prüfprotokoll](../reports/2026-11-22_W10-W11-bedienabnahme.md).

1. Bei nativen Skalierungsstufen 100/150/200 % prüfen, soweit das jeweilige
   System sie anbietet. OS, Tk-Version, Bildschirmauflösung und effektive
   Skalierung protokollieren.
2. Per Tab und Shift+Tab durch die Anwendung gehen. Einen legalen Zug,
   eine Unterverwandlung, Rückgängig/Wiederholen und ein Demo-Rätsel nur mit
   Tastatur ausführen. Sichtbaren Fokus, Rückkehr aus Dialogen und
   erreichbare Inhalte bei kleinen Fenstern prüfen.
3. Zugliste, Bibliothek und System-Dateidialoge mit dem Screenreader des
   Zielsystems prüfen. Ansagen für Brettfeld, Belegung, Zugstatus und
   Fokuswechsel mit Plattform und Toolversion dokumentieren.
4. Vor der W06-Abnahme die Markierungen und Figuren auf den gelieferten
   Inhaber-SVGs in beiden Brettorientierungen prüfen.

Keine x/100-Testzahlen ohne tatsächlich gemessenen Lauf in einem datierten Bericht.

## Suite-Zuordnung für CI

`python scripts/ci_tests.py inventory` gleicht jedes Testmodul sowie die
pytest-Kollektion mit den produktiven CI-Einträgen ab. Der Runner
`headless` übernimmt unittest-Fachtests, `gui` die fünf nativen Tk-Suiten
in der festgelegten Reihenfolge, und `pytest` die Figurensatz-Gruppe.
Für Inventar und pytest muss pytest installiert sein. Diese Abhängigkeit
gehört zur Entwicklung. Der Workflow startet Tk unter Linux mit Xvfb.
Unerwartete unittest-Skips schlagen in der CI fehl. Seit F01 zugelassene
Ausnahmen stehen direkt im Runner. Die separate native macOS-Panelprobe
bleibt eine Plattformprobe im Workflow. App-Installation, System-Standby,
reale UCI-Engine und physische Bedienhilfen brauchen eigene Abnahmen.
[Prüfbericht zum Entwicklungsbranch](../reports/2026-11-27_F01-F12-functional-core.md)

## Auftrag III – Integrationsnachweise

- `test_engine_registry` prüft lokale Freigaben über Neustarts,
  Binär- und Ressourcenänderungen, Widerruf und Benchmark-Smoketest.
- `test_game_session`, `test_game_clock` und die native Session-Suite
  prüfen Zeitkontrolle, aktive und pausierte Zeit, Konfliktzweige,
  bewusstes Verwerfen und bestätigten Wechsel der Engine.
- `test_storage` prüft Migrationen aus v1–v7, ZIP-Kompatibilität,
  isolierte Engine-Referenzen, Prozessabbruch und unterbrochene Recovery.
- `test_engine_analysis` zählt reale UCI-Befehle des Projekt-Fixtures
  für Cache-Treffer und geänderte Budgets. Separate
  `searchmoves`-Anfragen prüfen beide Zugfarben.
- Die native Archivsuite prüft Labels, Fortsetzung und das Laden
  eines Analyse-Trainingskandidaten nach dem Löschen seiner Quellen.

Die bestehende Actions-Matrix umfasst Windows, macOS und Linux mit
Python 3.11 und 3.14. Lokale Ergebnisse und offene Plattformabnahme
sind im [Auftragsbericht](../reports/2026-11-28_phase-a-completion-phase-b-engine-analysis.md) getrennt.
