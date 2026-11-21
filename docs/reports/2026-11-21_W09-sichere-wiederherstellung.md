# W09 – SQLite-Sicherungen vor der Wiederherstellung prüfen

**V.0.0.1 · 21.11.2026 · Codex, KI-gestützt.**
Branch `codex/chess-chains-w09-restore-validation`, Startpunkt
`80bb1ce914d5266065504120b1ee0ac8d2105313`. Die Änderung ist in
`4e5eae5aeae8a43c739449f07b188f4e3b551338` enthalten.
`origin/main` wurde beim Start bei `6bcd9ada580be10f289c34dd0040be62297597d2`
bestätigt. Der W09-Stand liegt lokal.

## Befund und Umsetzung

In einer Probe mit zwei temporären SQLite-Datenbanken enthielt die aktive
Bibliothek eine Partie mit `1. e4`. Die Sicherung enthielt `1. d4` im
PGN und `g1f3` in der gespeicherten UCI-Zugliste. Auf der Basis endete
`Database.restore()` erfolgreich und ersetzte die aktive Datenbank.
`Database.load_game()` lehnte die eingespielte Partie danach wegen des
Widerspruchs ab. Die Probe protokollierte beide Ergebnisse per Python,
Exitcode 0.

`Database.restore()` öffnet die Sicherungsdatei lesend, kopiert sie wie
bisher in ein temporäres Verzeichnis und migriert sie bei Bedarf. Nach den
Strukturprüfungen lädt es jede gespeicherte Partie aus dieser Kopie mit
dem regulären `Database.load_game()`. Das prüft Ausgangsstellung, PGN,
UCI-Zugliste, Ergebnis und gegebenenfalls den gespeicherten Endgrund.
Erst danach legt der Ablauf die Sicherung des aktiven Stands an und
überträgt die geprüfte Datenbank. Die Fehlermeldung nennt die Partie und
die ausgewählte Sicherung.

Die Prüfung verwendet den bestehenden Lesepfad für SQLite-Schema 3
einschließlich der Regeln für ältere Partien aus [W05](2026-11-21_W05-tote-stellungen-und-altpartien.md).
Sicherungen mit unlesbaren Partien werden vollständig zurückgewiesen.
Bei großen Bibliotheken wächst der Validierungsaufwand mit den
gespeicherten Partien und Halbzügen.

## Prüfungen

Windows 11 Pro x64, Python 3.15.1. Alle Datenbanken lagen in temporären
Verzeichnissen. `PYTHONWARNINGS=error::ResourceWarning` war für den
Gegenlauf gesetzt.

- Vor der Korrektur schlug der neue Restore-Test in beiden Subtests fehl
  (widersprüchliche Zugliste und widersprüchliche Aufgabe). Beide
  Sicherungen wurden fälschlich eingespielt. Die zwei ergänzenden
  Abbruchtests bestanden auf der Basis. Der gezielte Vorlauf verwendete
  `python -m unittest` für diese drei Methoden, Exitcode 1.
- `python -m unittest tests.test_storage -q` bestand mit **29 Tests**,
  Exitcode 0. Die inkonsistenten Sicherungen lassen die aktive und die
  ausgewählte Datenbank bytegleich und erzeugen keine Rückfallsicherung.
  Ein simulierter Berechtigungsfehler beim Anlegen der Rückfallsicherung
  lässt die aktive Datenbank ebenfalls bytegleich.
- Ein ausgelöster Abbruch im SQLite-Fortschrittscallback während der
  aktiven Kopie bewahrte im Test beide bisherigen Partien und die
  Rückfallsicherung. Der erfolgreiche Testlauf stellte Partien und
  Rätselfortschritt aus der Sicherung wieder her und konnte den Stand vor
  der Wiederherstellung aus der Rückfallsicherung lesen.
- `py -3.14 -m unittest tests.test_storage -q` mit Python 3.14.7
  bestand ebenfalls mit **29 Tests**, Exitcode 0.
- `python -m unittest discover -s tests -q` prüfte Tree
  `2c7b9cd145cbdf227e8392264c96e5f8c5dca621` vor Ergänzung dieses
  Ergebnisses. Windows 11 Pro x64, Python 3.15.1/Tk 9.0.4,
  `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`,
  `PYTHONWARNINGS=error::ResourceWarning` und `PYTHONFAULTHANDLER=1`.
  **202 Tests bestanden**, keine Skips, Exitcode 0 (100,736 Sekunden).
  `verify_starter.py`, `verify_document_links.py`, `check_policy.py`,
  `python -m compileall -q src app scripts tests` und `git diff --check`
  endeten ebenfalls mit Exitcode 0.

## Nächste Abnahmen

1. W09 bleibt für den belegten Umfang `TESTED`. Native Plattformabnahme
   auf macOS und Linux, das Profilmodell nach Q-012 sowie ADR-004 stehen aus.
2. Bei einer Freigabe für die GitHub-Veröffentlichung den Branch in der
   plattformübergreifenden CI prüfen. Weitere Aufgaben stehen in der
   [Roadmap](../roadmap/ROADMAP.md).

Für einen Rollback lassen sich Code-Commit und zugehörige Dokumentation
revertieren. Die Änderung arbeitet auf dem bestehenden SQLite-Dateiformat.
