# Chess & Chains – Roadmap

**V.0.3.0 · Stand 28.11.2026.** GitHub-`main` steht bei `6dcd12f` mit
14 erfolgreichen Jobs des Merge-Laufs von PR #26. Der lokale
Integrationsbranch enthält Auftrag III und IV-B. Als Nächstes stehen
IV-A für die Engine-Abnahme und V für Connected Learning an.
[Funktionsinventar F01–F26](FUNCTIONAL_CORE.md) ·
[Integrationsbericht](../reports/2026-11-28_Integration-Gate-III-IV-B.md)

## Wo das Projekt steht

| Bereich | Erreicht | Fehlt bis zur Abnahme |
| --- | --- | --- |
| Regeln (W05) | Legale Züge, FEN/SAN/PGN, Remisregeln, Perft, tote Stellungen bei kurzen Zwangsfolgen und geschlossenen Bauernsperren | Allgemeine Erkennung toter Stellungen, Owner-Abnahme |
| Brett und Figuren (W06) | Tk-Brett auf Glide Shell `0.6.2` (`AppHost`, `AfterScope`, `modal_session`, Light/Dark/System-Themes), Original V.06, Draufsicht V.04.2 und Klassisch V.05.1, PNG-Fallback, SVG-Brettvorschau mit Cache | Finale Inhaber-Bretter, native Sicht- und High-DPI-Prüfung |
| Bot (W07) | UCI-Adapter, asynchroner Controller, sechs Presets, Bereitschaftstest | Echte Engine nach ADR-001, Kalibrierung, Offline-Partie |
| Rätsel (W08) | Lokal verarbeitetes `lichess-core-20k` mit Seed, Ratingbändern bis 3000+ und SQLite-Index | Bündelung und Vertriebsweg separat freigeben. [IV-B](../reports/2026-11-28_W08-IV-B-lichess-produktdaten.md) |
| Daten (W09) | SQLite v8 im Engine-Analysis-Branch, archivierte Uhrdaten, automatische Restore-Recovery und eigenständige Trainingskandidaten | Profile (Q-012), ADR-004, native Dialoge macOS/Linux |
| Bedienung (W10) | DE/EN, Tastaturwege, Brett als Text, Fokusrückgabe | Native Skalierung 150/200 %, Screenreader, Ziffernblock |
| Qualität (W11) | 14-Job-Matrix nach jedem Merge, Policy-, Link- und Manifestprüfung | Installations-, Offline- und Artefaktabnahme |
| Vertrieb (W12) | Strategie dokumentiert | BLOCKED durch ADR-001, ADR-005, ADR-006 |

## Entscheidungen mit dem größten Hebel

Diese Owner-Entscheidungen geben die meiste blockierte Arbeit frei. Antwortformat und Vorschläge: [Offene Fragen](../questions/OPEN_QUESTIONS.md).

| Rang | Entscheidung | Gibt frei | Referenz |
| --- | --- | --- | --- |
| 1 | Engine- und Vertriebslizenz (Weg A: GPL-konformer Gesamtvertrieb, oder Alternative) | Echte Offline-Engine, Bot-Kalibrierung, jeder Installer | [ADR-001](../decisions/ADR-001_ENGINE_LICENSE.md), Q-001 |
| 2 | Lokal geprüfte Datenbasis für Connected Learning verwenden | Der Download und die lokale Realdatenverarbeitung sind für IV-B freigegeben | Q-022, [ADR-003](../decisions/ADR-003_PUZZLE_POLICY.md) |
| 3 | Ratingbereich und Paketgröße | Zuschnitt des mitgelieferten Rätselpakets | Q-008, Q-009 |
| 4 | Profilmodell (ein oder mehrere Profile) | Abschluss von W09, ADR-004 | Q-012, [ADR-004](../decisions/ADR-004_STORAGE.md) |
| 5 | Mock-Bot in Vorschau-Builds sichtbar oder ausgeblendet | Verhalten des Bot-Modus ohne echte Engine | Q-021 |
| 6 | Finale SVG-Bretter liefern | Abschluss der Brettgestaltung in W06 | Q-004, [Lieferformate](../../assets/boards/source/README.md) |
| 7 | Plattformpriorität und Apple Developer ID | Reihenfolge und Signatur der Installer | Q-007, Q-016, [ADR-006](../decisions/ADR-006_DISTRIBUTION.md) |
| 8 | Ablage des Arbeitsrepositorys außerhalb von OneDrive | Weniger Konfliktkopien und Phantom-Änderungen | Q-025 |

## Nächste Aufgaben

Nur offene Arbeit. Erledigte Punkte stehen unten unter „Abgeschlossen“.

