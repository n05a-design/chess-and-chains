# W08 und W09 – Rätselneustart und Partiewiedergabe

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Zwei lokale Folgepakete auf
`codex/chess-chains-w08-w09-wiederholtraining`.

## W09 · Partiewiedergabe

`a0f712c29d6d9d251643f0e76b60e73bb08064c4` ergänzt „Partie nachspielen…“
unter „Züge“ und in der Partiebibliothek. Die Vorschau verwendet die
Anfangsstellung und genau einen gespeicherten Positionsstand je gespieltem
Halbzug. Über Zugliste, Links/Rechts, Anfang und Ende lässt sich die
Position wechseln. Das Ende zeigt das Ergebnis. Der Benutzer behält die
laufende Partie und ihre Historie. Die Datenbank wird nur gelesen.
Ein Test ruft die Funktion über die Bibliothek auf und prüft eine
FEN-Ausgangsstellung mit Schwarz am Zug, en passant und historischem Remis.

## W08 · Rätselneustart und gestufte Hinweise

`981833b09ed1a8bdd65dd36049c29bf392367a8a` ergänzt zwei Hinweisstufen und
einen Neustart der aktuellen Aufgabe. Die erste Hilfe markiert die Figur,
die zweite das Zielfeld und nennt eine etwaige Umwandlungsfigur. Die
Hinweisstufen starten nach einem richtigen Zug neu. Der Neustart eines
begonnenen Versuchs fragt vor dem Verwerfen nach. Er kehrt zur Stellung
nach dem Aufbauzug zurück. Abgeschlossene Versuche bleiben in SQLite.
Eine Regression prüft beide Stufen, abgelehnten Neustart, gespeicherte
Hinweise und eine getrennte, anschließend fehlerfreie Lösung. Das
Figurenlabel der Brettkopfzeile bricht bei schmalen, skalierten Fenstern um.

## Prüfungen

Windows 11, Tk 9.0.4 und verpflichtendes Tk-Display für die Testläufe.
`py -3.14 -m unittest tests.test_app_integration.PuzzleUiTests tests.test_app_integration.StorageAndLocaleUiTests tests.test_puzzles tests.test_i18n -q`
bestand mit 61 Tests und Exitcode 0. Der Windows-Volltest auf
`981833b` bestand mit 240 Tests und Exitcode 0.

Eine Tk-Sichtprobe nutzte Deutsch bei 1180 × 820 px und 96 Tk-DPI sowie
Englisch bei 860 × 700 px und 192 Tk-DPI. Sie prüfte Navigation per
Pfeiltaste und das zweite Hinweisziel. In einer Folgeprobe bei
192 Tk-DPI reichte die Breite eines Wiedergabebuttons zunächst nicht.
`007d46e` leitet die Mindestbreite der Bedienleiste aus den Steuerelementen
ab. Die erneute Probe bestätigte in DE und EN ausreichend breite Buttons
und einen wieder verfügbaren ersten Hinweis nach einem gespielten Gegenzug.
Der anschließende Volltest `python -m unittest discover -s tests -q`
auf `007d46e` bestand mit 240 Tests, Exitcode 0 (101,723 s,
Python 3.15.1). Strukturprüfung, relative Links, Policy, Kompilierung
und Git-Diff bestanden ebenfalls.

## Übergabe

1. Plattformmatrix für den lokalen Branch nach beauftragter
   Veröffentlichung ausführen. Auf GitHub war während der Umsetzung
   kein Lauf für den lokalen Wiederholtraining-Branch aktiv.
2. Screenreader und native Skalierung auf den Zielplattformen abnehmen.

Ein Rollback der Funktions- und Dokumentationscommits erfordert keine
Datenmigration.
