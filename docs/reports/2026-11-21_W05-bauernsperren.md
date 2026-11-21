# W05 – Tote Stellungen mit geschlossener Bauernsperre

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Implementierungsstand
`599700cbbb2ab53ad67930d2756e6e45b0869fc2` auf
`codex/chess-chains-w05-bauernsperren`.

In Stellungen mit Königen und Bauern greift automatisches Remis, wenn
ein Nachweis jede Möglichkeit zum Matt ausschließt. Auf jedem
Bauernvorfeld muss ein gegnerischer Bauer stehen. Bauernschläge und
en passant müssen ausgeschlossen sein. Dann überschätzt der Kern den
Bewegungsraum jedes Königs, indem er den anderen König bei der
Erreichbarkeitsprüfung ausblendet. Er prüft höchstens 64 Felder je
König. Wenn die Bereiche überlappen, sich berühren oder ein möglicher
Königsschlag die Sperre öffnen kann, reicht der Nachweis nicht aus.
Bei getrennten Bereichen ohne erreichbaren Schlag bleiben die Bauern
unbeweglich und es ist kein Schach möglich. Das Ergebnis erscheint über
den bestehenden Remisstatus. Historische Zugfolgen bleiben abspielbar.

Die neue Prüfung braucht keine Bibliothek und keine Datenmigration.
Sie deckt geschlossene Bauernsperren ab. Verblockte Stellungen mit
weiteren Figuren und längere verzweigte Zwangsfolgen bleiben offene
Regelfälle. Der Rollback kann die Implementierung und ihre Nachweise
zurücknehmen, ohne Nutzerdaten umzuschreiben.

## Prüfungen

- Vier neue Tests verwenden projekteigene Stellungen. Der erste Lauf
  vor der Implementierung meldete fünf erwartete Assertion-Fehler in
  positiven Fällen und Teilfällen.
- `py -3.14 -m unittest tests.test_chess_golden.TerminationRuleTests tests.test_storage tests.test_puzzles -q`
  bestand unter Windows 11/Python 3.14.7 mit 75 Tests und Exitcode 0.
  Geprüft wurden Farbspiegelung, beide Zugfarben, das Schließen der
  Sperre, Gegenbeispiele, Undo/Redo, PGN und historische Wiedergabe.
- `python -m unittest discover -s tests -q` auf dem Quellstand oben
  bestand unter Windows 11/Python 3.15.1/Tk 9.0.4 mit 237 Tests
  und Exitcode 0 (87,204 s). Tk-Display war verpflichtend,
  `ResourceWarning` ein Fehler und `PYTHONFAULTHANDLER=1` gesetzt.
- Struktur-, Link-, Policy-, Kompilierungs- und Git-Diff-Prüfung
  endeten mit Exitcode 0.
- Eine einmalige unabhängige Traversierung der Referenzstellung mit
  dem regulären Zugerzeuger besuchte 768 Stellungen und 3.808 legale
  Übergänge. Keiner gab Schach oder veränderte die Bauernstruktur.
  Die Traversierung fasste gleiche Brettbelegungen und Zugfarben
  zusammen. Die Zusatzprüfung benötigte im lokalen Mittel aus 5.000
  Aufrufen ca. 0,43 µs in der Startstellung und 62 µs in der
  Referenzstellung. Die Werte gelten für diese zwei Stellungen.

## Übergabe

[PR #17](https://github.com/n05a-design/chess-and-chains/pull/17) ist in
`main`. [Push](https://github.com/n05a-design/chess-and-chains/actions/runs/44932609420),
[PR](https://github.com/n05a-design/chess-and-chains/actions/runs/44932613717)
und [Merge-Lauf](https://github.com/n05a-design/chess-and-chains/actions/runs/44932980772)
bestanden je 14 Jobs. Die vier neuen Regelfälle liefen unter macOS mit
Python 3.11 und 3.14 erfolgreich.

Weitere Regelfälle für verblockte Stellungen bleiben Teil der Roadmap.
