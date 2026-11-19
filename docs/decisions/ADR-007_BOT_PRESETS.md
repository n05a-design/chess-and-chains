# ADR-007 – Bot-Stärken und Spielstile

**Status: OPEN.**

Für MVP sechs bis zehn feste Presets und eine Expertenoption erwägen. Stockfish UCI `UCI_LimitStrength` / `UCI_Elo` nur innerhalb tatsächlich unterstützter Werte; `Skill Level` getrennt verstehen. Produktlabels niemals als reale Elo kalibriert darstellen, bevor Benchmark-Matches vorliegen. Sehr niedrige Stärken brauchen ggf. andere Zugauswahl und differenziertes Fehlermodell.

Bot-Persönlichkeiten (*aggressiv*, *defensiv*, *menschenähnlich*) sind Folgefeatures, keine Marketingbehauptung über einfache Stockfish-Einstellungen. Testbare Regeln und Engineprofil-Spezifikation folgen nach W07.
