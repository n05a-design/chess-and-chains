# ADR-003 – Puzzle-Katalog und Qualität

**Status: PROPOSED**.

Reguläre Puzzle-Packs mit `Rating >= 1000` laut **Puzzle-Rating** der Datenquelle. Die persönliche FIDE-/Online-Elo ist nicht gleich dem Puzzle-Rating. Geplanter Startumfang: 20.000–50.000 kuratierte Aufgaben. Vorhanden ist ein projekteigenes Paket mit fünf Demo-Rätseln. Ein produktiver Lichess-Datensatz steht aus.

Quelle: Lichess Open Database (CC0). Von jeder CSV-Zeile PuzzleID, FEN, Moves, Rating, RatingDeviation, Popularity, NbPlays, Themes, GameUrl etc. nur gemäß aktuellem offizieller Schema verarbeiten. FEN ist Stand **vor** dem ersten Move; zuerst Gegenzug, dann Nutzer. Alle Züge legal validieren, schwierige Varianten/Promotion/Schachstatus testen. Auswahlfilter für Ratingabweichung/Beliebtheit/Spielzahl müssen anhand Datenprofil und Bias-Analyse entschieden werden.

Keine Online-API als Pflicht. Datenimport in separatem Build/Preprocessing-Prozess; keine heruntergeladenen 100-MB-Dateien ins normale Git-Repository. Vor Binärpaketen Verteilung und Dateigröße prüfen.

Der [Offline-Builder](../../data/puzzle_packs/README.md) implementiert die
optionalen Qualitätsgrenzen und eine reproduzierbare Auswahl mit Seed.
Für ein Produktpaket stehen der freigegebene Realdatenimport, ein
Datenprofil, Grenzwerte, die Beurteilung der Stichprobe und Q-008/Q-009 aus.
Fertig erzeugte Pakete können im Puzzle Lab lokal geprüft, installiert
und wieder geöffnet werden.
[W08/W09-Prüfnachweis](../reports/2026-11-21_W08-W09-lokale-raetselpakete.md)
