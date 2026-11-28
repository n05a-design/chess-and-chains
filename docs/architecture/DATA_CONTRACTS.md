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
wenn jeder betrachtete Zweig in Patt oder ungenügendem Material endet. Bei
mehreren legalen Zügen verfolgt die Prüfung ausschließlich Stellungen, in
denen sämtliche verfügbaren Züge Schläge auf besetzte Felder sind. Für
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
Die Bibliothek bietet Fortsetzen im ursprünglichen Modus, lokales Öffnen für
zwei Personen, Wiedergabe, Analyse und eine neue Partie ab Stellung. Eine
gespeicherte Bot-Partie braucht zum Fortsetzen die passende lokale
Engine-Referenz. Ältere Bot-Datensätze bleiben für die anderen Aktionen
verfügbar. Aus dem Brett ableitbare Partieenden behalten ihren Grund.

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

## Automatische Partiekopie und Zeitkontrolle

SQLite v4 legt genau einen Slot in `active_session` an. Das JSON-Schema 1
enthält eine UUID, UTC-Zeitstempel, Profil, Spielmodus, Ausgangs-FEN, die
vollständige Zugfolge einschließlich Redo, einen Aktionsindex und die
Metadaten eines ausdrücklichen Spielendes. Der Decoder begrenzt Größe und
Zugzahl und validiert alle Felder bei der Wiederherstellung. Ein unbekanntes
Schema oder eine unpassende Engine lässt die Kopie zur späteren Fortsetzung
vorliegen. Der gespeicherte Engine-Verweis enthält keine Befehlszeile.
Der Dialog prüft Fingerabdrücke separat. Bibliotheksarchive und automatische
Kopie haben unterschiedliche Lebensdauern.

