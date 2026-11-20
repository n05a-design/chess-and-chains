# QA-Matrix – Foundation / Produkt

Stand 2026-11-20. Die Foundation-Prüfungen bleiben grün. Ein unabhängiger,
headless Schachregel-Kern ist implementiert und hat lokale Unit-/Perft-Tests
bestanden; damit sind weder vollständige FIDE-Abnahme noch GUI, Engine,
Offline-Produkt oder Release validiert. Umgebung, Befehle und Grenzen stehen
in `docs/reports/2026-11-20_W05_chess-core.md`.

| Bereich | Testidee | Status |
| --- | --- | --- |
| Bereich | Testmodul | Status (N02, lokal macOS arm64, Python 3.14.5) |
| --- | --- | --- |
| Foundation/Status | `test_foundation`, `scripts/verify_starter.py` | Evidenzbasiertes Statusmodell geprüft |
| Chess Core | `test_chess_core`, `test_chess_golden` | Perft (Start d4, CPW 2–6), Spiegel-Symmetrie, SAN, PGN-Fehlerfälle, Roundtrips, Performance-Budget |
| UCI | `test_uci_engine` | Nur Mock-Engine; echte Engine NICHT getestet |
| Bot/Controller | `test_game_controller`, `test_bot_presets` | Vertical Slice, Crash, Timeout, Stale-Results, Undo, Shutdown; Mock-Engine |
| Puzzle | `test_puzzles` | Rating ≥ 1000, Setup-Zug-Regression, Duplikate, Packs, Session; nur projekteigene Fixtures |
| Storage | `test_storage` | Migration, Backup/Restore, Korruption, Settings; nur Temp-Verzeichnisse |
| UI | `test_board_ui`, `test_app_integration` | Tk-Integration inkl. Event-Loop-Latenz; nativ nur macOS; Linux via Xvfb in CI vorgesehen |
| i18n | `test_i18n` | Schlüssel-/Platzhalter-Parität, UI-Abdeckung |
| Security | `scripts/check_policy.py` | Kein `shell=True`, keine Netzwerk-Imports, keine Engine-Binaries |
| Accessibility | – | Tastatur teilweise getestet; Kontrast/Screenreader/High-DPI OFFEN |
| Release | – | NICHT IMPLEMENTIERT |

Lokale Gesamtläufe: siehe `docs/reports/2026-11-20_N02_functional-core.md`. CI-Ergebnisse erst nach Push belegbar.

Keine x/100-Testzahlen ohne tatsächlich gemessenen Lauf in einem datierten Bericht.
