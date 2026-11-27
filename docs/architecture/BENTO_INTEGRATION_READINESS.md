# Fachliche Schnittstellen für Glide Bento

**Status IN_PROGRESS · V.0.3.0 · 27.11.2026.** Die Desktop-App verwendet die bestehende Glide Shell 0.6.2. Das spätere Präsentationssystem kann dieselben fachlichen Operationen aufrufen. [Architektur](ARCHITECTURE.md) · [Datenvertrag](DATA_CONTRACTS.md)

| Bereich | Befehle und Daten | Lebensdauer und Fehler |
| --- | --- | --- |
| Spiel | `GameController.new_game`, `resume_game`, `play_human`, `undo`, `redo`, `claim_draw`, `resign`. `GameView` liefert Stellung, legale Züge, Ergebnis, Bot- und Uhrzustand. | Ein Controller pro aktiver Partie. `ChessError` meldet unzulässige Befehle. `shutdown` beendet Worker und Engine. |
| Zeitkontrolle | `GameSetup.time_control`, `toggle_clock`, `adjudicate_timeout`, `ClockReading`. | Die monotone Uhr gehört dem Controller. Darstellung darf `clock_reading` zwischen Zustandsereignissen lesen. |
| Sitzungen und Bibliothek | `GameSessionSnapshot`, `Database.save_session` und `load_session`, `game_summaries`, `load_game`. | Die Datenbank validiert Zugfolge und Sitzungsformat. Die Präsentation unterscheidet Fortsetzen, Wiedergabe und eine neue Partie ab Stellung. |
| Analyse | `AnalysisService.start(AnalysisRequest)`, `AnalysisJob.progress` und `cancel`. `AnalysisProgress` liefert bestätigte Varianten und einen Jobstatus. `Database.analysis_reports` und `load_analysis_report` lesen abgeschlossene Bibliotheksanalysen. | Eine aktive Analyse pro Dienst. Eigener UCI-Prozess. Der Worker validiert die komplette Zugfolge und jede veröffentlichte Variante. |
| Rätsel und Training | `PuzzleSession`, `TrainingSelection`, `TrainingSession`, `summarize_attempts` und `Database.due_puzzle_ids`. `TrainingCheckpoint` sowie `Database.load_training_checkpoint` und `save_training_checkpoint` erhalten die Mattkette. | Aufgabenschlüssel bestehen aus Paket- und Rätsel-ID. Einzelresultate leben in SQLite. Eine Trainingsstellung verweist auf die Ausgangspartie und den Halbzug. |

Die Präsentation ruft Spielbefehle und `poll` auf ihrem Owner-Thread auf. `subscribe` liefert danach eine neue `GameView`. Bot-Aufträge tragen eine Generation und einen Halbzugindex. Ein Partiewechsel, Undo, Redo oder das Anhalten der Uhr invalidiert alte Aufträge. Analyse verwendet eine eigene Auftrags-ID und liefert nur Daten an den aufrufenden Thread. Beim Schließen des Analysedialogs wird der Auftrag abgebrochen. Die bestehende Shell verwaltet Tk-Timer und Fenster. Die nächste Oberfläche rendert Daten und übergibt Benutzereingaben an diese Befehle.

Der Wechsel in die Bibliothekswiedergabe oder Analyse lässt die aktive Partie als Datenquelle verfügbar. Die Bibliotheksanalyse arbeitet mit einer geladenen Kopie. Die Schachdomäne, der Controller, die Rätseldomäne und die Engine-Adapter lassen sich ohne Tk importieren. Der Foundation-Test prüft die Importgrenze statisch. Headless- und native Tests prüfen Spielfortsetzung, Analyse, Zeitgrenzen und Puzzle-Übergänge mit lokalen Testdaten.

Offen bleiben stabile gemeinsame Ansichtsdaten für Bibliothek, Training und Dashboard, eine Abstraktion der verbleibenden Desktop-Orchestrierung sowie die spätere Abnahme mit Glide Bento.
