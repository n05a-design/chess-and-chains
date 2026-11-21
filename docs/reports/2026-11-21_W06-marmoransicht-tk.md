# W06 – Marmoransicht im Tk-Spielfenster

**V.0.0.1 · 21.–22.11.2026 · KI-gestützt.** Implementierung
`ce622e2c794c2d411a20c3f9d71e300fba13310a` auf
`codex/chess-chains-marmor-dateiaustausch-wiedergabe`.

**Marmorbrett in 3D** schaltet die orthografisch projizierte Ansicht
im bestehenden Spielfenster ein und aus. Der Umschalter ändert das
Rendering desselben Brett-Widgets. Spielcontroller, Zugliste, Spielmodus
und Undo/Redo werden dabei weder neu erstellt noch zurückgesetzt.
Maus, Drag-and-drop, Tastatur, Schachmarkierung, importierte FEN-Stellung,
Orientierung und das separate Textbrett verwenden den bestehenden
Partiestand und dieselbe Zugvalidierung.

Die Marmoransicht hat einen festen Schrägwinkel. Über **Brett drehen**
wechselt die Spielerseite. Die frei drehbare Kamera ist im separaten
WebGL-Prototyp verfügbar. Der 3D-Modus der Tk-App benötigt weder eine
Browser-Engine noch einen lokalen Server. Die
[editierbaren SVGs](../../design/source/marmor-3d/spielsatz/) bleiben
die Quelle für die [drei Tk-Texturen](../../src/chess_and_chains/ui/marble_assets/PROVENANCE.md).

## Prüfungen

Unter Windows wurden Ansichtswechsel mit Enter und Leertaste,
Feldnavigation, Zugausführung auf dem projizierten Brett, Spielerseitenwechsel
und erhaltene Zuggeschichte geprüft. Die Regression wechselt bei
vorhandenem Wiederholen-Verlauf ins Marmorbrett, zieht nach
schwarzer Perspektive weiter und kehrt ins normale Brett zurück.
Die Tk-Sichtprobe lief auf Deutsch bei 1180 × 820 px und 96 Tk-DPI
sowie auf Englisch bei 860 × 700 px und 192 Tk-DPI.
Die fokussierte Tcl/Tk-Suite mit Python 3.14.7 bestand mit 77 Tests.
Der erste vollständige Windows-Lauf meldete einen falsch übertragenen
SHA-256-Wert der hellen Bretttextur im Assetregister. Der Wert in Register
und Provenienz wurde anhand der tatsächlich gebauten PNG-Datei korrigiert.

- `python -m unittest discover -s tests -q` auf `a4d0a50` bestand mit
  251 Tests und Exitcode 0 (104,004 s). Umgebung Windows 11, Python
  3.15.1 und Tk 9.0.4, verpflichtendes Display, `ResourceWarning` als
  Fehler und `PYTHONFAULTHANDLER=1`.
- Die neu erzeugten drei Texturen waren bytegleich mit den committeten
  Laufzeitdateien. Struktur-, Link-, Policy-, Kompilierungs- und
  Git-Diff-Prüfungen bestanden.
- Ein offline gebautes und getrennt installiertes Wheel aus `a4d0a50`
  enthielt alle drei Texturen und die Provenienz. `--headless-check`
  sowie Wechsel, Drag-and-drop und Rückgängig im installierten Fenster
  bestanden. Wheel-SHA-256
  `7a12f5529a89f1229b4072b0c213913b350ccee97bc5692831f06fdb15a14c47`.

## Übergabe

1. Plattform-CI nach beauftragtem Push ausführen. Die lokale
   Sichtprobe belegt die Windows-Darstellung.
2. Native Skalierung und Screenreader auf den Zielsystemen prüfen.
   Die Veröffentlichung des Entwicklungsstands und die Produktabnahme
   bleiben getrennte Schritte.

Ein Rollback benötigt keine Datenmigration.