| Priorität | Arbeit | Nächster Nachweis |
| --- | --- | --- |
| 1 | W10/W11 · Native Bedienabnahme | Manuelle Prüfung auf Windows und macOS bei 100/150/200 %, Screenreader-Stichprobe und physischer Ziffernblock. Regression und Protokollvorlage stehen im [Bediennachweis](../reports/2026-11-22_W10-W11-bedienabnahme.md). |
| 2 | W06 · Finale Brettgestaltung | Nach Lieferung der Inhaber-SVGs: Partie, Rätsel und beide Figurenansichten mit den Brettern prüfen, Assetregister mit Hashes ergänzen. |
| 3 | W05 · Tote Stellungen allgemein | Weitere verblockte Materialkombinationen und längere oder verzweigte Zwangsfolgen. Golden-Fixtures mit Quelle. [Bauernsperren](../reports/2026-11-21_W05-bauernsperren.md) |
| 4 | W09 · Native Dialoge | FEN-, PGN- und Ordnerdialoge auf macOS und Linux nativ prüfen. Profile nach Q-012. [FEN-Austausch](../reports/2026-11-21_W05-W09-fen-austausch.md) |
| Nach ADR-001 | W02/W07 · Echte Offline-Engine | Identifiziertes Binary mit Hash, vollständige Partie ohne Netz, Abbruch- und Absturzverhalten, Kalibrierplan für die sechs Stufen. |
| Nach IV-B | W08 · Connected Learning | Wiederhol- und Themenpfade auf stabilen IDs und dem lokalen Produktpaket aufbauen. [IV-B](../reports/2026-11-28_W08-IV-B-lichess-produktdaten.md) |
| Danach | W12 · Distribution | Installer, Lizenz- und Quellenbelege, Signaturen, Upgrade- und Offline-Tests, Inhaberfreigabe. Danach GitHub Releases und Software-Katalog. [Vertriebsstrategie](../release/RELEASE_STRATEGY.md) |

## Meilensteine bis 1.0 (PROPOSED)

