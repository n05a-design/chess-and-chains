# QA-Matrix – Foundation / Produkt

Stand **V.0.0.1**. Die automatisierte Plattformmatrix für PR #7 und seinen
Merge auf `main` bestand. Die Matrix unten beschreibt die geprüften Pfade.
Manuelle Windows-/macOS-/Linux-Sichtprüfungen, ein Test mit echter Engine und
Installerabnahmen sind eigene Nachweise. [Standabgleich](../reports/2026-11-21_W11-v0.0.1-standsaudit.md)

| Bereich | Testmodul | Umfang des automatisierten Nachweises |
| --- | --- | --- |
| Foundation/Status | `test_foundation`, `scripts/verify_starter.py` | Struktur, Status-Evidenz und Versionskonsistenz über Laufzeit, Paketquelle, Manifest und Einstiegsdokumente |
| Chess Core | `test_chess_core`, `test_chess_golden` | Perft (Start d4, CPW 2–6), Spiegel-Symmetrie, SAN, PGN-Fehlerfälle, Roundtrips, deklarierte Remisansprüche, Aufgabe gegen blanken König, Matt mit zwei Springern, Wiederholungszähler nach Undo/Redo und Abzweigung, Performance-Budget |
| UCI | `test_uci_engine` | Nur Mock-Engine; echte Engine NICHT getestet |
| Bot/Controller | `test_game_controller`, `test_bot_presets` | Vertical Slice, Crash, Timeout, verworfene Suchaufträge, UCI-Partiewechsel, Undo, Shutdown mit Mock-Engine |
| Puzzle | `test_puzzles` | Rating ≥ 1000, Setup-Zug-Regression, Duplikate, Packs, Session, Themen-/Ratingfilter und gespeicherter Fortschritt mit projekteigenen Fixtures |
| Storage | `test_storage` | Migration v1/v2→v3, Speichern der Terminierung, Backup/Restore inklusive Version 2 sowie fremder und fehlender Sicherungen, beschädigte Partiedaten, PGN-Datei-Roundtrip, Importgrenzen, atomarer Export und Settings in Temp-Verzeichnissen |
| UI | `test_board_ui`, `test_app_integration` | Brett, Umwandlung, Tastaturfokus, Partie/Rätsel, V.02 und Draufsicht, PNG-Fallback sowie UCI-Dialog. Nativ auf Windows/macOS und unter Xvfb auf Linux, jeweils Python 3.11 und 3.14 |
| i18n | `test_i18n` | Schlüssel-/Platzhalter-Parität, UI-Abdeckung |
| Security | `scripts/check_policy.py` | Kein `shell=True`, keine Netzwerk-Imports, keine Engine-Binaries |
| Accessibility | – | Tastatur teilweise getestet; Kontrast/Screenreader/High-DPI OFFEN |
| Release | – | NICHT IMPLEMENTIERT |

Lokale Gesamtläufe und Abgrenzung zur CI der Merge-Basis stehen in der [N02-Übergabe](../reports/2026-11-20_N02-follow-up.md).

Nächste QA-Stufe sind native Tastatur-, Kontrast-, Screenreader- und
Skalierungsproben bei 100/150/200 % mit dem versionierten Prototyp.

Keine x/100-Testzahlen ohne tatsächlich gemessenen Lauf in einem datierten Bericht.
