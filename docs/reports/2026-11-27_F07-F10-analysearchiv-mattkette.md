# Analysearchiv und wiederaufnehmbare Mattkette

**27.11.2026 · Functional-Core-Branch · Ausgangspunkt `acfcd65`, GitHub-`main` `2c4a594`.**

## Umsetzung

- Eine abgeschlossene Analyse aus der Partiebibliothek wird mit der Partie-ID und einer eindeutigen Lauf-ID gespeichert. Im Spielmenü öffnet „Gespeicherte Analysen…“ den Bericht offline. Varianten, Bewertungen, Engine-Angaben und kritische Positionen werden wiederhergestellt. Für kritische Stellungen bleibt das Speichern als freie Trainingsstellung verfügbar.
- Die „Matt-Trainingskette“ im Spielmenü öffnet drei kuratierte Aufgaben im vorhandenen Puzzle Lab. Die App sichert die aktuelle Zugfolge, Hinweisschritte, Fehler und aktive Dauer. Beim Verlassen des Puzzle Labs oder der App pausiert das Training. Eine eindeutige Versuch-ID und eine gemeinsame SQLite-Transaktion verhindern doppelte Wertung. Eine veraltete Programminstanz kann neueren Fortschritt durch die Revisionsprüfung nicht überschreiben.
- SQLite v5 ergänzt `analysis_reports`, `training_checkpoints` und eine optionale eindeutige Versuch-ID. Berichte bleiben an die Quellpartie gebunden. Die Rücksicherung prüft Berichtsinhalte, Varianten und Trainingsstände vor dem Austausch der aktiven Datenbank.

## Prüfung

macOS arm64, Python 3.14.5, Tk 9.0.3. Tests verwendeten temporäre App-Daten und ein vorhandenes UCI-Protokoll-Fixture. Der Entwicklungsstand vor dieser Runde wurde mit `git fetch origin` abgeglichen.

- `python3 -m unittest tests.test_engine_analysis tests.test_storage tests.test_training tests.test_i18n tests.test_app_integration.PuzzleUiTests.test_mate_chain_resumes_a_hint_and_grades_once_after_reopening -q` lief mit 76 Tests und Exitcode 0.
- `python3 -m unittest tests.test_app_integration.AnalysisArchiveUiTests tests.test_storage.DatabaseTests.test_v4_migration_preserves_games_and_progress tests.test_storage.DatabaseTests.test_chain_save_is_transactional_and_stale_writer_cannot_duplicate_attempts -v` lief mit drei Tests und Exitcode 0. Der native Archivtest hat einen Bericht erzeugt, die App neu geöffnet und kritische Stellungen ohne Engine-Prozess angezeigt. Die Storage-Tests prüften Migration, Wiederherstellung und veraltete Revisionen.
- `python3 -X faulthandler -m unittest discover -s tests -v` mit `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1` und `PYTHONWARNINGS=error::ResourceWarning` lief mit 430 Tests und Exitcode 0.
- `python3 scripts/ci_tests.py inventory` erkannte 441 Tests. `python3 scripts/ci_tests.py pytest` prüfte alle elf Figurensatztests, Exitcode 0.
- `python3 -m glide_shell.selftest` und `python3 -O -m glide_shell.selftest` meldeten je 13/13, Exitcode 0.
- `python3 -m pip wheel --no-index --no-build-isolation --no-deps` baute das Wheel in einem temporären Quellverzeichnis. Die isolierte Installationsprobe startete den Headless-Check und öffnete eine neue Datenbank mit Schema v5, Exitcode 0.

## Abnahmegrenze und Weiterführung

Gespeichert werden vollständige Analysen aus der Bibliothek. Einzelstellungsanalysen bleiben im jeweiligen Dialog verfügbar. Persistente Berichte sind für Menschen wieder zu öffnen. Der prozesslokale Suchcache arbeitet weiterhin separat. Reale Engine-Abnahme, eine allgemeine Verwaltung mehrerer Ketten und eine Bewertung aus Analysepositionen abgeleiteter Übungen bleiben offen. [Funktionsinventar](../roadmap/FUNCTIONAL_CORE.md)

Die Arbeit war KI-unterstützt. Für eine Rückkehr zum Stand vor der Migration gilt die automatisch erzeugte `.pre-v5-*.bak`-Sicherung. Sie enthält den Datenstand vor dem Upgrade. Neue Analyse- und Kettendaten liegen im v5-Bestand.