Vorschlag zur Fortschreibung der historischen Zielmarken. Die Nummern gelten erst nach Owner-Bestätigung; der aktuelle Entwicklungsstand ist V.0.3.0 nach der [Versionspflege](../governance/GOVERNANCE.md#projektversion).

| Meilenstein | Inhalt | Ausgangskriterium | Blockiert durch |
| --- | --- | --- | --- |
| 0.3.0 · Interner Prototyp | Regeln, Brett, Bibliothek, Demo-Rätsel, DE/EN | W05, W06, W09, W10 ohne offene native Prüfpunkte; Owner-Abnahme der Bedienung | Native Abnahme, finale Bretter (optional als 0.1.x nachziehen) |
| Offline-Bot · Zielmeilenstein | Echte lokale Engine, kalibrierte Stufen | Vollständige Offline-Partie mit identifiziertem Binary; Kalibrierbericht | ADR-001, ADR-007, Q-021, Q-023 |
| Puzzle-MVP · Zielmeilenstein | Mitgeliefertes Rätselpaket, Profile, Fortschritt | Realdatenimport mit Bericht; P-05/P-06 erfüllt | Q-008, Q-009, Q-012, Q-022, ADR-003, ADR-004 |
| 0.9.0 · Release Candidate | Installer Windows/macOS, Lizenzhinweise, SBOM | Installations-, Update-, Deinstallations- und Offline-Nachweise je Plattform | ADR-005, ADR-006, Q-007, Q-016 |
| 1.0.0 · Release | GitHub Release und Software-Katalog | Ausdrückliches Owner-Release-Gate | Alle vorherigen |

## Abgeschlossen seit Einführung von V.0.0.1

Die Marmoransicht ist im Tk-Spielfenster umschaltbar. Normalbrett und
Marmoransicht verwenden dieselbe Partie. [Tk-Marmoransicht](../reports/2026-11-21_W06-marmoransicht-tk.md)

Der lokale Marmorprototyp unterstützt PGN- und FEN-Dateiaustausch sowie
eine per Tastatur bedienbare Zugwiedergabe. [Prüfnachweis](../reports/2026-11-21_W09-W10-marmorbrett-dateien-wiedergabe.md)

Das Puzzle Lab unterstützt Lernstandfilter, Versuchsverlauf, Neustart und
gestufte Hinweise. Aktive und gespeicherte Partien lassen sich separat
nachspielen. [Wiederholtraining](../reports/2026-11-21_W08-W09-wiederholtraining.md)
· [Rätselneustart und Partiewiedergabe](../reports/2026-11-21_W08-W09-raetselneustart-partiewiedergabe.md)

| PR | Inhalt | Merge-Lauf |
| --- | --- | --- |
| [#21](https://github.com/n05a-design/chess-and-chains/pull/21) | W06/W09/W10 · Desktop-Marmoransicht, PGN/FEN und Wiedergabe im WebGL-Prototyp | [14/14](https://github.com/n05a-design/chess-and-chains/actions/runs/44972693793) |
| [#17](https://github.com/n05a-design/chess-and-chains/pull/17) | W05 · Tote Stellungen bei geschlossener Bauernsperre | [14/14](https://github.com/n05a-design/chess-and-chains/actions/runs/44932980772) |
| [#16](https://github.com/n05a-design/chess-and-chains/pull/16) | W09 · Gespeicherte Partien in der Bibliothek suchen | [14/14](https://github.com/n05a-design/chess-and-chains/actions/runs/44932023205) |
| [#15](https://github.com/n05a-design/chess-and-chains/pull/15) | W10 · Brett als Text, Züge per Tastatur | [14/14](https://github.com/n05a-design/chess-and-chains/actions/runs/44931230803) |
| [#14](https://github.com/n05a-design/chess-and-chains/pull/14) | W05/W09 · FEN-Stellungen austauschen und spielen | [14/14](https://github.com/n05a-design/chess-and-chains/actions/runs/44916460337) |
| [#13](https://github.com/n05a-design/chess-and-chains/pull/13) | W06/W08/W09 · SVG-Brettcache und lokale Rätselpakete | [14/14](https://github.com/n05a-design/chess-and-chains/actions/runs/44909381782) |
| [#12](https://github.com/n05a-design/chess-and-chains/pull/12) | W10 · Auswahldialoge per Enter, Fokusrückgabe | [14/14](https://github.com/n05a-design/chess-and-chains/actions/runs/44905214890) |
| [#11](https://github.com/n05a-design/chess-and-chains/pull/11) | W05/W08/W10 · Folgecommits und Ablageabgleich | [14/14](https://github.com/n05a-design/chess-and-chains/actions/runs/44904083668) |
| [#10](https://github.com/n05a-design/chess-and-chains/pull/10) | W11 · Projektquellen und OneDrive-Stände zusammengeführt | [14/14](https://github.com/n05a-design/chess-and-chains/actions/runs/44901076786) |
| [#9](https://github.com/n05a-design/chess-and-chains/pull/9) | W10 · Brettfokus und Tastaturbedienung | [14/14](https://github.com/n05a-design/chess-and-chains/actions/runs/44869510471) |
| [#8](https://github.com/n05a-design/chess-and-chains/pull/8) | V.0.0.1 eingeführt, Roadmap abgeglichen | – |

Den Stand je Paket führt der [Paketabgleich](../reports/2026-11-21_W00-W12-paketabgleich.md), die lokale Ablage das [Dokumentations- und Ablageaudit](../reports/2026-11-21_W11-dokumentations-und-ablageaudit.md).

## Kritischer Pfad und Risiken

Lizenz-Gate → echte Engine → Kalibrierung → Installer → native Plattformabnahme → Release. Design, Rätselkatalog und Bedienabnahme laufen parallel. Keine Veröffentlichung vor Legal-, Quellen- und QA-Freigabe.

| Risiko | Wirkung | Gegenmaßnahme |
| --- | --- | --- |
| ADR-001 bleibt offen | Kein Bot, kein Installer | Entscheidung priorisieren; Mock-Tests halten den Adapter bereit |
| Git-Repository in OneDrive | Konfliktkopien, Moduswechsel, veraltete lokale Branches | Q-025; vor jedem Commit `git fetch` und Statusprüfung |
| Native Abnahme nur manuell möglich | TESTED ohne Plattformbeleg | Prüfprotokolle je Gerät unter `docs/reports/` |
| Kein Apple Developer ID | Unsigniertes macOS-Paket | Q-016 vor 0.9.0 klären |

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

## Historische Zielmarken und Versionspflege

- **F0**: historisches Planungsstarterpaket.
- **v0.3.0**: kontrollierter interner Board-/Regeln-Prototyp.
- **v0.3.0**: Offline-Bot-Prototyp nach Lizenzentscheidung.
- **v0.3.0**: Puzzle-MVP + Profile/Save.
- **v0.9.0**: Release Candidate mit Plattformabnahmen.
- **v1.0.0**: Erst nach explizitem Owner-Release-Gate.

Die Zielmarken sind frühere Planungswerte. Die aktuelle Entwicklungsnummer wird gemäß [Versionspflege](../governance/GOVERNANCE.md#projektversion) fortgeführt. Der Umfang richtet sich nach den [Work Packages](WORK_PACKAGES.md).

Den Stand der Folgephase dokumentiert der [Bericht F13–F26](../reports/2026-11-27_F13-F26-functional-completion.md).

Den Stand von Auftrag III dokumentiert der [Bericht zur Engine- und Analyseintegration](../reports/2026-11-28_phase-a-completion-phase-b-engine-analysis.md).
