# ADR-004 – Lokale Daten und Formate

**Status: PROPOSED**.

SQLite für Puzzle-Index und Nutzerfortschritt; JSON für Einstellungen; PGN/FEN für interoperable Partien. App-Daten nicht neben der Installation oder im Repo schreiben. Backups/Atomizität/Migration versionieren. Auf Plattformen OS-gerechte AppData/Application Support/XDG-Pfade; Speicherpfade, Profile und Cloudablagen nie still annehmen.

Rätselkatalog (read-only, versioniert) getrennt von Nutzerprofilen und Solve-History halten. Kein Online-Konto, keine ungefragte Telemetrie. Importierte untrusted PGNs und Archivdateien begrenzen/validieren.
