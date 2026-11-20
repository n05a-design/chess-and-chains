# Zielarchitektur – Chess & Chains

**PROPOSED / ARCHITECTURE-GATE REQUIRED** – Ist-Stand N02 siehe Abschnitt „Implementierte Schichten (N02)“.

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

## Implementierte Schichten (N02)

| Paket | Verantwortung | Darf importieren |
| --- | --- | --- |
| `chess/` | Regeln, FEN/SAN/PGN, Historie | nur stdlib |
| `engines/` | UCI-Prozess, Mock-Engine, Presets, MoveProvider | `chess` |
| `game/` | GameController, Worker, Spielmodi | `chess`, `engines` |
| `puzzles/` | Modell, Importer, Packs, Session | `chess` |
| `storage/` | Pfade, SQLite, Settings | `chess` |
| `i18n/` | DE/EN-Kataloge | stdlib |
| `ui/` | Tk-App, Brett, Renderer, Dialoge | alle obigen |

Im aktuellen Code trägt die Anwendungsschicht den Paketnamen `game/`. `storage/` bündelt Datenbank und Einstellungen. Die Partiebibliothek reicht eine validierte `ChessGame` an den Controller. Ein Partiewechsel invalidiert dort ausstehende Bot-Aufträge.

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
Entscheidung klärt nicht die Stockfish-/Engine-Distribution. Der Owner wählte
zunächst Weg B für die UCI-Implementierung, bestätigte danach den
Sofortstart-Bot als Anforderung und beauftragte die Prüfung von Weg A. Diese
Prüfung ist keine Vertriebsfreigabe. Bis zur fachkundigen Prüfung bleiben
Engine-Bundles und -Downloads gesperrt; ADR-001 bleibt offen.

## Zu verifizierende Testfälle

Königs- und Bauernzüge, Schachabdeckung, Umwandlung in alle Figuren, EP-Entzug der Deckung, beidseitige Rochaden, unzulässige Rochade durch Angriff, Zugwiederholung und 50/75-Züge-Regel, Patt, unzureichendes Material, FEN-Castling/EP, PGN-Roundtrip, Engine-Hänger, Engine-Absturz, Zug während Berechnung, Undo, Katalog-Integrität, native Skalierung.
