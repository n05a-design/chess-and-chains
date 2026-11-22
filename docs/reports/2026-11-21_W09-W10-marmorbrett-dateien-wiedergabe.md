# W09/W10 – Dateiaustausch und Wiedergabe am Marmorbrett

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Lokaler Branch
`codex/chess-chains-marmor-dateiaustausch-wiedergabe` auf dem
W08/W09-PR-Stand `773f764878ee47467363833feeb7a52c396988fa`.
Der [Dokumentationsabgleich](https://github.com/n05a-design/chess-and-chains/pull/18)
und das [lokale Marmorbrett](https://github.com/n05a-design/chess-and-chains/pull/19)
aus GitHub-`main` sind enthalten.
Der Dateibaum dieses Ausgangspunkts entspricht dem Merge von PR #20
in `6238724`.

## W09 · Dateiaustausch

Commit `8dff8f31aeb5bce099166d1e5ecba9b80083f870` ergänzt den
PGN-/FEN-Dateiwähler und den FEN-Download. Der lokale Server prüft
Host, Herkunft, Revision, Dateityp und Größe vor der Übernahme.
PGN erlaubt die vorhandenen Grenzen von 256 KiB und 512 Halbzügen.
FEN erlaubt 4 KiB. Fehlerhafte Dateien lassen die laufende Sitzung
intakt. PGN-Kopfdaten und aufgezeichnete Ergebnisse bleiben beim
erneuten Export verfügbar.

## W10 · Partiewiedergabe

Commit `b7631725b7c40cd42219fefc6813cdf66d74e5c5` ergänzt einen
Positionsverlauf vom ersten Brettzustand bis zur aktuellen Stellung.
Der browsernative Regler reagiert auf Pfeiltasten. Die Zugliste markiert
den betrachteten Halbzug. Die Live-Aktionen sind während der Wiedergabe
ausgeblendet. Beim Verlassen lädt der Browser die aktuelle Partie.
Der Server stellt die vorhandenen, unveränderlichen Positionen des
Regelkerns bereit.

## Prüfungen

- `python -m unittest tests.test_marble_3d -q`: 10 Tests, Exitcode 0.
  Einschließlich PGN-Metadaten, abgewiesenem Import, FEN-Download,
  Revisionsprüfung, en passant, Rochade und unverändertem Live-Verlauf.
- `node --check app/marble_3d/game.js`: Exitcode 0.
- `python -m unittest discover -s tests -q` auf `b763172`: 250
  Tests, Exitcode 0 (100,246 s). Windows 11 mit Python 3.15.1 und
  Tk 9.0.4, verpflichtendes Tk-Display und `ResourceWarning` als Fehler.
- Lokale Chrome-Headless-Probe mit WebGL/SwiftShader unter Windows.
  Sie öffnete über die Dateieingabe PGN und FEN, wies eine fehlerhafte
  Datei ab, wechselte den Halbzug per Pfeiltaste und prüfte die
  Rückkehr samt FEN-Export. Bei 390 px gab es keinen horizontalen
  Überlauf. Der Browserdialog wurde über die Dateieingabe automatisiert.

## Übergabe

1. Plattformmatrix der beiden Folgecommits nach beauftragtem Push
   ausführen. Die Matrix von PR #20 deckt ihren Ausgangspunkt ab.
2. Manuelle Dateidialoge und Screenreader in den Zielbrowsern prüfen.

Der Rückbau erfordert keine Datenmigration.
