# Phase A und Engine-/Analyseintegration

Stand zum Beginn von Auftrag III. Der separate Entwicklungsbranch `codex/engine-analysis-integration` basiert auf dem am 28.11.2026 abgeglichenen `main` bei `6dcd12f187d19a878a6ad0ae81de37c251c00991`. Der zugehörige GitHub-Lauf war mit 14 erfolgreichen Jobs abgeschlossen. [PR #26](https://github.com/n05a-design/chess-and-chains/pull/26) · [Merge-CI](https://github.com/n05a-design/chess-and-chains/actions/runs/46084335806)

## Phase 0 – Delta-Audit

| Paket | Soll | Bereits implementiert | Nachweis | Restarbeit |
| --- | --- | --- | --- | --- |
| B1 | Einheitliche, persistente Engine-Identität | Registry mit SHA-256 und UCI-Bereitschaftstest, separate Legacy-Session-ID | `test_engine_registry`, projekteigene Fixtures | Persistenz, Startfreigabe und Integration |
| A1 | Sitzungszustände und Konfliktauflösung | Snapshot, CAS, Uhr, Undo/Redo, Remisangebot | `test_game_session`, `SessionRecoveryUiTests` | Konfliktexport, Lebenszyklus und dokumentierter Engine-Wechsel |
| A2 | Archivmetadaten und Bedienung | Uhrverlauf, API für Favoriten und Tags, Deduplizierung | `test_storage`, native Wiedergabe | Historische Engine-Metadaten, PGN-Uhr und Bedienung |
| A3 | Automatische Restore-Recovery | Validiertes ZIP, Sicherheitskopie, manuelle Rückkehr nach Prozessabbruch | `BackupBundleTests` | Journal, Profil-Lock, automatische Recovery |
| B2 | Kontrollierte Engine-Laufzeit | UCI-Handshake, Abbruch, Prozessbereinigung, Generationen | `test_uci_engine`, `test_game_controller`, Mock | Kein automatischer Produktionsfallback, Ressourcengrenzen |
| B3 | Reproduzierbarer Benchmark | Kalibrierungsentwurf | [Kalibrierungsplan](../qa/BOT_CALIBRATION_PLAN.md) | Ausführbarer Runner, deterministischer CI-Nachweis |
| B4 | Persistenter Analyse-Cache | Prozesslokaler Cache, getrenntes Analysearchiv | `test_engine_analysis`, `test_storage` | Neustartnachweis, Cache-Identität und Bereinigung |
| B5 | Vergleichbare kritische Momente | Positionsanalyse mit Perspektivnormalisierung | `test_engine_analysis`, Mock | Gleiche Ausgangsstellung, Matt und Grenzen |
| B6 | Eigenständige Trainingskandidaten | Gespeicherte Trainingsstellungen an Ursprungspartie gebunden | `test_storage`, `AnalysisArchiveUiTests` | Kandidatenidentität, Provenienz, Entkopplung |
| QA | Funktion und Regression über drei Betriebssysteme | 467 Tests, GitHub-Matrix und Offline-Stichprobe auf dem Ausgangsstand | Bericht zu PR #26 | Neue Integrationsnachweise und Plattformmatrix |

Reale Engine-Abnahme und Distribution bleiben den Freigaben aus Q-001, ADR-001 und Auftrag IV-A vorbehalten. Der offizielle Rätseldownload wartet auf Q-022 und Auftrag IV-B.

## Gate III-1 – Engine-Identität

Die persistente Registry verwendet einen eigenen lokalen SQLite-Speicher mit
Schema 1. Befunde und Freigaben sind von der portablen Profilsicherung
getrennt. Bot und Analyse starten über denselben freigegebenen
Konfigurationsvertrag. Die Referenz im Partiedatensatz bezeichnet die
logische ID und den Konfigurationsfingerabdruck. Legacy-Referenzen werden
weiter gelesen und behalten ihre geringere Aussagekraft.

Die projekteigene Protokoll-Fixture belegt Neustart, zeitgesteuerte Bot-Partie,
Autor, Konfigurationsoptionen und geschützten Prozessstart. Ersetztes Binary
bei unveränderten Dateimetadaten, veränderte Ressource und widerrufene
Registrierung unterbinden den Prozessstart. Ausführung und Kalibrierung
einer freigegebenen Dritt-Engine stehen für Auftrag IV-A aus.
