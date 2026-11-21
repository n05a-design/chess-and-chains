# UCI Interface Contract (implementiert für Mock-Engine; echte Engine ungetestet)

## Standardablauf

Programm startet explizit konfigurierte lokale Engine als separaten Prozess, sendet `uci`, wartet auf `uciok`, sammelt angebotene `option`-Zeilen, sendet `isready`, wartet `readyok`, vor neuer Partie `ucinewgame`, dann `position ...`, `go ...`, liest `info ...` und `bestmove ...`, stoppt via `stop` und beendet via `quit`.

## Sicherheits- und Funktionsgrenzen

- Keine ungeprüfte Kommandoausführung, strikt Argumentliste statt Shell-Interpolation.
- Timeouts und Limits; Worker/Queue statt Tk-Blockade.
- Bei fehlender Engine verständliche lokale Fehlermeldung und UI-Rückkehr.
- Stärkenwerte nur setzen, wenn UCI-Option vom jeweiligen Binary bestätigt.
- Keine automatische Netzsuche/-Installation einer Engine; Bundle-Lizenz-Gate ist offen.
- Alle Versuche mit Test-double vor realem Engine-Prozess testen.

## Umsetzung N02

- `engines/uci.py`: Prozessadapter (`shell=False`), `kill()` für erzwungenes Beenden ohne Transaktionssperre.
- `engines/presets.py`: Presets werden gegen die im Handshake angekündigten Optionen geplant (`plan_options`); nicht angekündigte oder außerhalb des Bereichs liegende Werte werden übersprungen und protokolliert.
- `engines/bot.py`: `UCIBot` (MoveProvider), Engine-Konfiguration nur aus Settings-Pfad oder `CHESS_AND_CHAINS_ENGINE`; sonst Mock-Engine.
- `engines/bot.py::probe_engine`: Der Verbindungstest wartet auf `uciok` und `readyok`, liest den gemeldeten Namen und die Optionszahl und schließt den Prozess. Der Tk-Dialog pollt eine Ergebnis-Queue und beendet seine Abfrage beim Schließen. [Nachweis](../reports/2026-11-21_W07-uci-verbindungstest.md)
- `game/controller.py`: Worker-Thread mit Zugdaten und thread-sicherem Abbruchsignal pro `BotRequest`. Die Partie-ID löst einmal pro Partie und Engine-Prozess `ucinewgame` mit `isready` aus. Rückgängig/Wiederholen erhöhen nur die Generation. Ein abgebrochener Auftrag in der Warteschlange wird übersprungen. Der Adapter ordnet Abbruch und `go` über seine Zustandssperre. `poll()` verwirft veraltete Ergebnisse anhand von Generation und Halbzug und prüft den Zug gegen die eigene Regeldomäne.
- `engines/mock_engine.py`: projekteigener Test-Prozess, keine Schach-KI.

Norm-/Softwarequellen über `docs/research/SOURCES.md` dokumentieren. UCI-Details je Stockfish-Version erneut verifizieren.
