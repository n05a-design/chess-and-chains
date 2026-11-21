# W06 · Figurenschatten für die überarbeiteten Vorderansichten

**21.11.2026 · KI-unterstützt · Basis `f6ff4fc` auf `codex/chess-chains-figuren-w07`.**

## Quelle und Ausführung

Die [überarbeitete Inhaberfassung](../../design/source/chess_pieces/Schachfiguren-Vorderansicht-Inhaberfassung.svg) wurde bytegleich aus der gelieferten SVG übernommen. SHA-256 `2e3257ab231ab74e84af8cfb11149f64beec73662dd11aa98f6679eda8ecdc4f`. Alle zwölf Vorderansichten übernehmen die Silhouetten- und Kragenpfade samt 1,14 Einheiten breiter Kontur. Die Kragenmatrizen sind auf die 64 × 64-Zeichenfläche der jeweiligen Figur bezogen. Der ursprüngliche Master und die freigegebene Draufsicht sind separat erhalten.

Die Nutzerreferenz von Chess.com diente der Betrachtung der Lichtwirkung. Die Konturen, Schattenpfade und Farbverläufe in den App-SVGs stammen aus der Inhaberfassung und der darauf aufgebauten Schattierung. Die editierbaren Vektorflächen modellieren Kopf, rechte Flanke, Kragen und Fuß mit Licht von links oben. Der [Prüfbogen](../../design/source/chess_pieces/Schachfiguren-Vorderansicht-Schatten.svg) zeigt beide Figurfarben und die Darstellung in 40-Pixel-Feldern. Die Herkunft und Prüfsummen stehen im [Assetregister](../design/ASSET_REGISTER.csv).

## Prüfungen

Windows 11 x64, Python 3.15.1, Tk 9.0.4. Die Prüfungen beziehen sich auf die lokalen Änderungen auf Basis des oben genannten Commits.

| Befehl oder Verfahren | Ergebnis |
| --- | --- |
| Tk-Atlasgenerator `build_atlas` für die Vorderansicht | 1536 × 2968 Pixel mit allen 21 Skalierungsstufen, Exitcode 0. |
| Lokaler XML- und Tk-Rastervergleich | 12 Silhouetten und 12 Kragen entsprechen der Inhaberfassung einschließlich Konturstärke. Alle 252 SVG/PNG-Rasterpaare stimmen überein. Gegen eine unverschattete Rasterung der Inhaberfassung sind Position und Menge aller belegten Pixel identisch. Ab 48 px sind die Alpha-Kanäle bytegleich. Unterhalb davon beträgt die größte Abweichung innerhalb belegter Pixel 10 von 255 Alphastufen. Alle 24 App-Figuren bestanden den bestehenden Außenmaßtest. Exitcode 0. |
| `python -m unittest discover -s tests -v` mit `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`, `PYTHONWARNINGS=error::ResourceWarning`, `PYTHONFAULTHANDLER=1` | 187 Tests in 103,517 Sekunden, keine Skips, Exitcode 0. Der erzwungene PNG-Pfad prüft für helle und dunkle Könige auch die Tonwertabstufung. |
| Offline-Wheel mit `python -m pip wheel --no-build-isolation --no-deps --no-index --wheel-dir <Temp> .`, Installation und Tk-Smoke aus dem installierten Paket | Alle zwölf SVGs sowie der PNG-Fallback enthalten. Partie, Zug, Drehung und Rätsel waren bei 45,5 px Feldgröße über beide Renderpfade erfolgreich. Exitcode 0. Wheel-SHA-256 `a5f65a976855aa08f5daca19c78b85e3d09acac86226e41472467f471ded2aee`. |

## Übergabe

1. Schattierung und Kontrast mit den Inhaber-Brettmotiven visuell abnehmen.
2. Native Plattform- und High-DPI-Abnahme nachziehen. Der Tk-9-Test des älteren Fallback-Pfads belegt die erzeugten Bilddaten und ihre Wiedergabe.
3. Bei Änderungen an den SVGs die Vorderansicht-PNG-Tafel neu erzeugen und die Asset-Hashes aktualisieren. Ein Revert stellt die vorherigen Vorderansichten wieder her. Spielstände benötigen keine Migration.
