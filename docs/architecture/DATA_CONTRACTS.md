# Datenvertrag (W05-Regeldomäne implementiert; Produktpersistenz offen)

Der `src/chess_and_chains/chess/`-Kern ist eine lokale, unveränderliche
Positionsdomäne ohne GUI, UCI oder Dateisystem. `GameState` enthält ein
64-Felder-Tupel, Zugfarbe, Rochaderechte, en-passant-Ziel und FEN-Zähler;
`Move` enthält Quell-/Zielfeld und optionale Umwandlung. `RulesPort` bildet die
typisierte Grenze für Initialposition, legale Züge, Zustandsübergang,
FEN-Konvertierung, positionsidentitätsbasierte Wiederholung und Materialstatus.

Die `ChessGame`-Historie hält Zugliste, Wiederholungszähler und
Beendigungsstatus gemeinsam für Undo/Redo. Eine dreifache Wiederholung und die
50-Züge-Regel sind beanspruchbar; fünffache Wiederholung und 75 Züge sind
automatisch. Eine beanspruchte Remispartie ist von einem noch laufenden Spiel
unterschieden. FEN und PGN werden über die Domainfunktionen geparst/serialisiert;
PGN unterstützt die legale Hauptvariante sowie Tags, Kommentare/NAGs und
übersprungene Varianten, aber keine dauerhafte Varianten-/Kommentar-Editor-
Historie.

## Engine

`EngineProfile {id, display_name, executable_path, vendor, detected_uci_options, approved_bundle, license_record}`. Benutzerpfad nie ungeprüft als Shell-Kommando ausführen. Keine direkt in SQLite geschriebenen Engine-Binaries.

## Game

`Game {id, created_at_utc, initial_fen, moves_uci[], optional_pgn, result, time_control, engine_profile_id, schema_version}`. Externe PGN muss validiert werden; Zugzustände werden von einer einzigen Rules-Quelle berechnet.

## Puzzle

`Puzzle {id, source, source_export_date, original_fen, moves_uci[], rating, rating_deviation, popularity, plays, themes[], source_url, checksum}`. Bei Anzeige: `initial_fen -> first opponent move -> player start state`. Solve Progress getrennt: `puzzle_id, attempts, solved, last_attempt_utc, optional duration_ms, hints_used`.

## Einstellungen

`Settings {schema_version, locale, theme_id, piece_set_id, board_id, engine_profile_id, data_path}`. App-interne Pfade müssen portabel/migrierbar sein.

**Noch KEINE Datenbank-/JSON-Schemaversion beschlossen.** Vor Implementierung mit Tests und ADR-004 festlegen.
