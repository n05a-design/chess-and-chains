# W06 · Figurensatz V.02 mit optischem Ausgleich

**21.11.2026 · KI-unterstützt · Basis `a39cf93` auf `codex/chess-chains-figuren-w07`.**

## Umsetzung

Die [Inhaberfassung V.02](../../design/source/chess_pieces/V.02-Schachfiguren-Vorderansicht-Masspruefung.svg) ist bytegleich archiviert. SHA-256 `e0a6733c3420393bb72436c12ea9618d7d44c9d8f6a0137036d92908c33c3d65`. Die App übernimmt die revidierte Grundform der Vorderansichten. Hell und Dunkel verwenden identische Geometrie und 1,14 Einheiten breite Konturen. In den dunklen SVGs hellt Graphit die Lichtseite auf. Die tiefere Schattenseite trennt Kopf, Flanke und Fuß deutlicher. Der [editierbare V.02-Prüfbogen](../../design/source/chess_pieces/V.02-Schachfiguren-Vorderansicht-Schatten.svg) enthält beide Farben und eine 40-Pixel-Kleinansicht.

Alle sechs Figurentypen wurden in beiden Farben auf hellen und dunklen Feldern verglichen. Als zusätzliche Orientierung dient die Summe der Alpha-Fläche bei 256 Pixeln, in SVG-Flächeneinheiten zurückgerechnet. Die Werte beschreiben die gefüllte Fläche und ergänzen die visuelle Beurteilung.

| Typ | Fläche V.02 | Fläche mit Ausgleich | Eingriff |
| --- | ---: | ---: | --- |
| Bauer | 1.554,4 | 1.699,8 | Kopf, Hals und oberer Körper etwas voller. Abgerundeter Kopf und charakteristischer Stand bleiben lesbar. |
| Turm | 1.764,4 | 1.827,6 | Schultern und Körper weiter gefasst. Die symmetrische Kerbe bleibt erkennbar. |
| Springer | 1.815,2 | 1.815,2 | Diente als Referenz. Der asymmetrische Kopf und der Einschnitt entsprechen der Inhaberfassung. |
| Läufer | 1.721,5 | 1.806,9 | Etwas vollere Schultern und leicht angehobene linke Kante. Seitliche Kerbe und Rundung bleiben bestehen. |
| Dame | 1.827,4 | 1.827,4 | Diente als Referenz. Die geschwungene Krone entspricht der Inhaberfassung. |
| König | 1.733,5 | 1.790,2 | Schultern verbreitert, äußere Kronenschultern leicht angehoben. Das Mittelkreuz bleibt das Erkennungsmerkmal. |

## Prüfungen

- Windows 11 x64 / Python 3.15.1 / Tk 9.0.4. Der Tk-Atlasgenerator erstellte die Vorderansicht-Tafel mit 21 Größen in 1536 × 2968 px, Exitcode 0. Die Draufsichten sind bytegleich zum Basiscommit.
- XML- und Rastervergleich der zwölf SVGs. 252 native SVG-Kacheln stimmen mit den Atlas-Kacheln überein. Über alle 21 Größen stimmen die sichtbaren Außenraster mit der normalisierten Inhaberfassung überein. Die Schatten belegen ausschließlich Pixel der jeweils fertigen Figur. Die korrigierten Vorderansichten belegen bei 128 × 128 px dieselbe Grundfläche von 78 × 108 px einschließlich Kontur, mit identischer Lage. Exitcode 0.
- Auf 40-Pixel-Feldern stieg der gemessene Tonwertabstand zwischen linker und rechter Körperfläche bei dunklen Figuren von 10,9–17,2 auf 37,7–39,8 von 255 Stufen. Messfenster sind die Spalten 14–18 und 26–29 und die Zeilen 27–29. Gewichtet nach RGB-Kanalhelligkeit. Der König-Test prüft die Trennung zusätzlich im PNG-Fallback.
- `python -m unittest discover -s tests -v` unter der oben genannten Umgebung mit `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`, `PYTHONWARNINGS=error::ResourceWarning` und `PYTHONFAULTHANDLER=1`. 187 Tests in 94,858 Sekunden, keine Skips, Exitcode 0. Ein Zwischenlauf hatte zwei Fehler, weil der Bericht bereits im Manifest referenziert wurde, während er noch fehlte. Die vollständige Endprüfung lief mit vorliegendem Bericht.
- `git diff --cached --check`, `python scripts/check_policy.py`, `python scripts/verify_starter.py` und `python scripts/verify_document_links.py` waren erfolgreich. Die eingetragenen SHA-256-Werte der Figurendateien und Prüfbögen stimmen mit dem Git-Index überein. Der SVG-Prüfbogen und das ZIP mit zwölf Einzelgrafiken wurden ebenfalls geprüft.

## Übergabe

1. Sichtprüfung des optischen Ausgleichs und der dunkleren Schatten mit den Inhaber-Brettmotiven.
2. Native Plattform- und High-DPI-Abnahme ergänzen. Windows/Tk 9 belegt die geprüften Bilddaten und den Fallback-Pfad.
3. Nach SVG-Änderungen den Vorderansicht-Atlas und die [Asset-Hashes](../design/ASSET_REGISTER.csv) neu erzeugen. Ein Revert stellt die erste Schattierung wieder her. Spielstände erfordern keine Migration.
