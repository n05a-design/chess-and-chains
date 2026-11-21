# W09 – Gespeicherte Partien suchen

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Der lokale Folgebranch setzt
auf W10-Commit `c5b22dd605e026d3174c27cb4586a725bc5e6521` auf.
Die Partiebibliothek zeigt die bereits vorhandenen Spielernamen und
Veranstaltungen aus PGN. Die Suche kombiniert Teilbegriffe, ignoriert
Groß-/Kleinschreibung und berücksichtigt die angezeigte Partienummer,
das Speicherdatum und Ergebnis. Enter wechselt zur Trefferliste.
Bei leerer Trefferliste sind Öffnen und Export deaktiviert. Der Import
bleibt verfügbar. Geöffnete und exportierte Treffer werden über ihre
ursprüngliche Partiekennung zugeordnet.

Die Übersicht liest PGN-Kopfdaten ohne Zugwiedergabe. Öffnen und
Export verwenden weiterhin die vollständige Validierung.
SQLite-Schema und gespeicherte PGNs bleiben kompatibel.
Ein Rollback erfordert keine Datenmigration.

## Prüfungen

Windows 11 Pro, Tk 9.0.4 und verpflichtendes Tk-Display.
`python -m unittest tests.test_app_integration.StorageAndLocaleUiTests tests.test_storage tests.test_chess_core tests.test_i18n -q`
bestand unter Python 3.15.1 mit 72 Tests, Exitcode 0.
`py -3.14 -m unittest tests.test_app_integration.StorageAndLocaleUiTests tests.test_app_integration.TextBoardUiTests tests.test_storage tests.test_i18n -q`
bestand unter Python 3.14.7 mit 57 Tests, Exitcode 0. Die Regression
prüft kombinierte Unicode-Suche, ausbleibende Treffer und Zuordnung
der echten PGN-Datei und der geöffneten Partie. Der Dateiwähler
lieferte im Test einen isolierten Pfad. Struktur-, Link-, Policy-,
Kompilierungs- und Diff-Prüfung endeten mit Exitcode 0.

## Übergabe

Der [PR #16](https://github.com/n05a-design/chess-and-chains/pull/16) ist
in `main`. [PR-CI](https://github.com/n05a-design/chess-and-chains/actions/runs/44931796442),
[Push-CI](https://github.com/n05a-design/chess-and-chains/actions/runs/44931791296)
und [Merge-CI](https://github.com/n05a-design/chess-and-chains/actions/runs/44932023205)
bestanden mit je 14 Jobs. Auf macOS liefen je 65 Tk-Tests mit
Python 3.11 und 3.14. Die Logs dokumentieren den erfolgreichen Suchtest
samt Öffnen und Export.

1. Native Bedienabnahme für Systemdialoge und Screenreader nach der
   [QA-Matrix](../qa/TEST_PLAN.md) weiterführen.
