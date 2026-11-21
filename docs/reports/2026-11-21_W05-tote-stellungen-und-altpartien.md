# W05/W09 – Tote Stellungen bei erzwungenen Schlagzügen

**V.0.0.1 · 21.11.2026 · Codex, KI-gestützt.**
Lokaler Branch `codex/chess-chains-w05-dead-positions` mit Basis
`d982c83afcc5eb25d4567b1d6c3f6ec100db0b3e` aus dem Paketabgleich nach PR #9. Der Implementierungscommit
ist `b1fbab269da52da3bf2bdc9eeafbb780fa6a86cd`. Der Referenzstand auf
`origin/main` ist `6bcd9ada580be10f289c34dd0040be62297597d2`.

## Reproduktion und Regel

Eigene Teststellung `8/8/8/8/8/8/r1k5/K7 w - - 0 1`. Die Basis meldete
`ACTIVE`. Weiß hat nur `Kxa2`, danach sind beide Könige allein. Nach
Art. 5.2.2 ist die Stellung bereits vor diesem Schlagzug remis. Die
Vorprobe auf der Basis verwendete `ChessGame.outcome()` und
`ChessRules.legal_moves()` in Python, Exitcode 0.
[FIDE Laws of Chess, Art. 5.2.2](https://handbook.fide.com/chapter/E012023)

Der Regelkern erkennt die Stellung jetzt anhand aller legalen Antworten.
Führen sie ausschließlich durch unmittelbare Schlagzüge in Stellungen
mit nachgewiesen ungenügendem Material, ist die Partie sofort beendet.
`DRAW_DEAD_POSITION` wird auf Deutsch und Englisch in der App angezeigt.
Der Test spielt die Stellung über `…Ra2+` an und prüft auch die
farbgespiegelte Position, Rückgängig/Wiederholen und den PGN-Export mit
`1/2-1/2`. Gegenproben decken einen verfügbaren Ausweichzug, eine
Schlagfortsetzung mit verbleibendem Mattmaterial und zwei alternative
Schlagzüge ab. Andere tote Stellungen, etwa verblockte Strukturen und
mehrzügige Zwangsfolgen, bleiben zur Regelprüfung offen.

## Bestehende Aufzeichnungen

Der PGN-Parser und die SQLite-Bibliothek validieren historische Züge mit
den vor diesem Paket geltenden Abbruchprüfungen. Züge müssen weiterhin
auf dem Brett legal sein. Beim Wiederöffnen bleiben Züge, deklarierte
Ergebnisse und lokale Endgründe erhalten. Der Rückweg in eine
unabgeschlossene Stellung verwendet die aktuelle Remiserkennung.
Insbesondere kann eine alte Partie mit aufgezeichnetem `Kxa2` geladen und
wiedergegeben werden, während ein neuer Spielzug aus derselben toten
Stellung ausgeschlossen ist. Rätsel prüfen weiterhin ihre vorgegebenen
Zugfolgen. Datenbankschema und PGN-Format bleiben kompatibel.

## Prüfnachweise

Windows 11 Pro x64, Python 3.14.7/Tk 9.0.4 mit
`CHESS_AND_CHAINS_REQUIRE_DISPLAY=1` und
`PYTHONWARNINGS=error::ResourceWarning`.

```powershell
py -3.14 -m unittest tests.test_chess_golden.TerminationRuleTests tests.test_storage tests.test_puzzles tests.test_app_integration.DrawClaimTests tests.test_i18n -q
```

**60 Tests bestanden**, Exitcode 0. Die Speicherfälle nutzen temporäre
SQLite-Datenbanken und prüfen alte Aufzeichnungen mit Schlagzug,
Aufgabe, Remisanspruch, übernommenem Sieg und offenem Ergebnis. Ein
neues Remis wird gespeichert und anhand der Stellung erneut erkannt.

Der Gesamtlauf `python -m unittest discover -s tests -q` prüfte
Tree `196b8c1db3631de2065cf113355f14b1f39233ab` vor Ergänzung dieses
Ergebnisses mit Python 3.15.1/Tk 9.0.4 unter Windows. Zusätzlich war
`PYTHONFAULTHANDLER=1` gesetzt. **199 Tests bestanden**, keine Skips,
Exitcode 0 (89,947 Sekunden). `verify_starter.py`,
`verify_document_links.py`, `check_policy.py`,
`python -m compileall -q src app scripts tests` und `git diff --check`
schlossen ebenfalls mit Exitcode 0 ab.

## Übergabe

1. Paket W05 bleibt für seinen dokumentierten Teilumfang `TESTED`.
   Allgemeine tote Stellungen und die Gesamtregelabnahme bleiben offen.
2. Den Folgebranch plattformübergreifend prüfen, sobald ein Push für
   diese Änderungen beauftragt ist. W10/W11 und die weiteren
   Freigabepunkte bleiben in der [Roadmap](../roadmap/ROADMAP.md).
3. Eine spätere allgemeine Erkennung muss zusätzlich die Rückgabezeit
   im Tk-Ereignisablauf und die Wiedergabe historischer Partien prüfen.

Für einen Rollback lassen sich Code-Commit und zugehörige Dokumentation
revertieren. Die Tests verwenden das bestehende SQLite-Schema 3.
