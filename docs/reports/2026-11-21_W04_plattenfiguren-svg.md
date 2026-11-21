# Sechs Schachfiguren auf Platten

**21.11.2026 · KI-gestützte Vektoraufbereitung · Lokal geprüft**

Auftrag war ein erster Satz aus König, Dame, Turm, Läufer, Springer und Bauer
als editierbare Einzel-SVGs mit einem gemeinsamen Raster. Die sieben
Ausgabedateien liegen lokal in `%USERPROFILE%/Downloads/Chess-and-Chains-Plattenfiguren/`.
Die Dateien `01-koenig.svg` bis `06-bauer.svg` enthalten jeweils eine Platte.
`00-raster-3x2.svg` ordnet dieselben sechs Platten an.

## Vorlage und Geometrie

- Arbeitsquelle `2026-08-25-2D-Figuren-2D – Figuren.stl` aus den vom Owner
  bereitgestellten Dateien. SHA-256
  `6d5120e1d8135416501154c57f25a956abf526f134de2dbd72c2ffcba7600977`.
  Die beiden SVG-Vorlagen bestehen aus projizierten Netzflächen bzw.
  Netzlinien. Die HTML-Datei ist ein STL-Viewer. Die STL liefert über einen
  Schnitt parallel zur Oberseite die vollständigen Figurengravuren.
- Der Schnitt bei Y = 3,95 ergab 42 geschlossene Konturen. Zwölf gehören zu
  den Plattenrändern und 30 zu den Figuren. Die Figurenkonturen wurden mit
  Geraden, kubischen Bézierkurven und Kreisbögen nachgebildet. Die Reihenfolge
  der Aussparungen und die charakteristischen Ecken folgen der Vorlage.
- Die Sockelkanten wurden um 1,036° bis 2,857° horizontal ausgerichtet. Die
  Figuren sind proportional auf 14,6 mm Höhe skaliert und in ihrer
  Begrenzungsbox zentriert. Der Springer blickt wie in der Draufsicht nach links.
- Das Exportlayout verwendet runde Platten mit 24 mm Außendurchmesser,
  0,94 mm Randstärke und 28 mm Abstand zwischen benachbarten Mittelpunkten.
  Einzeldateien haben eine Zeichenfläche von 26 × 26 mm, das Raster
  86 × 58 mm. Dunkle Konturen und weiße Plattenflächen ergeben eine
  monochrome Darstellung mit transparentem Bereich außerhalb der Platten.

## Prüfnachweis

- Lokaler Checkout `%USERPROFILE%/OneDrive/Github/chess-and-chains`, Remote
  `https://github.com/n05a-design/chess-and-chains.git`, Branch
  `codex/chess-and-chains-n02-functional-core`, HEAD
  `f8c30052a7e7115c55ae67f3e02f0d05029e7621`. Der Arbeitsbaum enthielt
  bereits weitere Änderungen. Der Export und die Geometrieprüfungen betrafen
  ausschließlich die lokalen Grafikdateien. Kein Commit oder Push.
- Windows NT 10.0.26300.0, Python 3.15.1, NumPy 2.5.4, SciPy 1.18.1,
  Shapely 2.2.0, Pillow 13.0.0 und Chrome 158.0.8127.37.
  Die Arbeits- und Prüfskripte liegen lokal unter
  `%TEMP%/chess-chains-plate-20261121/`.
- `python "$env:TEMP/chess-chains-plate-20261121/plate_export.py" "%USERPROFILE%/Downloads/Chess-and-Chains-Plattenfiguren"`
  lief mit Exitcode 0. Die 30 neu gebildeten Figurenkonturen sind geschlossen
  und behalten die Verschachtelung der Vorlage. Der größte an abgetasteten
  Pfaden geprüfte Abstand zur proportional skalierten STL-Schnittkontur
  lag bei 0,0235 mm. Die Glättungstoleranz bezieht sich auf diese digitale
  Vorlage.
