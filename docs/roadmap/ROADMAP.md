# Chess & Chains – Abhängigkeitsbasierte Roadmap

**Planungsbaseline F0 / 19.11.2026.** Keine freigegebene Lieferfrist und keine Zusage, dass Copilot autonom publizieren darf.

| Phase | Ziel | Geschätzte Intensivwochen* | Gate |
| --- | --- | --- | --- |
| F0 – Foundation | GitHub, SSOT, Scope, Rechte, Shell-Freeze, Marktposition | 1–2 | W00–W04 |
| F1 – Playable Core | Reines Schachmodell, Regeln, Board/Assets | 2–3 | W05–W06 |
| F2 – Bot Play | UCI und lokale, getestete Schwierigkeitsstufen | 1–2 | W07 + ADR-001 |
| F3 – Puzzle Lab | Lichess-Import, SQLite, Rating >= 1000, Lösungen | 2–3 | W08 |
| F4 – Product Experience | Save/Load, DE/EN, Design, Profile, Accessibility | 2–3 | W09–W10 |
| F5 – Distribution | Native QA, Lizenzen, Installer, Website/Packagemanager | 2–4 | W11–W12 |
| V1.1+ | Analysetools, Chain Training, weitere Engines, Öffnungs-Bibliothek | TBD | Neu entscheiden |

*Aufwand bei fokussierter Arbeit mit KI-Unterstützung, **nicht** verbindliche Kalenderwochen; Arbeit parallel zu Steps/Glide dauert länger.*

## Kritischer Pfad

Lizenz-Gate + Schachregeln + Engine-Fähigkeit + Rendering/Interaktion + Puzzle-Korrektheit + native Paketprüfung. Design und Marktanalyse parallel möglich; keine Veröffentlichung vor Legal/Source/QA-Freigabe.

## Zielversionen

- **F0**: dieses Planungsstarterpaket (nicht als spielbares `v0.1.0` bezeichnen).
- **v0.1.0**: kontrollierter interner Board-/Regeln-Prototyp.
- **v0.2.0**: Offline-Bot-Prototyp nach Lizenzentscheidung.
- **v0.3.0**: Puzzle-MVP + Profile/Save.
- **v0.9.0**: Release Candidate mit Plattformabnahmen.
- **v1.0.0**: Erst nach explizitem Owner-Release-Gate.

Verbindliche Wxx-Tickets: [WORK_PACKAGES.md](WORK_PACKAGES.md).