Mit Uhr gilt der vom Controller erfasste monotone Zeitpunkt für die
Zugannahme. Genau null zählt als Zeitablauf. Ein legal angenommener Zug
erhält Fischer-Inkrement. Umwandlung und Bot-Suche zählen zur laufenden Zeit.
Anhalten, Neustart und Undo/Redo pausieren. Der nächste Spieler behält seine
Restzeit aus dem passenden Zugcheckpoint. Beim ordentlichen Schließen
speichert die App die aktuellen Zeiten. Bei einem Absturz gilt der letzte
committete Checkpoint. Standby folgt dem Zeitverhalten der Host-Plattform.
Beim Zeitablauf prüft der Regelkern die Mattmöglichkeit der verbleibenden
Seite mit einer begrenzten Suche nach legalen Folgen. Ein nachgewiesener
Mattweg ergibt einen Sieg. Eindeutig ausgeschlossene Mattmöglichkeiten
ergeben Remis. Bei offenem Ausgang pausiert die App zur Entscheidung.
Die Bibliothek speichert Ergebnis und `Termination "time forfeit"` im PGN.
Uhrstände sind an die automatische Kopie gebunden.
[FIDE-Regeln ab 1. Januar 2023, Art. 5.2.2 und 6.9](https://handbook.fide.com/chapter/E012023)

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

Installierte Pakete werden im Puzzle Lab über einen separaten SQLite-Katalog
geöffnet. Im Nutzerdatenordner `puzzle_packs-catalogs/<pack_id>` bindet ein
lokal geschriebener Validierungsbeleg den SHA-256-Fingerabdruck von Manifest,
JSONL und Index an Katalogschema 1. Der erste Zugriff auf ein altes JSONL-Paket
prüft dessen Stellungen und Zugfolgen vollständig. Spätere Zugriffe prüfen
Dateiintegrität und Schema und lesen über den Index. Ein extern mitgelieferter
Index ist damit keine Quelle für die fachliche Freigabe. Pro Auswahl werden IDs
und ein Fenster von bis zu 48 Rätseldatensätzen geladen.

Kompatible Paketrevisionen dürfen Metadaten ändern und Aufgaben ergänzen.
Für bestehende IDs bleiben normalisierte FEN und gesamte UCI-Zugfolge
einschließlich Aufbauzug gleich, damit die Fortschrittszuordnung stabil
bleibt. Die vorherigen Paketgenerationen bleiben lokal verfügbar. Ein aktiver
Verweis wird erst nach erfolgreicher Validierung der neuen Generation ersetzt.

Das lokale Produktpaket `lichess-core-20k` verwendet Pack- und Katalogschema 1.
Der Offline-Builder verarbeitet den gesamten CC0-Quellstream und versieht
`import_report.json` mit komprimierter und entpackter SHA-256, Profil,
Qualitätsfiltern, Seed und Verteilung. Der Builder hält eine begrenzte
Vorauswahl je Ratingband und prüft die aufgenommenen Zeilen im Schachkern.
Für die Auswahl zählt die kanonische spielbare Position nach dem Aufbauzug
mit ihrer Lösungsfolge als Inhaltsidentität. Der Katalog behält zusätzlich
den versionskompatiblen Fingerabdruck über die Ausgangsstellung und die
gesamte Zugfolge. Der Fortschritt bleibt über `pack_id` und `puzzle_id`
zugeordnet. Manifest und Nutzdaten liegen getrennt vom Build-Bericht.

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

**Implementierungsstand im Functional-Completion-Branch (ADR-004 weiterhin PROPOSED).** SQLite
`PRAGMA user_version` = 8. Altdaten in `games` und `puzzle_attempts`
erhalten die feste Kennung `local`. `training_candidates` speichert
Stellungen mit Partiereferenz und Halbzug. Der Wiederholungsplan beruht
auf den vorhandenen Versuchen. Einstellungen bleiben bei JSON `schema_version` 1
und Puzzle-Packs bei `schema` 1 (`manifest.json` mit SHA-256, `puzzles.jsonl` und
`import_report.json`). Migrationen sichern bestehende Datenbanken vorab
unter `*.pre-vN-*.bak`. Die App lehnt neuere Schemata ab und benennt
bestätigt beschädigte Dateien um. Wenn dabei eine neue Bibliothek
angelegt wird, nennt die App den Dateinamen der gesicherten beschädigten
Datei beim Start. Die endgültige Festlegung erfolgt
durch den Inhaber über ADR-004.

Bei einer Wiederherstellung liest SQLite die Sicherung in eine temporäre
Datenbank ein und migriert diese bei Bedarf. Anschließend validiert
`Database.load_game()` dort jeden Partiedatensatz mit denselben Regeln
wie beim Öffnen der Bibliothek. Die Rücksicherung prüft auch die automatische
Kopie, die referenzierten Trainingsstellungen, Analyseberichte und die Mattkette. Nach erfolgreichen Prüfungen sichert die
App den aktiven Stand unter `*.pre-restore-*.bak` und ersetzt ihn in
einer SQLite-Backup-Transaktion.
[W09-Prüfnachweis](../reports/2026-11-21_W09-sichere-wiederherstellung.md)

## Partiearchiv und Profilbackup

SQLite v6 ergänzt `games.session_snapshot` als optionales, auf 256 KiB
begrenztes Sitzungs-JSON. Lokale Archive halten darüber die Zeitkontrolle,
den Uhrverlauf, den letzten eingefrorenen Stand und die Redo-Historie fest.
Beim Lesen werden Spielmodus, Engine-Referenz, Ergebnis, Stellung und
Zugfolge gegen den Partiedatensatz geprüft. Alte Archive und PGN-Importe
haben keinen Sitzungssnapshot. Ganzzahlige Zeitkontrollen in Sekunden
werden auch als PGN-`TimeControl` exportiert. Beginn und Ende sind bei neuen
fertigen lokalen Partien aus dem Sitzungssnapshot ablesbar. Die Zeitspanne
zwischen diesen Zeitpunkten enthält auch Pausen.

SQLite v7 ergänzt ein Favoritenfeld sowie normalisierte Tags mit Fremdschlüssel
zur Partie. Die Bibliotheksabfrage kann diese Merkmale mit Archivzeitraum (UTC),
Modus, Ergebnis, Engine-Referenz, Preset, Zeitkontrolle und vorhandenen Analysen
oder Trainingsstellungen kombinieren. Lese- und Schreibzugriff auf Labels
sind als Datenbank-API verfügbar.

Die automatische Sicherung ersetzt den Einzel-Slot nur, wenn sein Inhalt
noch dem zuletzt von der jeweiligen App-Instanz gelesenen Stand entspricht.
Bei einem Konflikt kann die neuere Partie über „Sitzung fortsetzen“ geladen
werden. Remisvereinbarungen erhalten im Sitzungsformat einen optionalen
Endgrund. Ein offenes Remisangebot ist an die laufende Bestätigung gebunden.

Das Profilbackup ist ein ZIP der Version 1 mit `manifest.json`, `games.sqlite3`
und `settings.json`. Das Manifest enthält Dateiprüfsummen und die referenzierten
Paket-IDs. Enthalten sind die SQLite-Nutzerdaten einschließlich des Profils
`local`, aktiver Sitzungen, Partien, Analysen, Trainingskandidaten und
Trainingsfortschritt sowie die Einstellungen. Paketdateien, deren Index,
Programmdateien und Engine-Binaries werden separat verwaltet. Engine-Pfade
im Backup bleiben beim Import inaktiv. Die lokalen Engine-Einstellungen des
Zielrechners werden übernommen. Fehlende Rätselpakete werden gemeldet.

Archivnamen und Größen werden vor dem Entpacken geprüft. SQLite und
Settings werden vor der Übernahme validiert. Bei einem Fehler während des
Settings-Austauschs wird die Datenbank zurückgesetzt. Für einen
Prozessabbruch zwischen den Schreibvorgängen liegt ein gemeinsames
`pre-profile-restore-*.zip` im Backup-Ordner. Es lässt sich mit demselben
Wiederherstellungsbefehl einspielen. Dazu die App schließen.

```bash
PYTHONPATH=src python3 -m chess_and_chains --create-backup /absoluter/pfad/profil.zip
PYTHONPATH=src python3 -m chess_and_chains --restore-backup /absoluter/pfad/profil.zip
```

Die zweite Option unterstützt auch ältere SQLite-Sicherungen. Einstellungen
werden beim Laden eines alten SQLite-Backups beibehalten.
Beim Löschen einer Partie löscht die aktuelle Datenbank die abhängigen
Analyseberichte, Tags und stellungsbezogenen Trainingskandidaten per Fremdschlüssel.
Paketfortschritt und eigenständige Trainingsversuche bleiben erhalten.

## Analyseberichte und Mattkette

SQLite v5 speichert vollständige Bibliotheksanalysen in `analysis_reports`.
Das begrenzte JSON-Format der Berichte hat Schema 1. Jede Position ist über
ihren Index an die Zugfolge der Quellpartie gebunden. Die App prüft FEN,
UCI-Varianten und Engine-Metadaten. Die Engine-Konfiguration im Bericht
dient der Herkunft. Die Anzeige löst keinen Engine-Start aus.

`training_checkpoints` enthält den zuletzt gesicherten Stand der kuratierten
Mattkette. Das versionierte Format enthält die Ketten-ID, eine Signatur
der Rätselreihenfolge und Lösungen, die Versuch-IDs und den laufenden
Versuch mit Zugfolge, Zählern und verstrichener Spielzeit. Die Wiederaufnahme
prüft die Züge mit dem installierten Demopaket. Der Revisionsvergleich und
die Wertung abgeschlossener Versuche laufen in derselben SQLite-Transaktion.
Die bestehende Fortschrittsansicht verwendet dieselben Puzzle-Versuche.

## Sitzungsphasen und Wiederherstellung

Der Partiekern erhält Zugfolge, Cursor und Ergebnis. Das optionale Feld
`phase` des Sitzungsformats unterscheidet erstellt, aktiv, pausiert,
unterbrochen, wiederhergestellt, ausstehende Zeitablaufentscheidung,
abgeschlossen und verworfen. Ältere Snapshots lassen sich laden. Erstellt
oder wiederhergestellt wird bei Zug oder laufender Uhr aktiv. Nur eine
laufende Uhr kann pausieren. Das Schließen pausiert die Uhr und sichert die
Unterbrechung. Ein Zeitablauf mit offenem Ergebnis sperrt weitere Züge.
Bestätigtes Verwerfen beendet die Wiederaufnahme dieser Kopie. Bei CAS-
Konflikt kann das Fenster seine Partie separat in die Bibliothek schreiben,
den neueren Stand laden oder mit pausierter Autosicherung geöffnet bleiben.

Für einen bestätigten Engine-Wechsel stehen alte und neue Referenz,
Wechselzeit, Halbzug und Grund im Snapshot. Verifizierte historische
Metadaten werden eingebettet. Sie bleiben beim Entfernen der lokalen
Registrierung lesbar. Eine zeitgesteuerte Wiederaufnahme beginnt pausiert.

Uhrannotationen `[%clk ...]` erhalten die Restzeit der ziehenden Seite
nach ihrem Halbzug. Eingelesen werden Annotationen der Hauptvariante.
Der lokale Snapshot hält zusätzlich beide Uhrstände, die finale Lesung
und bei neuen Zeitpartien die monoton gemessene aktive Spielzeit sowie explizite
Pausen fest. Ein Zeitraum bei beendeter App zählt dabei als Unterbrechung.

Das Restore-Journal `.profile-restore.json` enthält eine
Transaktions-ID, Prüfsummen des Eingangspakets, der Sicherheitskopie und
des Profils sowie die aktuelle Phase. Vor normalem Öffnen muss die App
einen ausstehenden Restore abschließen oder den vorherigen Profilstand
wiederherstellen. Die SQLite-basierte Profilsperre erlaubt mehrere
lesende Desktop-Leases und exklusiven Restore. Die Betriebssystem-Sperre
endet beim Prozessabbruch. Portable Backups führen unveränderliche Registry-Referenzen im Manifest.
Die Auswahl und Ausführungsfreigabe stammen ausschließlich aus dem Zielprofil.

SQLite v8 ergänzt `analysis_training_candidates` mit formatversionierten,
regelvalidierten Datensätzen. Die optionalen Fremdschlüssel auf Partie und
Analyse verwenden `ON DELETE SET NULL`. Historische Quellenkennungen und
der für freies Stellungstraining benötigte Inhalt bleiben eingebettet.
Bestehende stellungsgebundene Trainingskandidaten behalten ihren Vertrag.