- `python "$env:TEMP/chess-chains-plate-20261121/verify_plates.py" "$env:TEMP/chess-chains-plate-20261121" "%USERPROFILE%/Downloads/Chess-and-Chains-Plattenfiguren"`
  lief mit Exitcode 0. XML und Pfadkoordinaten wurden für alle sieben Dateien
  geprüft. Jede Rasterfigur hat dieselbe Geometrie wie ihre Einzeldatei.
  Chrome bestätigte die Bounding Boxes aller sechs Figuren, die gemeinsamen
  Höhen und Grundlinien sowie die Zentrierung. Das gerenderte Raster wurde
  visuell auf Außenkonturen und Innenformen kontrolliert.

## Gefüllte Fassung

Auf Wunsch des Owners sind die inneren Teilflächen der sechs Figuren dunkel
gefüllt. Die hellen Trennfugen zwischen den Teilflächen, die beiden
Aussparungen der Königskrone und das Springerauge sind sichtbar. Die
Teilflächen wurden als Gruppe proportional auf 14,6 mm Höhe gebracht. Die
Plattengeometrie und das 3 × 2-Raster entsprechen der ersten Fassung.
Die sechs Einzel-SVGs und die Raster-SVG liegen lokal in
`%USERPROFILE%/Downloads/Chess-and-Chains-Plattenfiguren-Gefuellt/`.

Die folgenden Befehle liefen mit Exitcode 0 auf derselben Umgebung und
demselben Checkout-HEAD wie oben.

- `python "$env:TEMP/chess-chains-plate-20261121/export_filled.py" "%USERPROFILE%/Downloads/Chess-and-Chains-Plattenfiguren-Gefuellt"`
  prüfte die Geometrie von 22 Teilpfaden einschließlich der drei
  Binnenaussparungen.
- `python "$env:TEMP/chess-chains-plate-20261121/verify_filled.py" "$env:TEMP/chess-chains-plate-20261121" "%USERPROFILE%/Downloads/Chess-and-Chains-Plattenfiguren-Gefuellt"`
  prüfte die sieben SVGs auf geschlossene Pfade und übereinstimmende
  Geometrie zwischen Raster und Einzeldateien. Chrome bestätigte sechs
  zentrierte Figuren mit gleicher Höhe und Grundlinie. Das gerenderte
  Raster wurde visuell auf gefüllte Flächen, Fugen und Aussparungen geprüft.

## Optische Abstimmung der gefüllten Fassung

Die Einzel-SVGs und die Raster-SVG liegen in
`%USERPROFILE%/Downloads/Chess-and-Chains-Plattenfiguren-Abgestimmt/`.
Die Basis bilden die sieben vorangegangenen SVGs der gefüllten Fassung.
Die sechs Figuren sind weiterhin 14,6 mm hoch. Die Platten haben 24 mm
Außendurchmesser. Der diagonale Einschnitt des Läufers misst in der
horizontalen Schnittebene durch die Plattenmitte 1,21 mm statt 1,71 mm.
König, Dame, Turm und Springer wurden in der Breite gestrafft. Der Läufer
erhielt mehr Füllfläche im Körper. Beim Bauern wurden Kopf, Kragen und
Schultern verstärkt. Kreuz, Kronenspitzen, Zinnen, Läufereinschnitt,
Springerauge und Bauernkopf bleiben als Erkennungsmerkmale erkennbar.

| Figur | Vorherige dunkle Fläche in mm² | Abgestimmte dunkle Fläche in mm² |
| --- | ---: | ---: |
| König | 108,73 | 99,00 |
| Dame | 110,20 | 98,00 |
| Turm | 107,66 | 98,00 |
| Läufer | 80,83 | 98,00 |
| Springer | 105,53 | 98,00 |
| Bauer | 81,83 | 95,87 |

Die Flächen wurden aus abgetasteten SVG-Pfaden innerhalb der Platten
berechnet, einschließlich der Abzüge für Aussparungen. Sie dienen
als Maß für das optische Gewicht. Die Figurentypen unterscheiden sich
weiterhin in ihrer Form und in der Verteilung der Füllfläche.

Die folgenden drei Befehle liefen unter der oben dokumentierten Umgebung
auf Checkout-HEAD `f8c30052a7e7115c55ae67f3e02f0d05029e7621` mit Exitcode 0.
In den Befehlen steht `$p` für
`%USERPROFILE%/Downloads/Chess-and-Chains-Plattenfiguren` und `$t` für
`$env:TEMP/chess-chains-plate-20261121`.

