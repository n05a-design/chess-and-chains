# W10 – Brett als Text lesen und Züge spielen

**V.0.0.1 · 21.11.2026 · KI-gestützt.** „Brett als Text…“ ist für Partie,
Zugliste und Rätsel direkt über dem Brett erreichbar. Die Listen zeigen
besetzte Koordinaten, Farbe und Figur sowie die legalen Ziele der Auswahl.
Umwandlungen erscheinen als eigene Wahl pro Figur. Die Stellung aktualisiert
sich nach Spielerzug, Botzug und Rätselantwort. Für das Ziehen gelten die
bestehenden Partie- und Rätselregeln.

Pfeiltasten ändern die Auswahl. Enter wechselt von der Figur zum Ziel und
führt den gewählten Zug aus. Escape schließt den Dialog und stellt den
vorherigen Fokus wieder her. Während eines Botzugs und nach Partieende
bleibt die Stellung lesbar. Sobald keine Züge angeboten werden, ist
„Zug spielen“ deaktiviert.

## Prüfumfang

Unter Windows mit Python 3.15.1/Tk 9.0.4 und verpflichtendem Tk-Display
bestand `python -m unittest tests.test_app_integration.TextBoardUiTests tests.test_i18n -q`
mit 10 Tests und Exitcode 0. Der Tastaturtest sendet Pfeil, Enter und Escape
an die fokussierten Widgets. Ein weiterer Test spielt eine Turmumwandlung
und löst das erste Demo-Rätsel. Die Plattform-CI und die Screenreader-Probe
sind eigene Nachweise. Ein Rollback erfordert keine Datenmigration.

## Übergabe

1. Plattform-CI mit Fokus auf Aqua-Tastatur und Fokusrückkehr verfolgen.
2. Screenreader-Ansagen für Listen, Auswahl, Zugmeldung und Dialogfokus
   auf den Zielsystemen prüfen.
