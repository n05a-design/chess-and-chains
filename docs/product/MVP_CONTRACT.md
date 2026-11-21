# MVP Contract 0.1 – noch zu bestätigen

Status: **PROPOSED**, nicht abgenommen.

| ID | Nutzen / Fähigkeit | Akzeptanz- und UX-Kriterium | Voraussetzung / Gate | Nachweis |
| --- | --- | --- | --- | --- |
| P-01 | Ein Brett, das eine Partie klar und korrekt darstellt | 64 eindeutig angeordnete Felder, korrekte Koordinaten und Brettorientierung; Auswahl und letzter Zug sind erkennbar | W05/W06; eigene oder freigegebene Assets | Headless-Board-/Koordinatentests plus Tastatur-/DPI-UI-Prüfung |
| P-02 | Eine Standardpartie ohne illegale Züge spielen | Schach, Matt, Patt, Rochade, en passant, Umwandlung und geltende Remisregeln sind korrekt; ungültige Züge werden sichtbar abgewiesen | W05; Regelwerk nach ADR-001 | Regeltests, bekannte Sonderstellungen, FEN/PGN-Roundtrip |
| P-03 | Ohne Internet gegen einen lokalen Bot spielen | Nur lokal konfigurierte Engine; Timeout/Absturz blockiert weder UI noch Partie und zeigt eine verständliche Meldung | W07 + ADR-001; keine Engine-Bündelung vor Freigabe | UCI-Prozess- und Offline-Tests ohne Netzabhängigkeit |
| P-04 | Eine passende Bot-Herausforderung wählen | Mindestens sechs reproduzierbare Presets; Stärke wird nicht als Elo versprochen, bevor sie gemessen ist | W07; konkretes Engine-Profil | Wiederholbare Profiltests und dokumentierter Match-Benchmark |
| P-05 | Taktik mit nachvollziehbarer Schwierigkeit trainieren | Jedes Standard-Puzzle hat Puzzle-Rating >= 1000; Gegner-Setupzug wird vor der Nutzerlösung angewendet; alle Lösungszüge sind legal | W08; Datenquelle und Weitergabe geprüft | Import-/Positions-/Lösungsvalidierung mit Grenzfällen |
| P-06 | Trainingsfortschritt behalten | Status, Fehler und benötigte Zeit werden lokal gespeichert und nach Neustart korrekt angezeigt | W09; Speicherort nach ADR-004 | Persistenz-, Wiederherstellungs- und Migrationstests |
| P-07 | Das Brett persönlich gestalten | Nur dokumentierte Assets; Figuren-/Brettwechsel bleibt bei 100/150/200 % und Tastaturbedienung brauchbar | W06; Q-003/Q-004 und ADR-005 | Asset-Register plus DPI-, Kontrast- und Fokusprüfung |
| P-08 | Partien mit anderen Schachwerkzeugen austauschen | PGN/FEN-Import und -Export roundtrippen; fehlerhafte Eingaben werden begrenzt und verständlich abgewiesen | W05/W09; Formatvertrag | Gültige und absichtlich fehlerhafte Import-/Export-Fixtures |
| P-09 | Die App auf Deutsch und Englisch bedienen | Kerntexte sind lokalisiert, Kataloge haben gleiche Schlüssel und keine stillen Fallbacks | W10; Startsprache noch offen | Katalogparität, Missing-Key- und Tastaturtests |
| P-10 | Einen nachvollziehbar geprüften Desktop-Build erhalten | Installer, Quellen-/Lizenzhinweise und Prüfsummen passen zum tatsächlich getesteten Artefakt | W11/W12 + ADR-001/005/006 | Plattformbezogene Install-/Offline-/Update-/Uninstall-Nachweise |

Die Spalte „Nachweis“ nennt Abnahmeanforderungen. Den tatsächlichen Stand zeigt der Abschnitt „Erfüllungsstand“.
Akzeptanzkriterien sind vorgeschlagen und können ohne Issue/Owner-ADR nicht
still erweitert werden.

## Erfüllungsstand V.0.0.1 (21.11.2026)

Abgleich der vorgeschlagenen Kriterien mit dem Code auf `main` (`1acd9bd`). „Automatisiert geprüft“ heißt: Tests bestehen in der 14-Job-Matrix. Es ersetzt weder native Abnahme noch Owner-Bestätigung.

| ID | Stand | Beleg | Offen |
| --- | --- | --- | --- |
| P-01 | Automatisiert geprüft | [Brett-UI](../reports/2026-11-20_W06_board-ui.md), [Figuren V.02](../reports/2026-11-21_W06-figurenschatten-v02.md) | Native DPI- und Sichtprüfung |
| P-02 | Automatisiert geprüft | [Regelkern](../reports/2026-11-20_W05_chess-core.md), [Bauernsperren](../reports/2026-11-21_W05-bauernsperren.md) | Allgemeine tote Stellungen, Owner-Abnahme |
| P-03 | Nur mit Mock-Engine | [UCI-Bereitschaft](../reports/2026-11-21_W07-uci-verbindungstest.md) | Echte Engine nach ADR-001, Offline-Partie |
| P-04 | Teilweise | Sechs Presets ohne Kalibrierung | Benchmark nach ADR-007 |
| P-05 | Mit Fixtures geprüft | [Lokale Pakete](../reports/2026-11-21_W08-W09-lokale-raetselpakete.md), [Qualitätsfilter](../reports/2026-11-21_W08-puzzle-qualitaetsfilter.md) | Realdaten nach Q-022 |
| P-06 | Automatisiert geprüft | [Rücksicherung](../reports/2026-11-21_W09-sichere-wiederherstellung.md) | Profile nach Q-012, benötigte Zeit je Rätsel prüfen |
| P-07 | Teilweise | [SVG-Brettcache](../reports/2026-11-21_W06-svg-brettcache.md) | Finale Bretter, 150/200 % nativ |
| P-08 | Automatisiert geprüft | [FEN-Austausch](../reports/2026-11-21_W05-W09-fen-austausch.md), [Bibliothekssuche](../reports/2026-11-21_W09-partiebibliothek-suche.md) | Native Dateidialoge macOS/Linux |
| P-09 | Automatisiert geprüft | [Rätselthemen](../reports/2026-11-21_W10-raetselthemen.md), [Brett als Text](../reports/2026-11-21_W10-brett-als-text.md) | Startsprache Q-010, Screenreader |
| P-10 | Nicht begonnen | – | W12 nach ADR-001, ADR-005, ADR-006 |

## Release-Blocker

Kein Release bei ungeklärter Vertriebs-Lizenz, illegalen Schachzügen, Crash beim Engine-Tod, beschädigter Datenmigration, Rätseln unter 1000 in ausgelieferter Standardauswahl, nicht belegten Runtime-Komponenten, ungeprüften System-Installationen.

## Änderungsregel

Scope-Änderung erfordert Issue + Owner-ADR. Ein Entwickleragent darf neue Ideen in die Backlog-Liste schreiben, aber nicht heimlich zum MVP hinzufügen.
