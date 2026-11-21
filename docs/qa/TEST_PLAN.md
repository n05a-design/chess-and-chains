# QA-Matrix – Foundation / Produkt

Stand **V.0.0.1**. Der Merge von PR #10 auf `main` bestand die
Plattformmatrix. Der Entwicklungsabgleich belegt die Prüfung der
Folgecommits, das installierte Wheel und den Vergleich mit OneDrive.
Die native Windows-Probe für PGN-Dateidialoge, Backup/Restore und
Brettfokus ist separat dokumentiert.
[Entwicklungsabgleich](../reports/2026-11-21_W11-entwicklungsabgleich.md) ·
[Paketabgleich](../reports/2026-11-21_W00-W12-paketabgleich.md)

| Bereich | Testmodul | Umfang des automatisierten Nachweises |
| --- | --- | --- |
| Foundation/Status | `test_foundation`, `scripts/verify_starter.py` | Struktur, Status-Evidenz und Versionskonsistenz über Laufzeit, Paketquelle, Manifest und Einstiegsdokumente. Pfade und Prüfsummen des Assetregisters und OneDrive-Archivs |
| Chess Core | `test_chess_core`, `test_chess_golden` | Perft (Start d4, CPW 2–6), Spiegel-Symmetrie, SAN, PGN-Fehlerfälle, Roundtrips, deklarierte Remisansprüche, Aufgabe gegen blanken König, Matt mit zwei Springern, Wiederholungszähler nach Undo/Redo und Abzweigung, Performance-Budget. Tote Stellungen in kurzen Zwangsfolgen zum Patt oder Materialremis mit Matt und Zugwahl als Gegenproben. [W05-Nachweis](../reports/2026-11-21_W05-mehrzuegige-tote-stellungen.md) |
| UCI | `test_uci_engine` | Nur Mock-Engine; echte Engine NICHT getestet |
| Bot/Controller | `test_game_controller`, `test_bot_presets` | Vertical Slice, Crash, Timeout, verworfene Suchaufträge, UCI-Partiewechsel, Undo, Shutdown mit Mock-Engine |
| Puzzle | `test_puzzles`, `test_app_integration` | Rating ≥ 1000, Setup-Zug-Regression, Duplikate, Importgrenzen, Seed-Auswahl, Demo-Herkunft, Packs und Session. Themen-/Ratingfilter, DE/EN-Themenanzeige und gespeicherter Fortschritt mit projekteigenen Fixtures. [W08-Prüfnachweis](../reports/2026-11-21_W08-puzzle-seed.md) |
| Storage | `test_storage` | Migration v1/v2→v3, gespeicherte Partieenden, PGN-Dateiaustausch, Importgrenzen und atomare Einstellungen. Rücksicherung prüft widersprüchliche Partien vor dem Austausch. Simulierte Schreibfehler und abgebrochener SQLite-Transfer erhalten den aktiven Stand. [W09-Prüfnachweis](../reports/2026-11-21_W09-sichere-wiederherstellung.md) |
| Windows-Dateiaustausch | Native Dialogprobe | PGN importiert und exportiert, Züge und Event-Tag erneut geprüft, SQLite-Sicherung in ein zweites Testprofil wiederhergestellt. |
| UI | `test_board_ui`, `test_app_integration` | Brett, Umwandlung, Tastaturfokus, Partie/Rätsel, V.02 und Draufsicht, PNG-Fallback sowie UCI-Dialog. Nativ auf Windows/macOS und unter Xvfb auf Linux, jeweils Python 3.11 und 3.14 |
| i18n | `test_i18n` | Schlüssel-/Platzhalter-Parität, UI-Abdeckung, eindeutige DE/EN-Bezeichnungen aller Demo-Themen und Fallback für zusätzliche Kennungen |
| Security | `scripts/check_policy.py` | Kein `shell=True`, keine Netzwerk-Imports, keine Engine-Binaries |
| Bedienqualität | `test_app_integration` und Windows-Tk-Probe | Feldfokus, Zug, Unterverwandlung per Eingabetaste und Tab-Wechsel als Regressionen. Zugliste, Bibliotheksdialog und Puzzle mit Tk-Textskalierung 100/150/200 % geprüft. Sichtprobe mit 96 nativen Fenster-DPI. Weitere native DPI-/Screenreader-Prüfungen offen. |
| Release | – | NICHT IMPLEMENTIERT |

Lokale Gesamtläufe und Abgrenzung zur CI der Merge-Basis stehen in der [N02-Übergabe](../reports/2026-11-20_N02-follow-up.md).

Nächste QA-Stufe für W10/W11:

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
