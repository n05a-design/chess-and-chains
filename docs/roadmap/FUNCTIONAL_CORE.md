# Funktionsinventar F01–F12

**V.0.3.0 · 27.11.2026 · Entwicklungsgrundlage GitHub `main` bei `2c4a594`.** Die IDs stammen aus dem Masterauftrag Functional Core & Application Integration. TESTED bezeichnet den in der jeweiligen Zeile genannten Umfang. Übergreifende Paketabnahme und Release-Freigabe stehen aus. [Ausgangsstand](../reports/2026-11-27_F01-F12-functional-core.md) · [Analysearchiv und Mattkette](../reports/2026-11-27_F07-F10-analysearchiv-mattkette.md)

| ID | Zweck und fachliche Schnittstelle | Daten und Abhängigkeit | Nachweis und verbleibendes Gate |
| --- | --- | --- | --- |
| F01 | GitHub-Abgleich, Funktionsinventar und CI-Zuordnung über `scripts/ci_tests.py` | Entwicklungswerkzeug pytest und CI-Workflow | Inventar, Figurensatztests und Basis-CI geprüft. Branch-CI und laufende Aktualisierung bleiben offen. |
| F02 | Partienschicht `GameController.resume_game` und `GameSessionSnapshot`. Start, Zug, Undo/Redo, Partieende und Schließen sichern. Bibliotheksaktionen erhalten explizite Öffnungsabsichten. | Ein SQLite-Slot. Spielsetup, Uhr, FEN, Zugfolge und Ende. Engine-Konfiguration aus lokalen Einstellungen. | `test_game_session`, `SessionRecoveryUiTests` und `test_storage`. Wiederherstellung bei realem Engine-Wechsel, separate Archivzeit und erweitertes Lebenszyklusmodell offen. |
| F03 | `ChessGame.outcome` erkennt zusätzliche tote Stellungen aus verzweigten erzwungenen Schlagzügen. `mate_possibility` prüft Mattmöglichkeiten für eine Seite mit begrenztem Suchbudget. Deterministische Partien prüfen Königsdeckung, FEN und jeden Undo/Redo-Zustand. | FIDE-Regeln ab 1.1.2023. Eigenständiger Regelkern. | `test_chess_core`, `test_chess_golden`. Allgemeine Mattmöglichkeit, Remisvereinbarung und Vergleich gegen unabhängige Implementierung offen. |
| F04 | `EngineRegistry` und Engine-Dialog prüfen lokalen UCI-Prozess, Dateifingerabdruck und Optionen. Der Dialog merkt sich ausdrücklich gespeicherte Pfade. | Prüfmetadaten im Speicher, Pfadauswahl in lokalem Settings-JSON. Kein Download und keine Bundles. | `test_engine_registry`, `test_uci_engine`, GUI-Bereitschaftsprüfung mit Mock. Reale Engine, Kalibrierung und persistierte Prüfmetadaten offen. |
| F05 | `import_lichess_file`, `write_pack`, `read_pack`, `PackLibrary`. Temporärer SQLite-Duplikatindex, Streaming, Verteilungen und kompatible Paketrevisionen. | Lokale CSV/CSV.zst und JSONL-Pakete. Nutzerdaten separat. | `test_puzzles`, synthetische Läufe bis 50.000 Zeilen. Indizierter Laufzeitkatalog in der Folgephase umgesetzt. Realdatenabnahme offen. |
| F06 | `GameClock`, `GameSetup.time_control` und `UCIEngine.go_clock`. Fischer-Inkrement, elf Presets, eigene Zeitkontrollen, pausierte Wiederherstellung und UCI-Zeitparameter. | Zeitstände je gespieltem Halbzug im SQLite-Snapshot. Monotone Zeitquelle und UI-Owner-Thread. | `test_game_clock`, `test_uci_engine`, `SessionRecoveryUiTests`. Beweisbare Siege und Remis nach Zeitablauf werden automatisch gewertet. Unklare Stellungen bleiben zur Entscheidung offen. Uhrdaten im Partiearchiv in der Folgephase umgesetzt. Native Standby-Abnahme offen. [Zeitablauf](../reports/2026-11-27_F03-F06-zeitablauf.md) |
| F07 | `Database` migriert zu v5. Standardprofil `local`, Snapshot, Trainingskandidaten, Analyseläufe und Trainingsstände. Rücksicherung prüft neue Datensätze vor dem Tausch. | SQLite mit bestehender Migrations- und Backup-Strategie, persönliche Einstellungen als eigenes JSON. | `test_storage`, `test_game_session`. Mehrprofil-Scope, dauerhafter Analyse-Cache und Settings-Backup offen. |
| F08 | `AnalysisService` analysiert Stellung, ausgewählte Halbzüge oder ganze Partie. Scores aus Weißsicht, MultiPV, FEN/Zugvalidierung, Abbruch, kritische Momente. | Separater UCI-Prozess. Versionierter Cache pro Prozess bei bekannter Engine-Version. Vollständige Bibliotheksanalysen sind als Berichte in SQLite gespeichert. | `test_engine_analysis` mit Protokoll-Fixtures. Reale Engine, persistenter Cache und Klassifikation von Mattwerten offen. |
| F09 | `summarize_attempts`, `TrainingSession`, `TrainingChain` und Fälligkeitsfilter. Wiederholungen aus der Versuchsreihe ableiten. Eine kuratierte Mattkette ist im Puzzle Lab fortsetzbar. | Puzzle-Versuche, Paket-/Rätsel-ID, UTC und versionierte Kettenstände. | `test_training`, nativer Wiederaufnahmetest und transaktionaler Storage-Test. Themenstatistik und Verwaltung mehrerer Ketten offen. |
| F10 | Bibliothek und aktuelle Partie erreichen Analyse. Aus kritischen Positionen gespeicherter Partien entstehen nachvollziehbare Trainingsstellungen zum freien Üben. Bibliothek kann eine neue Partie ab der ausgewählten Stellung starten. | Trainingskandidaten in SQLite mit Referenz auf Originalpartie und Halbzug. Keine Bewertung als veröffentlichtes Rätsel. | Analyse-, Speicher- und GUI-Tests für Teilstrecken. Analyseberichte sind nach Neustart offline verfügbar. Validierte Übungen in der Lernwarteschlange bleiben offen. |
| F11 | CI-Inventar, native Regressionen, deterministische Uhrtests und abrupt beendete SQLite-Schreibtransaktion. | Vorhandene OS-Matrix, isolierte lokale Testdaten. | Mac arm64 lokal. Windows/Linux für diesen Branch, Langzeitbelastung, Offline- und Release-Abnahme offen. |
| F12 | Typisierte GameView-, UCI-, Trainings- und Datenbankverträge. Fachpakete per Importgrenze abgesichert. | Präsentation über vorhandene Glide Shell 0.6.2. Künftige Bento-Verträge in der Architekturdokumentation. | Foundation-Test und lokale Regression. Gemeinsamer Dashboard-Datenvertrag und spätere Bento-Abnahme offen. |

