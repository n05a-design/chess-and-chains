# MVP Contract 0.1 – noch zu bestätigen

Status: **PROPOSED**, nicht abgenommen.

| ID | Nutzerfähigkeit | Akzeptanz | Abhängigkeit |
| --- | --- | --- | --- |
| P-01 | Schachbrett | 64 Felder, Farben/Orientierung, korrekte Koordinaten | W05/W06 |
| P-02 | Regelkonformes Spiel | Schach, Matt, Patt, Rochade, EP, Umwandlung, Remisregeln | W05 |
| P-03 | Offline-Bot | Engine über UCI, Timeout, Fehlerbehandlung, Offline-Test | W07 + ADR Lizenz |
| P-04 | Stärke | 6+ reproduzierbare Presets, keine ungeprüften Elo-Zusagen | W07 |
| P-05 | Rätsel | Rating >= 1000, korrekter Setup-Zug, legale Lösung | W08 |
| P-06 | Fortschritt | Rätselstatus, Fehler, Zeit, lokale Persistenz | W09 |
| P-07 | Design | SVG-Figuren, auswählbare Board-Styles, DPI | W06 |
| P-08 | Export | PGN/FEN Import/Export mit Datenvalidierung | W05/W09 |
| P-09 | Sprache | Deutsch und Englisch, keine hartcodierten Kerntexte | W10 |
| P-10 | Release | Installierbar, Quellen/Lizenzen + Prüfsummen | W11/W12 |

## Release-Blocker

Kein Release bei ungeklärter Vertriebs-Lizenz, illegalen Schachzügen, Crash beim Engine-Tod, beschädigter Datenmigration, Rätseln unter 1000 in ausgelieferter Standardauswahl, nicht belegten Runtime-Komponenten, ungeprüften System-Installationen.

## Änderungsregel

Scope-Änderung erfordert Issue + Owner-ADR. Ein Entwickleragent darf neue Ideen in die Backlog-Liste schreiben, aber nicht heimlich zum MVP hinzufügen.
