# PROMPT 05 – Schachregel-Domäne und nachweisbar korrekte Partien

**Nur nach W01 + W02 und geklärter Regeln-Lizenzentscheidung starten.** Keine GUI-Implementierung als Ersatz für Schachregeln.

**Ziel:** unabhängiger Python Chess Core als Adapter (gewählte, rechtlich freigegebene Bibliothek oder getestete eigene Domain). Features: initiale Stellung, legal moves, turn state, castling, EP, all promotions, check, checkmate, stalemate, insufficient material, repetition, 50/75 move handling, resignation/draw claim state, FEN, PGN, move history, complete undo/redo. Für 3-/5-fache Wiederholung und Remisanspruch exakte Semantik von automatischen und beanspruchten Remis unterscheiden.

**Design:** typed API: GameState/Move/MoveOutcome/RulesPort; kein Tk-/UCI-/Dateisystemimport in Domain. Versions- und Fehlerverhalten definieren. Keine eigenen Schachregeln in `Canvas.click()`.

**Tests:** Standard-Perft-Stellungen gegen vertrauenswürdige Referenzen, Sonderzug-Golden-Tests, illegal moves, positions with pinned pieces, undo restores full state, serialization roundtrip, game end; bekannte Referenz-/Lizenzquelle für Testpositions-FEN dokumentieren. Alle Tests mit Umgebung und Exitcode protokollieren.

**Deliverables:** Headless-Module + Tests + Architektur/QA/README-Status + W05-Bericht.

**Gate:** vollständig geprüfte Regeln, keine ungeklärte GPL-Abhängigkeit, keine Behauptung von Release-Reife aus allein grünen Unit-Tests.
