# W05/W09 – FEN-Stellungen austauschen und spielen

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Lokaler Branch
`codex/chess-chains-w05-w09-fen-austausch`, Implementierung
`25e5b36f70b4398c683ce87105a136d9886aaba7`, Tree
`a67fb939c95974aa3fb61065cf3cf896a92f5cde`. Ausgangspunkt ist
`dd47f2238c992906ce34302dfef5d1c1e24187d4`. Der GitHub-Merge von
[PR #13](https://github.com/n05a-design/chess-and-chains/pull/13) hat für
diesen Ausgangspunkt einen identischen Dateibaum in `main` übernommen.

## Ablauf

1. Unter „Spielen“ öffnet „Stellung austauschen…“ ein vorausgefülltes FEN-Feld
   mit der zu diesem Zeitpunkt angezeigten Stellung.
2. Die FEN kann eingefügt, kopiert oder aus einer lokalen Datei gelesen
   werden. Der Dateiexport schreibt die validierte FEN atomar. Fehler beim
   Lesen und Schreiben erscheinen im Dialog. Der Entwurf bleibt erhalten.
3. „Stellung spielen“ startet eine lokale Partie zu zweit mit neuem
   Zugverlauf. Beim Ersetzen eines Zugverlaufs fragt die App nach. Nach
   Abbruch bleibt der Entwurf erhalten. Escape schließt den Dialog und
   gibt den Fokus an das zuvor aktive Steuerelement zurück.
4. Die importierte Zugfarbe, Rochaderechte, en-passant-Angabe und Zähler
   gelten ab der ersten Stellung. Weitergespielte Züge können über die
   vorhandene Bibliothek als Partie gespeichert werden. Das PGN trägt
   `SetUp` und `FEN` für abweichende Ausgangsstellungen.

Der [Datenvertrag](../architecture/DATA_CONTRACTS.md) beschreibt die
Dateigrenze und das Roundtrip-Format. PGN und FEN nutzen denselben atomaren
Schreibpfad. Beim Rollback können die Funktions- und Dokumentationscommits
zurückgenommen werden. Die bestehenden Datenformate bleiben kompatibel.

## Lokale Prüfungen

Windows 11 Pro x64 (10.0.26300), Tk 9.0.4, Python 3.15.1 und 3.14.7.
GUI-Testläufe mit `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`,
`PYTHONWARNINGS=error::ResourceWarning` und `PYTHONFAULTHANDLER=1`.

| Prüfung | Ergebnis |
| --- | --- |
| `python -m unittest tests.test_storage.PositionFileTests tests.test_app_integration.PositionExchangeUiTests -v` | 5 Tests, Exitcode 0. Abgedeckt sind FEN mit BOM, ungültige Daten, Schreibfehler, Zwischenablage, Bestätigung, Zug und Fokusrückkehr. |
| `py -3.14 -m unittest tests.test_storage.PositionFileTests tests.test_app_integration.PositionExchangeUiTests tests.test_i18n -q` | 13 Tests, Exitcode 0. Die native Tk-Oberfläche wurde mit isolierten Testpfaden für die Öffnen-/Speichern-Dialoge betrieben. |
| `python scripts/check_policy.py`, `python -m compileall -q src app scripts tests`, `git diff --check dd47f22...HEAD` | Exitcode 0. |

Der erste vollständige Lauf startete während der Dokumentationsarbeit.
Beim Prüfen des Manifests fehlte der dort bereits verlinkte Bericht.
Der Lauf endete mit zwei Foundation-Fehlschlägen und Exitcode 1.

## Übergabe

1. Die Plattformmatrix für dieses Folgepaket nach beauftragtem Push
   ausführen. Die grünen GitHub-Läufe von PR #13 betreffen den Ausgangspunkt.
2. Systemdialoge auf den Zielsystemen und Tastaturbedienung mit
   Screenreader prüfen. Die Datenpfade mit alten SQLite-Bibliotheken
   bleiben durch die bestehenden Regressionen abgedeckt.
3. Profilmodell und Gesamtfreigabe nach Q-012 und ADR-004 in der
   [Roadmap](../roadmap/ROADMAP.md) weiterführen.
