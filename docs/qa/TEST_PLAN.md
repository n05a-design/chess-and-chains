# QA-Matrix – Foundation / Produkt

Stand 2026-11-20. Die Foundation-Prüfungen bleiben grün. Ein unabhängiger,
headless Schachregel-Kern ist implementiert und hat lokale Unit-/Perft-Tests
bestanden; damit sind weder vollständige FIDE-Abnahme noch GUI, Engine,
Offline-Produkt oder Release validiert. Umgebung, Befehle und Grenzen stehen
in `docs/reports/2026-11-20_W05_chess-core.md`.

| Bereich | Testidee | Status |
| --- | --- | --- |
| Starter | JSON-Metadaten und Referenzdateien vorhanden | Test vorgesehen |
| Starter | `__version__` und CLI-Ausgabe | Test vorgesehen |
| Chess Core | Legale Züge, Promotions, Rochaden, EP, Remis, Perft, FEN/PGN, Undo/Redo | Implementiert; 14 gezielte Tests bestanden, Abnahme offen |
| Bot | UCI Handshake, Zeitlimit, Crash, Offline | NICHT IMPLEMENTIERT |
| Puzzle | FEN-vor-Gegnerzug, Ratingfilter, Lösungen, Quellen | NICHT IMPLEMENTIERT |
| UI | SVG, DPI, Hit testing, Keyboard, Kontrast, Fokus | NICHT IMPLEMENTIERT |
| Storage | Save/Load, Migration, Backup Restore | NICHT IMPLEMENTIERT |
| Security | Dateien, Archive, Datenschutz, unbekannte Engine | NICHT IMPLEMENTIERT |
| Release | Native Installer, BOM, Signatur, SHA, isolierter Start | NICHT IMPLEMENTIERT |

Keine x/100-Testzahlen ohne tatsächlich gemessenen Lauf in einem datierten Bericht.
