# Datenvertrag

Der `src/chess_and_chains/chess/`-Kern ist eine lokale, unveränderliche
Positionsdomäne ohne GUI, UCI oder Dateisystem. `GameState` enthält ein
64-Felder-Tupel, Zugfarbe, Rochaderechte, en-passant-Ziel und FEN-Zähler;
`Move` enthält Quell-/Zielfeld und optionale Umwandlung. `RulesPort` bildet die
typisierte Grenze für Initialposition, legale Züge, Zustandsübergang,
FEN-Konvertierung, positionsidentitätsbasierte Wiederholung und Materialstatus.

Die `ChessGame`-Historie speichert pro Aktion den Positionsübergang und
bei einem Zug den hinzugekommenen Wiederholungsschlüssel. Undo/Redo
ändert die Zähler pro Zug. Aufgabe und Remisansprüche sind eigene Aktionen
ohne Änderung der Zugliste oder Stellung. Eine dreifache Wiederholung und die
50-Züge-Regel sind beanspruchbar; fünffache Wiederholung und 75 Züge sind
automatisch. Eine beanspruchte Remispartie ist von einem noch laufenden Spiel
unterschieden. FEN und PGN werden über die Domainfunktionen geparst/serialisiert;
PGN importiert Tags und die legale Hauptvariante. Kommentare, NAGs und
Nebenvarianten werden beim Einlesen übersprungen und beim Export nicht erzeugt.
Für P-08 ist der Austausch der Hauptvariante nachgewiesen. Verlustfreier
Annotierungsaustausch bleibt eine mögliche Erweiterung nach Scope-Entscheidung.

## Engine

`EngineProfile {id, display_name, executable_path, vendor, detected_uci_options, approved_bundle, license_record}`. Benutzerpfad nie ungeprüft als Shell-Kommando ausführen. Keine direkt in SQLite geschriebenen Engine-Binaries.

## Game

`Game {id, created_at_utc, initial_fen, moves_uci[], optional_pgn, result, time_control, engine_profile_id, schema_version}`. SQLite lädt eine Partie erst, wenn Ausgangs-FEN, UCI-Züge und Ergebnis mit dem validierten PGN übereinstimmen. Die Bibliothek öffnet Spiele lokal für zwei Personen. Aus dem Brett ableitbare Partieenden behalten ihren Grund.

SQLite v3 speichert bei einer lokalen Aufgabe die Farbe der aufgebenden
Person. Bei einem Remisanspruch speichert es die Anspruchsregel und einen
gegebenenfalls angesagten UCI-Zug getrennt von ausgeführten Zügen. Beim
Laden wird das Partieende über die Regeldomäne nachvollzogen und mit dem
gespeicherten PGN-Ergebnis abgeglichen. Ältere Datensätze und PGN-Importe
ohne lokalen Grund behalten ihr allgemeines Ergebnis. Der PGN-Dateiaustausch
transportiert das Ergebnis und die Hauptvariante.

Der Dateiaustausch der Partiebibliothek verarbeitet pro Vorgang genau eine
Partie. Import akzeptiert UTF-8 mit optionalem BOM bis 256 KiB und 512
Halbzügen und speichert erst nach der Validierung. Der Export übernimmt
die gespeicherte Hauptvariante mit Tags und Ergebnis. Die Zieldatei wird
erst nach vollständigem Schreiben im selben Verzeichnis ersetzt.

## Puzzle

`Puzzle {id, source, source_export_date, original_fen, moves_uci[], rating, rating_deviation, popularity, plays, themes[], source_url, checksum}`. Bei Anzeige: `initial_fen -> first opponent move -> player start state`. Solve Progress getrennt: `puzzle_id, attempts, solved, last_attempt_utc, optional duration_ms, hints_used`. Die UI kombiniert Themen-Tags und Ratingbereiche im aktiven Pack. Sie zählt für die Auswahl unterschiedliche gelöste IDs aus dem SQLite-Fortschritt.

## Einstellungen

`Settings {schema_version, locale, theme_id, piece_set_id, board_id, engine_profile_id, data_path}`. App-interne Pfade müssen portabel/migrierbar sein.

**Implementierungsvorschlag N02 (ADR-004 weiterhin PROPOSED):** SQLite `PRAGMA user_version` = 3 (`storage/database.py`: Tabellen `games`, `puzzle_attempts`, View `puzzle_progress`), Settings-JSON `schema_version` 1 (`storage/settings.py`), Puzzle-Packs `schema` 1 (`puzzles/pack.py`: `manifest.json` mit SHA-256 + `puzzles.jsonl` + `import_report.json`). Migrationen sichern bestehende DBs vorher (`*.pre-vN-*.bak`); neuere Schemata bleiben geschützt. Bestätigt beschädigte Dateien werden umbenannt. Bei einer Wiederherstellung wird eine nur lesend geöffnete Sicherung in einer temporären Datenbank geprüft und migriert. Erst danach wird der aktive Stand gesichert und in einer SQLite-Backup-Transaktion ersetzt. Endgültige Festlegung durch Owner über ADR-004.
