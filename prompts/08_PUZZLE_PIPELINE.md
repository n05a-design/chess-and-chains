# PROMPT 08 – Lichess CC0 Offline-Puzzle-Pipeline

**Start nach W05, Datenquelle mit CC0 und Schema geprüft.** Lade keinen Riesendatensatz in das normale Repo und keine Bilder ohne Rechte herunter.

**Pipeline:** offizielles `lichess_db_puzzle.csv.zst` schemaorientiert lesen, mit Abbruchgrenzen und Fehlerbericht streamen, `Rating >= 1000`, Qualitätsfilter konfigurierbar (RatingDeviation, Popularity, NbPlays), reproduzierbarer Seed, Duplicate-IDs, Themes, Source-URL und Provenienz. Beachte: FEN ist Position **vor** dem ersten gegnerischen Zug; wende ersten Move an, erst dann Nutzerzug. Sämtliche UCI-Moves validieren inkl. Promotion, legaler Antworten und Endposition. Prüfe alternative gleichwertige Lösungen, soweit fachlich begründet, ohne unehrliche „alle Züge korrekt“-Behauptung.

**Storage:** Puzzle-Pack versioniert und read-only mit Prüfsumme, user solve history getrennt. Importer muss offline laufen, bis auf ausdrücklich initiierten Download der Rohquelle; Runtime darf beim Puzzlestart nicht ins Internet gehen.

**Tests:** kleine selbst erstellte Fixtures; invalid FEN, illegal Move, <1000, duplicates, empty themes, promotions, Mate-in-one, CSV malformation, memory behavior. Echte CC0-Batch-Prüfung mit dokumentiertem Datensatzstand; Fehlerrate/Packgröße messen.

**Gate:** Kein „20k Rätsel verfügbar“-Claim ohne real erzeugtes, validiertes Paket; Rohdatenrechte und Lizenz dokumentiert; Bericht + ADR-003 + ggf. Frage-Register.
