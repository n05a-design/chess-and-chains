# Chess & Chains – Abhängigkeitsbasierte Roadmap

**V.0.0.1 · Stand 21.11.2026.** Der lokale Desktop-Prototyp ist als Entwicklungsstand versioniert. Automatisierte Prüfungen und die noch offenen Abnahmen stehen in den [Work Packages](WORK_PACKAGES.md).

## Nächste Aufgaben

| Priorität | Arbeit | Voraussetzung und nächster Nachweis |
| --- | --- | --- |
| 1 | W10 und W11 · Native Bedienabnahme | Die PR-#9-Matrix und die Windows-Sichtprobe bei 96 DPI sind dokumentiert. Folgestand in der GUI-CI prüfen. Fokusreihenfolge, Dialoge, Zugliste und Screenreader bei weiteren nativen Skalierungen abnehmen. [Paketabgleich](../reports/2026-11-21_W00-W12-paketabgleich.md) |
| 2 | W06 · Individuelle Brettgestaltung | Finale SVG-Bretter des Inhabers mit Partie, Rätseln, Perspektivwechsel und V.02 prüfen. Die lokale SVG-Vorschau unterstützt die [vereinbarten Lieferformate](../../assets/boards/source/README.md). |
| Parallel | W02/W07 · Echte Offline-Engine | Konkrete Engine- und Vertriebsstrategie für den sofort spielbaren Offline-Bot prüfen und in ADR-001 entscheiden lassen. Danach Test einer vollständigen Partie mit identifiziertem Binary und Offline-Nachweis. Die Mock-Tests dienen der Adapterprüfung. |
| Parallel | W08 · Produktiver Rätselkatalog | Nach Opt-in Q-022 den realen Lichess-Export und den Setupzug prüfen. Q-008/Q-009 entscheiden Ratingbereich und Paketgröße. Die Demo und Fixture-Tests sind vorhanden. |
| Parallel | W05/W09 · Regeln und Datenaustausch | Weitere tote Stellungen untersuchen. Windows-PGN-Import und -Export sind belegt. Rücksicherung mit widersprüchlichen Partiedaten und simulierten Schreibfehlern geprüft. Native Dateidialoge auf macOS/Linux und Profile nach ADR-004/Q-012 stehen aus. [W05-Nachweis](../reports/2026-11-21_W05-tote-stellungen-und-altpartien.md) · [W09-Nachweis](../reports/2026-11-21_W09-sichere-wiederherstellung.md) |
| Danach | W12 · Distribution | Installer, Lizenz- und Quellenbelege, Signaturen, Upgrade-/Offline-Tests und Inhaberfreigabe nach ADR-001, ADR-005 und ADR-006. Danach GitHub Releases und Software-Katalog. |

## Historische Phasenplanung F0 vom 19.11.2026

Die Aufwandswerte stammen aus der ursprünglichen Planung. Die Tabelle bildet Abhängigkeiten und Ziele ab. Für anstehende Arbeit gilt die Priorisierung oben.

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

## Stand nach PR #9

Der Prototyp enthält lokale Zweispielerpartien, Mock-UCI mit Bereitschaftstest,
fünf Demo-Rätsel, eine Partiebibliothek mit PGN-Austausch und Originalfiguren
in Vorderansicht V.02 und Draufsicht. Der [separate main-Lauf nach PR #9](https://github.com/n05a-design/chess-and-chains/actions/runs/44869510471)
schloss alle 14 Jobs erfolgreich ab. Den Stand und die offenen
Abnahmekriterien pro Paket führt der [Paketabgleich](../reports/2026-11-21_W00-W12-paketabgleich.md).

## Kritischer Pfad

Lizenz-Gate + Schachregeln + Engine-Fähigkeit + Rendering/Interaktion + Puzzle-Korrektheit + native Paketprüfung. Design und Marktanalyse parallel möglich; keine Veröffentlichung vor Legal/Source/QA-Freigabe.

## Historische Zielmarken und Versionspflege

- **F0**: historisches Planungsstarterpaket.
- **v0.1.0**: kontrollierter interner Board-/Regeln-Prototyp.
- **v0.2.0**: Offline-Bot-Prototyp nach Lizenzentscheidung.
- **v0.3.0**: Puzzle-MVP + Profile/Save.
- **v0.9.0**: Release Candidate mit Plattformabnahmen.
- **v1.0.0**: Erst nach explizitem Owner-Release-Gate.

Die Zielmarken sind frühere Planungswerte. Die aktuelle Entwicklungsnummer wird gemäß [Versionspflege](../governance/GOVERNANCE.md#projektversion) fortgeführt. Der Umfang richtet sich nach den [Work Packages](WORK_PACKAGES.md).
