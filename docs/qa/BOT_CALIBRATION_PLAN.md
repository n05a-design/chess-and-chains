# Bot-Kalibrierungsplan (vorbereitet, nicht ausgeführt)

**Status:** PROPOSED · **Bezug:** ADR-007, Q-023, `src/chess_and_chains/engines/bot_presets.json`

Die sechs Presets enthalten nur *angeforderte* Engine-Optionen (Skill Level, Threads, Hash, Zugzeit). Sie sind keine Spielstärkeangaben. Vor jeder Elo-Beschriftung:

1. **Voraussetzung:** ADR-001 klärt, welche Engine (Version, Binary-Hash, Lizenz) kalibriert wird. Ohne freigegebene Engine keine Messung.
2. **Referenzgegner:** Engine mit `UCI_LimitStrength`/`UCI_Elo` in festen Stufen (z. B. 1400/1700/2000) als Anker – nur wenn die Engine diese Optionen im Handshake anbietet.
3. **Turnier:** je Preset ≥ 400 Partien gegen jeden Anker, ausgeglichene Eröffnungsbuch-Stellungen (eigene oder gemeinfreie Liste), Farben getauscht, feste Zugzeit, 1 Thread, feste Hash-Größe, gleiche Hardware.
4. **Auswertung:** Elo-Differenz mit 95 %-Konfidenzintervall; Ergebnis nur als Spanne veröffentlichen.
5. **Reproduzierbarkeit:** Skript + Seed + Engine-Hash + Hardware + Befehlszeile in `docs/reports/` ablegen; Rohdaten-PGN außerhalb von Git oder komprimiert mit Prüfsumme.
6. **Regressionsschutz:** Eine Kurzversion (z. B. 40 Partien) als manueller CI-Job, nie bei jedem Commit.

Werkzeugbasis vorhanden: `GameController` + `UCIBot` + `plan_options` (Optionsprotokoll `UCIBot.last_plan`). Ein Turnier-Runner ist Folgeaufgabe (siehe N02-Handover, Aufgabe 6).
