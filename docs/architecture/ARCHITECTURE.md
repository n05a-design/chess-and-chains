# Zielarchitektur – Chess & Chains

**V.0.3.0 · Stand 24.11.2026 · Integrierte Laufzeitarchitektur auf Glide Shell 0.6.2 (Glide `v1.0.2`).**

```text
Chess & Chains Desktop Application (ui/app.py -> glide_shell.app_host.AppHost)
         /                                   \
        v                                     v
  Glide Shell 0.6.2 (src/glide_shell/)    Chess Services (chess_and_chains)
  [app_host, window_lifetime,              ├── chess/   [legal moves + FEN/SAN/PGN; stdlib only]
   modal_session, motion, custom_controls, ├── engines/ [UCI process, mock engine, presets]
   desktop_adapter, action_picker,         ├── game/    [GameController, async BotWorker]
   window_geometry, system_appearance,     ├── puzzles/ [Lichess importer, packs, sessions]
   text_fit, runtime_paths,                ├── storage/ [SQLite, migrations, settings, paths]
   command_history, redo_history]          └── i18n/    [DE/EN catalogs]
        |
        v
   Python / Tk
```

## Implementierte Schichten

| Paket | Verantwortung | Darf importieren |
| --- | --- | --- |
| `glide_shell/` | Neutrales Tk-Fundament (Shell 0.6.2, Commit `7dcd8dc04366`) | stdlib, `tkinter` (nie `chess_and_chains` oder `glide`) |
| `chess/` | Regeln, FEN/SAN/PGN, Historie | nur stdlib |
| `engines/` | UCI-Prozess, Mock-Engine, Presets, MoveProvider | `chess` |
| `game/` | GameController, Worker, Spielmodi | `chess`, `engines` |
| `puzzles/` | Modell, Importer, Packs, Session | `chess` |
| `storage/` | Pfade (`runtime_paths`), SQLite, Settings (`window_geometry`) | `chess`, `glide_shell.runtime_paths`, `glide_shell.window_geometry` |
| `i18n/` | DE/EN-Kataloge | stdlib |
| `ui/` | Tk-App auf `AppHost`, Brett, Renderer, `modal_session`-Dialoge, Themes | alle obigen |

Im aktuellen Code trägt die Anwendungsschicht den Paketnamen `game/`. `storage/` bündelt Datenbank und Einstellungen. Die Partiebibliothek reicht eine validierte `ChessGame` an den Controller. Ein Partiewechsel invalidiert dort ausstehende Bot-Aufträge.

`app/main.py` und das installierte Konsolenskript delegieren an
`src/chess_and_chains/__main__.py`. Die Tk-Runtime verwendet V.02-Vorderansichten
oder die per `--piece-view top` gewählte Draufsicht. Tk 9 liest Figuren und
optionale Brettvorschau direkt als SVG. Für die Figuren gibt es PNG-Atlanten
für Tk ohne SVG-Leser. Der Engine-Verbindungstest übermittelt Daten aus
dem Worker per Queue an den Tk-Thread. [UCI-Vertrag](UCI_CONTRACT.md)

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

Python 3.11+ und Tk sind die Basis des Prototyps. Die CI prüft Python 3.11
und 3.14 auf Windows, macOS und Linux. Tk 9 mit SVG wurde auch lokal geprüft.
CairoSVG bleibt ein separater Forschungspfad gemäß ADR-002. Native
Installer- und Plattformabnahmen folgen dem [Testplan](../qa/TEST_PLAN.md).

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
