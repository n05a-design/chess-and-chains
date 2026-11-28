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

## Gate III-2 – Sitzung, Archiv und Profil

- A1 ergänzt explizite Sitzungsphasen, bewussten Abbruch, die Bibliothekskopie
  bei CAS-Konflikt und die ausdrückliche Bestätigung eines Engine-Wechsels
  bei unverändertem Spielmodus. Engine-Wechsel werden im Snapshot belegt.
- A2 ergänzt Hauptvarianten-Uhrannotationen und native Anzeige importierter
  Werte, monotone aktive Spielzeit und historische Registry-Metadaten.
  Favoriten und Tags sind aus der Bibliothek bearbeit- und filterbar.
- A3 sichert jede Restore-Transaktion mit einem journalisierten,
  prüfsummengebundenen Rücksetzpunkt. Der Start validiert das Journal unter
  exklusiver Profil-Sperre. Zwei Desktop-Leases blockieren gemeinsam den
  Restore. Tests unterbrechen den Prozess sowohl zwischen
  Datenbankoperation und Journalstatus als auch während der Rücksetzung.

Die SQLite-Partiedatenbank bleibt bei Version 7. Neue Snapshotfelder sind
additiv. Der Backup-ZIP-Vertrag hält seine bisherigen Komponenten.
[Erweiterter Datenvertrag](../architecture/DATA_CONTRACTS.md)

## Gate III-3 – Laufzeit und Benchmark

Die produktive Auswahl zeigt eine fehlende Engine an. Der gekennzeichnete
Entwicklungsmock wird erst über den Engine-Dialog aktiviert. Die Analyse
wartet auf einen bereits laufenden Bot-Zug. Die UCI-Grenze begrenzt
Ausgabezeilen und Warteschlange und unterstützt begrenzte Knotensuchen.

Ein manueller Smoke-Lauf mit `--max-plies 4 --nodes 128` ergab zwei
ungewertete Partien mit Farbtausch und Exit 0. Der Ausgabevertrag trennt
reguläre Ergebnisse, technische Niederlagen und Abbrüche. Die reale
Kalibrierung wartet auf Auftrag IV-A. [Benchmark-Aufruf](../qa/BOT_CALIBRATION_PLAN.md)

## Gate III-4 – Analyse

Der analyseseitige SQLite-LRU bleibt außerhalb des Analyse-Archivs und
wird bei inkompatiblen oder beschädigten Ergebnissen wie ein Cache-Miss
behandelt. Der Fixture-Test startet den Dienst neu und zählt die
tatsächlichen UCI-Suchbefehle für identisches und geändertes Budget.
Kritische Momente verwenden bei geprüften Registry-Engines zwei
suchbeschränkte Läufe an derselben Wurzelstellung und die Perspektive
des ziehenden Spielers. Unabhängige Fixtures prüfen beide Farben.
Ältere Archivberichte behalten lesbare Schätzwerte.

## Gate III-5 – Trainingskandidaten

SQLite v8 speichert eigenständige Analyse-Trainingskandidaten. Der
Datensatz enthält die regelgeprüfte Stellung samt Historie, Partiezug,
Alternativen, Bewertungen, kritischer Kategorie und Engine-Referenz.
Ursprungspartie und Bericht sind optionale Fremdschlüssel. Ihre historischen
IDs bleiben im Datensatz, wenn der Benutzer diese Quellen löscht.
Der Inhaltsfingerabdruck verhindert identische Kandidaten. Der Kandidat
startet freies Stellungstraining. Die automatische Umwandlung in
bewertete Übungen gehört zu den folgenden Trainingspaketen.
