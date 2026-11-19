# PROMPT 07 – Vollständig lokale UCI-Engine und Schwierigkeitsstufen

**BLOCKER: ADR-001 muss für die gewählte Bundle-/Engine-Strategie entschieden sein; W05 muss grün sein.** Dieses Ticket ist keine automatische Genehmigung zum Bundlen von Stockfish.

**Ziel:** separater `UCIEnginePort` mit Lifecycle `start -> uci -> isready -> ucinewgame -> position -> go -> bestmove -> stop/quit`; konfigurierte Prozesspfade, CPU/Arch, Zeitbegrenzung, Fehler-/EOL-/Timeoutbehandlung. Kein `shell=True` mit untrusted Pfaden. No network required. Engine-Thread-/Process-Arbeit darf Tk event-loop nicht blockieren.

**Stärken:** Unterstützte echte UCI-Optionen dynamisch aus Engine-Handshake auslesen; sechs bis zehn Presets definieren, fehlende Optionen gracefully degradieren; keine unbewiesene Elo-Gleichsetzung oder fiktive Bot-Persönlichkeiten. Dokumentiere Benchmarkplan für Spielstärken und faire Bedenkzeiten.

**Tests:** Mock-UCI-Process ohne Dritt-Engine, danach reale Engine ausschließlich gemäß genehmigtem Rechtsweg; fehlende Binary, Absturz, Zug-Timeout, invalid bestmove, Verlassen des Spiels, Neustart, concurrent requests, no-network offline integration.

**Gate:** Nachweis einer vollständigen lokalen Bot-Partie nur bei realem Test, korrektes License/Binary-Inventar, kein unerlaubter Stockfish-Commit. Rapport W07 + README-Status.
