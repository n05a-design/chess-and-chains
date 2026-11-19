# Datenvertrag (Entwurf, kein Schema implementiert)

## Engine

`EngineProfile {id, display_name, executable_path, vendor, detected_uci_options, approved_bundle, license_record}`. Benutzerpfad nie ungeprüft als Shell-Kommando ausführen. Keine direkt in SQLite geschriebenen Engine-Binaries.

## Game

`Game {id, created_at_utc, initial_fen, moves_uci[], optional_pgn, result, time_control, engine_profile_id, schema_version}`. Externe PGN muss validiert werden; Zugzustände werden von einer einzigen Rules-Quelle berechnet.

## Puzzle

`Puzzle {id, source, source_export_date, original_fen, moves_uci[], rating, rating_deviation, popularity, plays, themes[], source_url, checksum}`. Bei Anzeige: `initial_fen -> first opponent move -> player start state`. Solve Progress getrennt: `puzzle_id, attempts, solved, last_attempt_utc, optional duration_ms, hints_used`.

## Einstellungen

`Settings {schema_version, locale, theme_id, piece_set_id, board_id, engine_profile_id, data_path}`. App-interne Pfade müssen portabel/migrierbar sein.

**Noch KEINE Datenbank-/JSON-Schemaversion beschlossen.** Vor Implementierung mit Tests und ADR-004 festlegen.