- `python "$t/balance_plates.py" "$p-Gefuellt" "$p-Abgestimmt"` prüfte
  Flächen, Einschnittbreite, getrennte Teilflächen und die drei Aussparungen.
- `python "$t/verify_balanced.py" "$t" "$p-Abgestimmt"` prüfte sieben
  Dateien und 22 geschlossene Teilpfade, die Gleichheit von Raster und
  Einzeldateien sowie Höhe, Zentrierung und Grundlinien in Chrome.
- `python "$t/check_optical_weight.py" "$t" "$p-Abgestimmt"` ermittelte im
  Browserbild eine Flächenspanne von 3,24 % des neuen Satzmittelwerts
  gegenüber 29,84 % des vorherigen Satzmittelwerts. Beide Werte schließen
  den Plattenrand aus. Die in Chrome gerenderte Darstellung mit
  72 und 40 Pixeln pro Platte wurde visuell geprüft.

## Korrektur nach Rückmeldung des Owners

Die gewünschte Fassung liegt in
`%USERPROFILE%/Downloads/Chess-and-Chains-Plattenfiguren-Korrigiert/`.
König, Dame, Turm, Springer und Bauer wurden bytegleich aus der ersten
gefüllten Fassung übernommen. Im Raster wurden die entsprechenden
Figurenpfade ebenfalls aus dieser Fassung übernommen. Der Läufer hat
wieder seine ursprüngliche Gesamtbreite von 10,09 mm. Der diagonale
Einschnitt misst auf Höhe der Plattenmitte 1,18 mm gegenüber 1,71 mm in der
ersten gefüllten Fassung. Die Korrektur betrifft die Flanken des Einschnitts.

Die folgenden Befehle liefen mit Exitcode 0 in der zuvor dokumentierten
Windows-Umgebung auf demselben Checkout-HEAD. Die Variablen `$p` und `$t`
bezeichnen dieselben Pfade wie im vorigen Abschnitt.

- `python "$t/restore_plates.py" "$p-Gefuellt" "$p-Abgestimmt" "$p-Korrigiert"`
  prüfte die fünf übernommenen SVGs auf Bytegleichheit und den Läufer auf
  gleiche Begrenzungsbox, drei getrennte Teilflächen und schmaleren Einschnitt.
- `python "$t/verify_restored.py" "$t" "$p-Korrigiert"` prüfte sieben SVGs,
  22 geschlossene Teilpfade und die Geometrie von Einzeldateien und Raster.
  Das Raster wurde in Chrome gerendert und visuell geprüft.

## Gestalterische Auswahl und lokaler W06-Kandidat

Der Owner stimmte dem korrigierten Satz im Chat zu. Die zwölf App-SVGs
übernehmen die sechs gewählten Figurenpfade einschließlich des schmaleren
Läufereinschnitts. Sie verwenden die Dateinamen des vorhandenen
Figurenvertrags, von `wK.svg` bis `wP.svg` und von `bK.svg` bis
`bP.svg`. Für die lokale Vorschau wurden die aktuellen Tk-Farben
`PAPER` und `INK` für Platte, Ring und Figur verwendet. Die helle und
die dunkle Ausführung unterscheiden sich in der Farbbelegung. Die 26-mm-
Master-Zeichenfläche bleibt unter `Design-Master/` erhalten. Die
App-SVGs haben eine dimensionslose viewBox von `0 0 260 260` und
260 Pixel als Standard-Ausgabegröße.

Das lokale Paket liegt unter
`%USERPROFILE%/Documents/Chess-and-Chains-Figurensatz/`. Es enthält
`Design-Master/` mit sechs Einzel-SVGs und Raster, `App-SVG/` mit zwölf
Farbdateien und `PROVENANCE.md`, die Prüfsummen in
`App-SVG-SHA256.txt` sowie die Brettvorschau als HTML und PNG.
Der vorherige Downloadordner war beim Folgeauftrag nicht vorhanden.
Die Master-SVGs wurden aus dem archivierten Prüf-HTML wiederhergestellt.
Das aus ihnen neu gerenderte Raster stimmt pixelgenau mit der früheren
Vorschau überein.

