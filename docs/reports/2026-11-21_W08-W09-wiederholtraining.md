# W08/W09 – Wiederholtraining und Versuchsverlauf

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Code und Regression in
`6960438b39864ca1089772035000bc333932412e` auf
`codex/chess-chains-w08-w09-wiederholtraining`.

Der Lernstand lässt sich mit Thema und Wertung kombinieren. „Ungelöst“
zeigt Aufgaben ohne gespeicherten Erfolg. „Wiederholen“ zeigt bereits
versuchte Aufgaben ohne fehlerfreie Lösung. Eine Lösung mit Fehlern oder
Hinweisen kann damit zur Wiederholung angeboten werden. Die aktuelle
Aufgabe und ihre Rückmeldung bleiben nach dem Abschluss sichtbar.
„Nächstes Rätsel“ aktualisiert den Lernstandfilter und geht in der
Reihenfolge des Pakets weiter. Gibt es keinen Treffer, bleiben die
Filter erreichbar.

Zu einer bearbeiteten Aufgabe zeigt das Rätsellabor die Anzahl
abgeschlossener Versuche, die beste Lösungszeit und Ergebnis, Fehler,
Hinweise und Zeit des letzten abgeschlossenen Versuchs. Beste Zeiten
berücksichtigen gespeicherte Lösungen. Alte Einträge ohne Dauer zeigen
einen Strich. Dieselbe Rätselkennung in verschiedenen Paketen hat
getrennte Verläufe. Die Daten stammen aus dem bestehenden SQLite-Schema.
Der Rollback erfordert keine Rückmigration.

## Prüfungen

- Windows 11 und Tk 9.0.4. Die Regression prüft beide Lernstandfilter,
  einen fehlgeschlagenen und einen unterstützten Versuch, den Wegfall
  eines fehlerfrei gelösten Rätsels beim Weitergehen, die leere Auswahl,
  getrennte Pakete und den Verlauf nach Neustart.
- Windows-Tk-Sichtprobe in Deutsch bei 1180 × 820 px und 96 Tk-DPI
  sowie Englisch bei 860 × 700 px und 192 Tk-DPI. Tab wechselte von
  „Wertung“ zu „Lernstand“. Filter und Versuchsdaten blieben sichtbar.
  In der schmalen Ansicht schnitt die bestehende Brettkopfzeile bei
  192 Tk-DPI das englische Figurenlabel ab.
- Im ersten Volltest überschritt der bestehende Tk-Zeittest für den
  Mock-Bot einmal seine Grenze (0,433 s bei 0,250 s Grenzwert). Der
  einzelne Wiederholungstest bestand. Die Zeitgrenze blieb unverändert.
- `py -3.14 -m unittest tests.test_app_integration.PuzzleUiTests tests.test_storage tests.test_i18n -q`
  bestand mit 49 Tests und Exitcode 0.
- Die vollständige Wiederholung mit `python -m unittest discover -s tests -q`
  bestand auf dem Code-Stand oben mit **238 Tests**, Exitcode 0
  (99,317 s, Python 3.15.1). Beide Läufe nutzten verpflichtendes Tk-Display,
  `ResourceWarning` als Fehler und `PYTHONFAULTHANDLER=1`.
- Struktur, Dokumentlinks, Policy, Kompilierung und Git-Diff bestanden.

## Übergabe

1. Plattformmatrix und native Screenreader-Prüfung nach beauftragtem Push.
2. Realdaten und Paketumfang weiter über ADR-003 und Q-022 abnehmen.
