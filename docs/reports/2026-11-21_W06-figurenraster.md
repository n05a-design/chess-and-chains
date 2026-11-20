# W06 · Figurenraster für Vorder- und Draufsicht

**21.11.2026 · KI-unterstützt · Windows 11 x64.**

## Auftrag und Basis

Der Inhaber beauftragte die Aufbereitung beider Originalansichten als Einzel-SVGs und eine stärkere Unterscheidung von König und Dame in der Vorderansicht. Am 21.11.2026 stellte er anhand seiner Maßgrafik klar, dass gleiche sichtbare Breite und Höhe jeweils innerhalb einer Ansicht gelten und die Vorderansichten ihr Hochformat behalten. Er bestätigte die Draufsichten visuell. Basis war `bee01b9711cd531784ad838f87bac32546f17a80` im Arbeitsbranch `codex/chess-and-chains-owner-design`. Der [registrierte Master](../../assets/chess_pieces/source_svg/masters/Schachfiguren.svg) ist bytegleich zur gelieferten SVG-Datei. Herkunft und die bestehende App-Lizenz unter MPL-2.0 sind im [Assetregister](../design/ASSET_REGISTER.csv) erfasst.

## Umsetzung

- **IMPLEMENTED** · Je zwölf [editierbare SVGs für Vorder- und Draufsicht](../../assets/chess_pieces/source_svg/README.md). Vorderansichten messen 39 × 54 Einheiten bei Grundlinie `y=59`, Draufsichten 52 × 52 Einheiten bei Kreismittelpunkt `(32, 32)`. Beide Maße schließen die zwei Einheiten breite Kontur ein. Zeichenfläche 64 × 64, Raster in halben Einheiten. Helle und dunkle Varianten teilen ihre Geometrie.
- Vorderansicht mit gezeichneten Bézierkurven statt stufiger Konturen. König und Dame teilen Sockel und Kragen. Der König trägt ein erhöhtes, kantiges Kreuz als Ableitung des Kreuzmotivs aus dem Master, die Dame eine breite, geschwungene Krone. Der seitliche Einschnitt am Läufer wurde vertieft.
- Die App nutzt Vorderansichten regulär und `--piece-view top` als Sitzungsoption für Partie und Rätsel. Tk 9 zeichnet die SVGs. Beide Sätze haben eigene offline erzeugte PNG-Tafeln für ältere Tk-Versionen.

## Prüfungen

Die Prüfungen beziehen sich auf den Änderungenstand dieses Berichts auf Basis des oben genannten Commits. Umgebung jeweils Windows 11 x64, Python 3.15.1, Tk 9.0.4. Für den Unittest-Lauf waren `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1` und `PYTHONWARNINGS=error::ResourceWarning` gesetzt.

| Befehl oder Verfahren | Beobachtetes Ergebnis |
| --- | --- |
| `python scripts/build_piece_fallback.py` und anschließender Aufruf von `build_atlas` für die korrigierte Vorderansicht | Tafeln mit jeweils 21 Größen und 1536 × 2968 Pixeln erzeugt, Exitcode 0. Alle 14 Dateien der bestätigten Draufsicht stimmen nach der Vorderansichtskorrektur per SHA-256 mit der bestätigten Fassung überein. |
| `python -m unittest discover -s tests -v` | 182 Tests in 89,533 s, Exitcode 0, keine Skips. Die Tests enthalten die sichtbaren Grenzen aller 24 Fallback-Kacheln bei 128 px sowie die Auswahl der Draufsicht in CLI, Partie und Rätseln. |
| Lokales Prüfskript über `OwnerSvgPieces._load_image` mit nativem SVG und erzwungenem PNG-Fallback | 504 Paare (24 Figuren × 21 Größen) lieferten identische gerenderte PNG-Daten, Exitcode 0. Bei 128 px hat die Vorderansicht exklusive Alphagrenzen `(25, 10, 103, 118)`, die Draufsicht `(12, 12, 116, 116)`. Bei der Vorprüfung erzeugten Knicke am Fuß von Turm, Läufer und Springer einen überstehenden Antialiasing-Pixel. Tangentenkurven beseitigten den Überstand. |
| Offline `python -m pip wheel --no-build-isolation --no-deps --no-index --wheel-dir <Temp> .` und Installation mit `python -m pip install --no-index --no-deps --target <Temp> <Wheel>` | Wheel enthält beide SVG-Sätze, beide Tafeln und die Herkunftsangaben, Exitcodes 0. SHA-256 `f5eebcc05b4937f4dfc5e1ac7253c6c5fa1ebdd05b35b096fd2f12d8cc9a03af`. |
| Nativer Tk-Smoke über die installierte CLI mit `--piece-view top` und Standardstart | Beide Sitzungen zeigten 32 Figuren und zwölf Varianten auf Feldern von 45,5 px. Zug, Brettdrehung und Rätselstart erfolgreich, Exitcode 0. |

## Übergabe

1. Sichtfreigabe der korrigierten Vorderansicht durch den Inhaber. Die Einzel-SVGs und der [SVG-Prüfbogen](../../design/source/chess_pieces/Schachfiguren-Vorderansicht-Masspruefung.svg) liegen im Repository.
2. Native Sichtprüfung auf macOS und Linux sowie High-DPI-Abnahme ergänzen. Der erzwungene Fallback auf Tk 9 belegt die Bilddaten und den Wiedergabepfad.
3. Nach einer Vektoränderung `python scripts/build_piece_fallback.py` ausführen und die Hashes im Assetregister aktualisieren.

Ein Revert der Figurenänderung stellt den früheren Vorderansichtssatz und seinen Fallback wieder her. Der Master ist separat versioniert. Spielstände verwenden keine Figuren-Dateinamen und benötigen keine Migration.
