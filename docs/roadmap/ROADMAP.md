# Chess & Chains – Abhängigkeitsbasierte Roadmap

**V.0.0.1 · Stand 21.11.2026.** Der lokale Desktop-Prototyp ist als Entwicklungsstand versioniert. Automatisierte Prüfungen und die noch offenen Abnahmen stehen in den [Work Packages](WORK_PACKAGES.md).

## Nächste Aufgaben

| Priorität | Arbeit | Voraussetzung und nächster Nachweis |
| --- | --- | --- |
| 1 | W10 und W11 · Native Bedienabnahme | PR #12 mit den Tastaturwegen für PGN-Import, Export und Abbruch ist in `main` und bestand den Merge-Lauf. Native Skalierung, physischer Ziffernblock und Screenreader stehen zur Abnahme aus. [W10-Prüfnachweis](../reports/2026-11-21_W10-dialogtastatur.md) |
| 2 | W06 · Individuelle Brettgestaltung | Die Wiederverwendung der beiden Perspektiven ist lokal geprüft. Finale SVG-Bretter des Inhabers mit Partie, Rätseln und V.02 prüfen. [Lieferformate](../../assets/boards/source/README.md) · [W06-Prüfnachweis](../reports/2026-11-21_W06-svg-brettcache.md) |
| Parallel | W02/W07 · Echte Offline-Engine | Konkrete Engine- und Vertriebsstrategie für den sofort spielbaren Offline-Bot prüfen und in ADR-001 entscheiden lassen. Danach Test einer vollständigen Partie mit identifiziertem Binary und Offline-Nachweis. Die Mock-Tests dienen der Adapterprüfung. |
| Parallel | W08 · Produktiver Rätselkatalog | Importgrenzen, Demo-Herkunft und Auswahl per Seed mit lokalen Fixtures geprüft. Nach Opt-in Q-022 den realen Export und den Setupzug prüfen. Datenprofil und Stichprobe auswerten. Q-008/Q-009 entscheiden Ratingbereich und Paketgröße. [W08-Prüfnachweis](../reports/2026-11-21_W08-puzzle-seed.md) |
| Parallel | W05/W09 · Regeln und Datenaustausch | Kurze Zwangsfolgen mit Remis und historische Aufzeichnungen geprüft. Verblockte Stellungen und längere oder verzweigte Zwangsfolgen weiter untersuchen. Rücksicherung mit widersprüchlichen Partiedaten und simulierten Schreibfehlern geprüft. Native Dateidialoge auf macOS/Linux und Profile nach ADR-004/Q-012 stehen aus. [W05-Nachweis](../reports/2026-11-21_W05-mehrzuegige-tote-stellungen.md) · [W09-Nachweis](../reports/2026-11-21_W09-sichere-wiederherstellung.md) |
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

## Entwicklung und CI-Stand

Der Prototyp enthält lokale Zweispielerpartien, Mock-UCI mit Bereitschaftstest,
fünf Demo-Rätsel, eine Partiebibliothek mit PGN-Austausch und Originalfiguren
in Vorderansicht V.02 und Draufsicht. Der [separate main-Lauf nach PR #9](https://github.com/n05a-design/chess-and-chains/actions/runs/44869510471)
schloss alle 14 Jobs erfolgreich ab. Den Stand und die offenen
Abnahmekriterien pro Paket führt der [Paketabgleich](../reports/2026-11-21_W00-W12-paketabgleich.md).
Der [Ablageabgleich](../reports/2026-11-21_W11-ablageabgleich.md) dokumentiert
die Folge-Commits, Designquellen und archivierten OneDrive-Stände. PR #10
bestand die Plattformmatrix im Push- und PR-Lauf sowie nach dem Merge auf
`main`. Die lokalen Folgecommits ergänzen die Rätselthemen auf Deutsch und
Englisch, Qualitätsfilter, kurze Zwangsfolgen und die Auswahl per Seed.
Diese Folgecommits sind mit PR #11 in `main` und bestanden dort 14 von
14 Jobs. Die Dialogtastatur folgte mit PR #12 und 14 erfolgreichen Jobs
nach dem Merge. Der lokale W06-Folgebranch beschleunigt die Drehung in
der SVG-Brettvorschau.
[Merge-Lauf PR #10](https://github.com/n05a-design/chess-and-chains/actions/runs/44901076786) ·
[Merge-Lauf PR #11](https://github.com/n05a-design/chess-and-chains/actions/runs/44904083668) ·
[Merge-Lauf PR #12](https://github.com/n05a-design/chess-and-chains/actions/runs/44905214890) ·
[W06-Prüfstand](../reports/2026-11-21_W06-svg-brettcache.md)

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
