# PROMPT 09 – Speicherung, Datenmigration und Benutzerprofile

W09 nach W05/W08. Lokale Dateien außerhalb `site-packages`, Programmordner und Git-Checkout ablegen. Kein ungefragtes OneDrive-Sync oder Nutzerpfad-Hardcoding.

**Konzept:** SQLite (Puzzlestatus, History, Einstellungen ggf. unabhängig), JSON für Appearance, PGN/FEN Import/Export; getrennte katalogseitig unveränderliche Puzzle-Packs und mutable User-Daten. Speicherpfade nach Windows/macOS/XDG, datierte Schema-Migrations, Atomic Writes, Backup/Restore und Beschädigungsdiagnostik. Multi-Profil optional hinter Owner-Frage.

**Tests:** Migration v1→v2, unerwartete Felder, Unicode, Import fehlerhafte PGN/FEN, Session-Save & Reopen, Recovery nach unterbrochenem Schreiben, Dateiberechtigungen, Read-only Orte. Keine persönlichen Daten in CI-Logs. Nutzerdefinierter Cloudordner nicht automatisch Multi-Writer-Synchronisation.

**Deliverables:** Datenverträge, Migration-/Backup-Tests, Dokumentation, W09-Evidenz, ADR-004-Vorschlag.

**Gate:** Abruf und Wiederherstellung sicher, keine Datenlöschung bei Fehler. Nutzerdateien werden bei Tests immer in isolierten temporären Verzeichnissen erzeugt.
