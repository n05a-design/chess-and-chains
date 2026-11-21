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
Für P-08 sind der Austausch der PGN-Hauptvariante und der FEN-Roundtrip
unter Windows nachgewiesen. Eine FEN-Datei enthält eine Stellung in einer
Zeile und umfasst höchstens 4 KiB. Beim Lesen sind UTF-8-BOM und umgebender
Leerraum zulässig. Die App schreibt die sechs kanonischen FEN-Felder
in ASCII mit abschließendem Zeilenumbruch und ersetzt die Zieldatei atomar.
Ein Start aus FEN beginnt einen lokalen Zweispielerverlauf ab der
importierten Stellung. Darin gelten Figurensatz, Zugfarbe, Rochaderechte,
en passant und Zähler aus der FEN. Die Vorgeschichte und ihre
Wiederholungszählung gehören zum Partieformat. In einem anschließend
exportierten PGN dokumentieren `SetUp` und `FEN` die abweichende
Ausgangsstellung. Verlustfreier Annotierungsaustausch bleibt eine
mögliche Erweiterung nach Scope-Entscheidung.

Der Regelkern erkennt tote Stellungen in Folgen von bis zu vier Halbzügen,
wenn jeweils nur ein Zug legal ist und die Folge in Patt oder ungenügendem
Material endet. Bei mehreren legalen Zügen gilt der Nachweis, wenn alle
unmittelbare Schläge in Stellungen mit ungenügendem Material sind. Für
geschlossene Bauernketten mit ausschließlich Königen und Bauern gibt
es einen weiteren Nachweis. Alle Bauern sind dauerhaft blockiert,
beide Könige bleiben in getrennten Bereichen und kein König erreicht
einen Schlag, der die Sperre öffnet. [Prüfbericht](../reports/2026-11-21_W05-bauernsperren.md)
Der Remisgrund wird aus dem Brett neu abgeleitet. Die
Wiedergabe alter PGN- und SQLite-Zugfolgen verwendet die bisherigen
Abbruchprüfungen, damit bereits gespeicherte Züge und Endgründe erhalten
bleiben. Für eine anschließend fortgesetzte Partie gilt die aktuelle
Regel. Rätsel prüfen weiterhin den vorgegebenen taktischen Ablauf.
[W05-Nachweis](../reports/2026-11-21_W05-mehrzuegige-tote-stellungen.md)

## Engine

Der Prototyp speichert einen Enginepfad in den Einstellungen. Der
Adapter ermittelt Name und Optionen beim UCI-Handshake. Ein gespeichertes
`EngineProfile` mit Anbieter, Lizenznachweis und Bundle-Freigabe gehört
zum Zielmodell. [UCI-Vertrag](UCI_CONTRACT.md)

## Game

Die Wiedergabe verwendet einen Schnappschuss der Anfangsstellung und der
bereits gespielten Positionen. Sie ändert weder den Spielverlauf noch
gespeicherte Aufzeichnungen. Bei einem historischen Datensatz wird das
Endergebnis am letzten Halbzug angezeigt.

`games` speichert `id`, `created_utc`, `initial_fen`, `moves_uci`, `pgn`,
`result`, `mode`, `bot_color`, `bot_name` und `bot_preset` sowie die ab
Schema 3 ergänzten Endgründe. SQLite lädt eine Partie erst, wenn
Ausgangs-FEN, UCI-Züge und Ergebnis mit dem validierten PGN übereinstimmen.
Die Bibliothek öffnet Spiele lokal für zwei Personen. Aus dem Brett
ableitbare Partieenden behalten ihren Grund.

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

Jede JSONL-Zeile enthält `id`, `source`, `fen`, `moves` (UCI),
`rating`, `rating_deviation`, `popularity`, `plays`, `themes`,
`game_url` und `opening_tags`. Die Ausgangs-FEN beschreibt die Stellung
vor dem Aufbauzug `moves[0]`. Erst nach diesem Zug übernimmt der Spieler.
Die Paketsumme steht im Manifest, angewendete Importgrenzen und Quellprüfsumme
stehen im Importbericht. [Offline-Builder](../../data/puzzle_packs/README.md)

