# ADR-003 – Puzzle-Katalog und Qualität

**Status: PROPOSED**.

Reguläre Puzzle-Packs mit `Rating >= 1000` laut **Puzzle-Rating** der Datenquelle. Die persönliche FIDE-/Online-Elo ist nicht gleich dem Puzzle-Rating. Geplanter Startumfang: 20.000–50.000 kuratierte Aufgaben. Vorhanden ist ein projekteigenes Paket mit fünf Demo-Rätseln. IV-B legt das erste lokale Produktpaket auf 20.000 Aufgaben fest.

Quelle: Lichess Open Database (CC0). Von jeder CSV-Zeile PuzzleID, FEN, Moves, Rating, RatingDeviation, Popularity, NbPlays, Themes, GameUrl etc. nur gemäß aktuellem offizieller Schema verarbeiten. FEN ist Stand **vor** dem ersten Move; zuerst Gegenzug, dann Nutzer. Alle Züge legal validieren, schwierige Varianten/Promotion/Schachstatus testen. Auswahlfilter für Ratingabweichung/Beliebtheit/Spielzahl müssen anhand Datenprofil und Bias-Analyse entschieden werden.

Keine Online-API als Pflicht. Datenimport in separatem Build/Preprocessing-Prozess; keine heruntergeladenen 100-MB-Dateien ins normale Git-Repository. Vor Binärpaketen Verteilung und Dateigröße prüfen.

Der [Offline-Builder](../../data/puzzle_packs/README.md) implementiert die
optionalen Qualitätsgrenzen und eine reproduzierbare Auswahl mit Seed.
Die Inhaberfreigabe Q-022 vom 28.11.2026 umfasst den lokalen offiziellen
CC0-Export, die Verarbeitung, ein privates Produktpaket und isolierte
Abnahme. Q-022 ist lokal umgesetzt. Öffentliche Distribution und
Bündelung sind ausdrücklich nicht freigegeben.

Für `lichess-core-20k` gelten mindestens 1000 Puzzle-Rating, Popularität
≥ 60, Ratingabweichung ≤ 125 und mindestens 10 Versuche. Sieben feste
Ratingbänder einschließlich 3000+ erhalten jeweils eigene Quoten.
Innerhalb eines Bandes sortiert der Builder nach SHA-256 aus Seed und
Rätsel-ID. Er validiert die Zugfolge im Schachkern und besetzt
abgewiesene Plätze mit Kandidaten derselben Schicht. Gleiche spielbare
Stellung mit gleicher Lösung zählt als Duplikat. Das Paket dient der
Trainingsabdeckung über Schwierigkeitsstufen.
[IV-B-Datenbericht](../reports/2026-11-28_W08-IV-B-lichess-produktdaten.md)
Fertig erzeugte Pakete können im Puzzle Lab lokal geprüft, installiert
und wieder geöffnet werden.
[W08/W09-Prüfnachweis](../reports/2026-11-21_W08-W09-lokale-raetselpakete.md)
