# Zielarchitektur – Chess & Chains

**PROPOSED / ARCHITECTURE-GATE REQUIRED**

```text
app/ (Desktop host; UI, Navigation, Board)
   │
   ▼
src/chess_and_chains/application/ (commands, controller)
   ├── chess/  [legal moves + FEN/PGN; rules adapter]
   ├── engines/ [UCI boundary; independent process, config, lifecycle]
   ├── puzzles/ [validated Lichess import, selection, solution state]
   ├── persistence/ [SQLite, migrations, atomic operations]
   └── settings/ [user options, theme & locale]
   ▲
integrations/glide_shell/ (ONLY when individually cleared)
```

## Vertragsgrenzen

1. Chess-Domäne hängt weder von Tkinter noch von Glide/Steps ab. UI hängt an typisierten Services, nicht an der Engine-Binärdatei.
2. Engine-Adapter spricht *UCI* zu einem separaten Prozess. Keine Engine-Library-API im Domain Core. Engine-Version, Dateipfad, CPU-Kompatibilität und Timeouts als konfigurierte Daten behandeln.
3. Züge intern UCI und objektbasierter Spielzustand, serialisiert FEN/PGN über den typisierten Rules-Port. Keine Schachregeln in Canvas-Event-Callbacks implementieren.
4. Puzzle-Import ist offline reproduzierbar: FEN vor dem ersten Zug; zuerst den ersten Gegnerzug anwenden, danach Nutzeraufgabe; alle Schritte validieren.
5. Runtime-Daten **außerhalb** Installations- und Git-Verzeichnissen unter geeigneten OS-Benutzerpfaden. Migrationsnummern und Rücksicherung.
6. Locale, Asset-Varianten und UI sind eigene Einstellungen. Fehlende Übersetzungen müssen auffallen.
7. Kein verpflichtender Server, Telemetrie, Update-Check oder ungefragter Download. Online-Funktion später nur mit transparenter Opt-in-Konfiguration.
8. Anbieterbibliotheken, Shell-Code, originale Artwork-Quellen, Rohdaten und gebaute Installer haben getrennte Herkunfts-/Rechtseinträge.

## Vorläufiger Stack

Python 3.11+ für den Headless-Core; bevorzugt Tkinter/Tk für Desktop-Wiederverwendung. Python 3.14/Tk 9 muss auf Zielsystemen explizit getestet werden. SVG-Rendering-Strategie (Raster-Cache/Vektorrenderer) erfordert Prototyp und Lizenzprüfung. Tk vs. Qt ist kein Selbstzweck, sondern eine benchmarkbasierte Entscheidung.

## Schachkern – begrenzte W05-Entscheidung

Der Owner hat am 2026-11-20 einen eigenständig implementierten Regelkern
unter MPL-2.0 für W05 autorisiert. Die Domain bleibt ohne Drittanbieter-
Schachbibliothek, Tk, UCI und Dateisystem. `python-chess` ist GPLv3 und wird
nicht verwendet; `Chessnut` wird ebenfalls nicht übernommen. Diese begrenzte
Entscheidung klärt nicht die Stockfish-/Engine-Distribution; ADR-001 und
Q-001/Q-002 bleiben dafür offen.

## Zu verifizierende Testfälle

Königs- und Bauernzüge, Schachabdeckung, Umwandlung in alle Figuren, EP-Entzug der Deckung, beidseitige Rochaden, unzulässige Rochade durch Angriff, Zugwiederholung und 50/75-Züge-Regel, Patt, unzureichendes Material, FEN-Castling/EP, PGN-Roundtrip, Engine-Hänger, Engine-Absturz, Zug während Berechnung, Undo, Katalog-Integrität, native Skalierung.