Die UI kombiniert Themen und Ratingbereiche im aktiven Paket und zählt
unterschiedliche gelöste IDs. SQLite speichert Versuche mit `pack_id`,
`puzzle_id`, `attempted_utc`, `solved`, `mistakes`, `hints_used`
und optional `duration_ms`. Eine Korrektur der Paketherkunft mit denselben
Paket- und Aufgabenkennungen lässt diesen Bezug bestehen.

„Ungelöst“ umfasst Aufgaben ohne gespeicherten Erfolg. „Wiederholen“
umfasst bereits versuchte Aufgaben ohne fehlerfreie Lösung. Fehlerfreie
Lösungen haben null Fehler und null Hinweise. Die beste Lösungszeit nimmt
das Minimum unter gelösten Versuchen mit Zeitwert. Der zuletzt gespeicherte
Versuch wird innerhalb von Paket und Rätsel über seine SQLite-ID bestimmt.
Der erste Hinweis eines Spielerzugs zeigt das Startfeld. Der zweite zeigt
das Zielfeld und bei Bedarf die Umwandlungsfigur. Jeder angeforderte
Hinweis zählt zum aktuellen Versuch. Ein Neustart setzt diesen Versuch
auf die Stellung nach dem Aufbauzug zurück. Abgeschlossene Versuche
bleiben erhalten.

Der Puzzle-Lab-Import legt die geprüften Originalbytes des Manifests
und der JSONL-Datei atomar unter `puzzle_packs/<pack_id>` in den
Nutzerdaten ab. Die reservierte ID `demo` gehört zur mitgelieferten
Demo. Paketordner sind Katalogdaten. Der veränderliche Trainingsstand
bleibt in SQLite. Die Paketprüfung nutzt dieselben Abbruchregeln wie
eine Trainingseinheit, einschließlich der Anwendung des Aufbauzugs.
[Lokale Rätselpakete](../../data/puzzle_packs/README.md#in-der-app-verwenden)

## Einstellungen

Die aktuelle Settings-Datei enthält `schema_version`, `locale`, `theme_id`,
`piece_set_id`, `board_orientation`, `engine_path`, `bot_preset_id`,
`play_mode` und `last_pack_id`. `locale=null` folgt dem System mit dem
Fallback aus `i18n/catalog.py`. `last_pack_id` enthält die letzte
Rätselpaketwahl und wird beim Start wieder geladen. Fehlt das Paket oder
ist es ungültig, zeigt die App die Demo und meldet den Grund.
`theme_id`, `piece_set_id` und `board_orientation` sind Felder des
Formats. Der Brett- und Figurenwechsel wird im aktuellen CLI-Aufruf
gewählt. Der Datenpfad folgt der Plattform oder `CHESS_AND_CHAINS_DATA_DIR`.

**Implementierungsvorschlag N02 (ADR-004 weiterhin PROPOSED)**. SQLite
`PRAGMA user_version` = 3 (`games`, `puzzle_attempts`, View
`puzzle_progress`), Settings-JSON `schema_version` 1 und Puzzle-Packs
`schema` 1 (`manifest.json` mit SHA-256, `puzzles.jsonl` und
`import_report.json`). Migrationen sichern bestehende Datenbanken vorab
unter `*.pre-vN-*.bak`. Die App lehnt neuere Schemata ab und benennt
bestätigt beschädigte Dateien um. Wenn dabei eine neue Bibliothek
angelegt wird, nennt die App den Dateinamen der gesicherten beschädigten
Datei beim Start. Die endgültige Festlegung erfolgt
durch den Inhaber über ADR-004.

Bei einer Wiederherstellung liest SQLite die Sicherung in eine temporäre
Datenbank ein und migriert diese bei Bedarf. Anschließend validiert
`Database.load_game()` dort jeden Partiedatensatz mit denselben Regeln
wie beim Öffnen der Bibliothek. Nach erfolgreichen Prüfungen sichert die
App den aktiven Stand unter `*.pre-restore-*.bak` und ersetzt ihn in
einer SQLite-Backup-Transaktion.
[W09-Prüfnachweis](../reports/2026-11-21_W09-sichere-wiederherstellung.md)

Die Projektversion V.0.0.1 lässt diese Schemaversionen unverändert.