## Weiterführung

1. Weitere offene Mattfälle absichern, Uhrzustände im Partiearchiv erhalten und native Standby-Prüfung ergänzen.
2. Analysepositionen mit validiertem Lernziel in die Trainingswarteschlange aufnehmen. Themenstatistik und weitere Ketten ergänzen.
3. Große Kataloge über einen indizierten Lesezugriff öffnen und nach Q-022 mit Realdaten prüfen.
4. Typisierte Ansichtsdaten für Bibliothek und Training vervollständigen und die vollständige Plattformmatrix ausführen.

## Folgephase F13–F26

Der Umsetzungs- und Prüfstand der nachfolgenden Arbeitspakete steht im
[Bericht zur Produktintegration](../reports/2026-11-27_F13-F26-functional-completion.md).

## Auftrag III – Engine und Analyse

Spiel und Analyse verwenden die persistente lokale Engine-Registry mit
gemeinsamem Konfigurationsfingerabdruck und erneuter Prüfung beim Start.
[Auftragsbericht](../reports/2026-11-28_phase-a-completion-phase-b-engine-analysis.md)

Die zweite Ausbaustufe ergänzt Sitzungsphasen, getrennte Archivierung von
Konfliktständen, bestätigte Engine-Wechsel, Hauptvarianten-Uhrannotationen,
Bibliothekslabels und automatische Rückkehr nach einem unterbrochenen
Profil-Restore.

Die Engine-Laufzeit startet den Entwicklungsmock nach ausdrücklicher
Auswahl. Die Analyse verwendet einen versions- und konfigurationsgebundenen
SQLite-Cache und getrennte Same-Position-Suchen. SQLite v8 hält
eigenständige Kandidaten auch nach dem Löschen ihrer Ursprungspartie.
Die reale Engine- und Lichess-Abnahme folgt in den Aufträgen IV-A und IV-B.