### Prüfnachweis W06-Kandidat

Windows NT 10.0.26300.0, Python 3.15.1, Tcl/Tk 9.0.4 und
Chrome 158.0.8127.37 auf Checkout-HEAD
`f8c30052a7e7115c55ae67f3e02f0d05029e7621`. Die Belege betreffen die
lokale Vorschau und den vorhandenen Arbeitsbaum. Es gab keinen
Commit, Push oder Eingriff in den Standard-Renderer der App.

| Prüfbefehl | Ergebnis |
| --- | --- |
| `python "$t/recover_approved_art.py" "$t"` und `python "$t/verify_recovered.py" "$t" "$t/korrigiert-recovered"` | Exitcode 0. Sieben SVGs und 22 geschlossene Teilpfade geprüft. Anschließender Pillow-Vergleich des erneuten Chrome-Renders mit der freigegebenen Vorschau ergab keine abweichenden Pixel. |
| `python "$t/prepare_app_piece_set.py" "$t/korrigiert-recovered" <Ausgabeordner> "$t"` | Erster Lauf Exitcode 1 bei der Browser-Vorschau durch fehlende Dateiendung im Lookup. Die korrigierte Funktion `generate` lief mit Exitcode 0 in einem separaten Vergleichsordner. Zwölf Dateien erfüllten den Projektvertrag. Pfaddaten, Geometrie und Farben wurden gegen den Master geprüft, die Ergebnisse bytegleich mit den ausgelieferten Dateien abgeglichen. Die Vorschau mit 32 Figuren wurde visuell geprüft. |
| `python "$t/verify_app_piece_set.py" "%USERPROFILE%/Documents/Chess-and-Chains-Figurensatz"` | Erster Lauf Exitcode 1 durch unnötigen Import eines früheren STL-Skripts. Zweiter Lauf Exitcode 1 durch zu strenge Farbgleichheit am geglätteten Springerauge bei 48 Pixeln. Nach Korrektur Exitcode 0. 36 native SVG-Ausgaben in Tk bei 48, 72 und 96 Pixeln einschließlich Transparenz, 18 Stichproben an Aussparungen und 32 Figuren im vorhandenen `BoardCanvas` bei sechs Größen-/Orientierungskombinationen. Verwendet wurde ein temporärer Test-Renderer. |
| `python -m unittest discover -s tests -p 'test_board_ui.py' -v` | Exitcode 0. 11 Tests bestanden. |
| `python -m unittest test_app_integration.PieceRendererContractTests -v` aus `tests/` | Exitcode 0. Zwei Tests bestanden. |

## Materialstudie und gewählter kühler Marmor

Die lokale Materialstudie in
`%USERPROFILE%/Documents/Chess-and-Chains-Figurensatz/Steinplatten/`
enthält zwei Marmor- und zwei Granitvarianten. Alle vier Texturen
wurden lokal prozedural erzeugt. Der Owner wählte kühlen Marmor und
bat darum, die Bearbeitbarkeit der SVGs zu erhalten.

Die weitergeführte Fassung liegt in
`%USERPROFILE%/Documents/Chess-and-Chains-Figurensatz/Marmor-Kuehl/`.
Sie enthält sechs Einzel-SVGs, das 3 × 2-Raster, einen separaten
Marmor-Master und eine lokale 3D-Vorschau als HTML. Die Einzeldateien
enthalten Marmorgrund, 17 Tonwertgruppen mit 180 Vektorflächen, einen
separaten Kreisring und den unveränderten Figurenpfad. Eine
Schnittmaske hält den Marmor unter der Innenkante. Das Raster
referenziert die gemeinsamen Marmorvektoren. Die Einzeldateien
enthalten die editierbaren Vektorformen direkt.

