# UCI Interface Contract (Ziel, noch nicht implementiert)

## Standardablauf

Programm startet explizit konfigurierte lokale Engine als separaten Prozess, sendet `uci`, wartet auf `uciok`, sammelt angebotene `option`-Zeilen, sendet `isready`, wartet `readyok`, vor neuer Partie `ucinewgame`, dann `position ...`, `go ...`, liest `info ...` und `bestmove ...`, stoppt via `stop` und beendet via `quit`.

## Sicherheits- und Funktionsgrenzen

- Keine ungeprüfte Kommandoausführung, strikt Argumentliste statt Shell-Interpolation.
- Timeouts und Limits; Worker/Queue statt Tk-Blockade.
- Bei fehlender Engine verständliche lokale Fehlermeldung und UI-Rückkehr.
- Stärkenwerte nur setzen, wenn UCI-Option vom jeweiligen Binary bestätigt.
- Keine automatische Netzsuche/-Installation einer Engine; Bundle-Lizenz-Gate ist offen.
- Alle Versuche mit Test-double vor realem Engine-Prozess testen.

Norm-/Softwarequellen über `docs/research/SOURCES.md` dokumentieren. UCI-Details je Stockfish-Version erneut verifizieren.