Die 3D-Vorschau erzeugt lokal ein rundes Modell mit 24 mm Durchmesser,
4 mm Stärke und gefasten Kanten. Sie lädt die Marmorvektoren mit dem
jeweiligen Figurenpfad als Textur der Oberseite. Eine Figur kann
über die Auswahl gewechselt und mit Maus oder Tastatur gedreht werden.
Der WebGL-Nachweis betrifft den lokalen Modellbetrachter. Eine
zusätzliche spielbare 3D-Brettansicht müsste an den vorhandenen
Brettzustand sowie die Zug- und Auswahlsteuerung angebunden werden.

### Prüfnachweis Material und 3D

Windows NT 10.0.26300.0, Python 3.15.1, NumPy 2.5.4, SciPy 1.18.1,
Pillow 13.0.0, OpenCV 5.0.0 und Chrome 158.0.8127.37, Checkout-HEAD
`f8c30052a7e7115c55ae67f3e02f0d05029e7621`. Die Skripte liegen
unter `$env:TEMP/chess-chains-plate-20261121/` (`$t`). `$a`
bezeichnet `%USERPROFILE%/Documents/Chess-and-Chains-Figurensatz`.

| Prüfbefehl | Ergebnis |
| --- | --- |
| `python "$t/stone_materials.py" "$a/Design-Master" "$a/Steinplatten" "$t"` | Exitcode 0. Vier Texturen, 24 Einzel-SVGs und vier Raster. |
| `python "$t/render_stone_contact.py" "$t" "$a/Steinplatten"` | Exitcode 0. Materialvergleich in Chrome gerendert und visuell geprüft. |
| `python "$t/vector_cold_marble.py" "$a/Design-Master" "$a/Steinplatten" "$a/Marmor-Kuehl" "$t"` | Exitcode 0. Acht SVGs geprüft. Keine eingebetteten Rasterbilder oder Filter. Alle vorhandenen Figurenpfade entsprechen den Masterdaten. |
| `python "$t/verify_marble_vectors.py" "$t" "$a/Marmor-Kuehl"` | Exitcode 0. Sechs Ringe und Innenflächen im Browser geprüft. Die quadratisch gemittelte RGB-Abweichung der Vektorvorschau vom gewählten Referenzbild beträgt 0,81 bei einem Kanalbereich von 0 bis 255. |
| `python "$t/verify_marble_webgl.py" "$t" "$a/Marmor-Kuehl"` | Exitcode 0. Alle sechs Figurentexturen in WebGL gerendert. Tastaturrotation und Ansicht-Reset verifiziert. Eine beim ersten Rendering sichtbare Fuge zwischen Deckfläche und Rand wurde durch Korrektur der Randkoordinaten im Mesh beseitigt und im abschließenden Screenshot visuell geprüft. Für die WebGL-Prüfung wurde Chrome mit lokaler Softwarebeschleunigung gestartet. |

### Offene Entscheidungen und Anschluss

1. Urheberschaft, Lizenz und Nutzungsumfang für die Übernahme der
   Grafiken bestätigen. [Q-003](../questions/OPEN_QUESTIONS.md) und
   [ADR-005](../decisions/ADR-005_BRAND_ASSETS.md) bleiben dafür offen.
2. Für den Spielbetrieb einen separaten 3D-Brett-Renderer mit dem
   vorhandenen Spielzustand verbinden und die Lesbarkeit von Marmor
   und Seitenkennzeichnung in typischen Brettgrößen prüfen.
3. W06-Renderer und Paketierung mit den tatsächlich
   ausgelieferten Tk-Versionen auf den Zielplattformen prüfen. Der
   lokale Windows-Test gilt für Tk 9.0.4.

## Einordnung für den GitHub-Arbeitsbranch

Die vorstehenden Prüfungen dokumentieren den ursprünglichen lokalen
Entwurf. [ADR-005](../decisions/ADR-005_BRAND_ASSETS.md) hält die inzwischen
dokumentierte Entscheidung zur Urheberschaft und App-Lizenz fest. Der
[Marmor-Arbeitsstand](../../design/source/marmor-3d/README.md) sichert die
editierbaren Master und die zugehörigen Studien. Die Laufzeitintegration
und die Prüfungen auf Grundlage von PR #18 stehen im
[Bericht zum 3D-Marmorbrett](2026-11-21_W06_marmorbrett-3d.md).
