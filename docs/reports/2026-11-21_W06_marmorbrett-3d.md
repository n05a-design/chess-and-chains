# Marmorbrett in 3D

**21.11.2026 · Lokaler, KI-gestützter Prototyp**

## Auftrag und Ergebnis

Der Owner beauftragte den schwarzen Marmor als Gegenstück zum
[freigegebenen kühlen Satz](2026-11-21_W04_plattenfiguren-svg.md),
das dazu passende Spielbrett und eine spielbare 3D-Ansicht.
Die helle Seite übernimmt die freigegebenen SVGs bytegleich.
Die dunkle Seite erhält eine invertierte, im Tonwertumfang angepasste
Palette. Figurenpfade, geäderte Flächen und Kontur des Plattenrings
bleiben geometrisch identisch. Helle Symbole und helle Ringe
kennzeichnen die schwarze Seite. Die runden Spielsteine bleiben
24 mm breit und 4 mm stark.

Die lokalen Dateien liegen in
`%USERPROFILE%/Documents/Chess-and-Chains-Figurensatz/Marmor-3D/`.
`SVG/Figuren/` enthält zwölf editierbare Kreisplatten. Die beiden
Satzübersichten liegen unter `SVG/Weisser-Satz.svg` und
`SVG/Schwarzer-Satz.svg`. `SVG/Brett.svg` enthält 64 getrennte
Feldgruppen, zwei bearbeitbare Marmorflächen, den Rahmen und die
Koordinaten. Als Zeichenmaß wurden 320 × 320 mm einschließlich
Rahmen gewählt. Die SVGs liefern die sichtbaren Texturen zur
Laufzeit. Grafikänderungen werden nach Neuladen der Browseransicht
übernommen. Der Entwurf enthält keine importierten Fremdgrafiken.

## Implementierung

- [Lokaler Einstieg](../../app/marble_3d/README.md) mit Windows-Startdatei
  im Materialordner und alternativem CLI-Befehl.
- [SVG-Ableitung](../../app/marble_3d/build_art.py) in der Python-
  Standardbibliothek. Die editierbaren Marmorgruppen bleiben lokale
  Arbeitsdateien außerhalb des Git-Repositories.
- [Lokale Spielanbindung](../../app/marble_3d/server.py) über den
  vorhandenen `GameController`. Für jeden Klickzug liefert der
  Regelkern die zulässigen Züge. Ein Zustandszähler weist veraltete
  Schreibanfragen aus einem zweiten Tab zurück. HTTP lauscht
  ausschließlich auf der IPv4-Loopback-Adresse.
- [3D-Szene](../../app/marble_3d/scene.js) mit Mesh-Geometrie für
  Brett und Platten und WebGL ohne externe Bibliotheken. Projektion und
  Trefferberechnung verwenden dieselbe Kamera. Die Kamera berücksichtigt
  die Ausmaße der projizierten Brettecken auch im schmalen Fenster.
- [Partieinteraktion](../../app/marble_3d/game.js) mit Figur- und
  Zielfeldauswahl per Maus oder Tastatur, legalen Zielmarkierungen,
  Zugliste, Schach-/Mattstatus, Umwandlung, Remisanspruch, vollständigem
  Undo/Redo, Draufsicht, Seitenwechsel und einer Bestätigung vor dem
  Zurücksetzen einer laufenden Partie.

## Inventar und Prüfnachweis

Checkout `%USERPROFILE%/OneDrive/Github/chess-and-chains`, Remote
`https://github.com/n05a-design/chess-and-chains.git`, Branch
`codex/chess-and-chains-n02-functional-core`, HEAD
`f8c30052a7e7115c55ae67f3e02f0d05029e7621`.
Der Arbeitsbaum enthielt bereits weitere Änderungen. Umgebung
Windows NT 10.0.26300.0, Python 3.15.1, Tk 9.0.4, Node v26.13.1
und Chrome 158.0.8127.37.

| Prüfung | Ergebnis |
| --- | --- |
| `python app/marble_3d/build_art.py <Marmor-Kuehl> <Marmor-3D/SVG>` | Exitcode 0. Zwölf Einzeldateien, zwei Satzübersichten und ein Brett. Die Feldtexturen wurden nach der ersten Sichtprüfung mit feldindividuellem Versatz aufgefrischt. |
| `python -m unittest discover -s tests -q` mit `PYTHONPATH=src`, `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`, `PYTHONWARNINGS=error::ResourceWarning` und `PYTHONFAULTHANDLER=1` | Exitcode 0. 244 Tests in 101,085 s, einschließlich der Tk-Tests. |
| `node --check app/marble_3d/scene.js`, `node --check app/marble_3d/game.js`, `python -m py_compile app/marble_3d/server.py app/marble_3d/build_art.py` | Exitcode 0 für JS-Syntax und Python-Kompilierung. |
| `python -m unittest discover -s tests -p test_marble_3d.py -v` | Exitcode 0. Fünf gezielte Tests für Zugprüfung, Undo/Redo, Unterverwandlung, Remisanspruch mit angesagtem Zug, Loopback-Anfragen und SVG-Feldstruktur. |
| `python "$env:TEMP/chess-chains-plate-20261121/verify_playable_marble.py" <Checkout> <Marmor-3D> "$env:TEMP/chess-chains-plate-20261121"` | Exitcode 0 im Wiederholungslauf. Chrome mit lokalem Software-WebGL. 13 SVG-Texturen, echte Züge per Maus und Tastatur, Undo/Redo, Seitenwechsel, Draufsicht, Drehen mit Ziehen, Ansichts-Reset, Abbruch und Bestätigung des Neustarts. Zweite Stellung mit vier Umwandlungsfiguren, Springerauswahl und regelkonformem anschließenden Remis. Schmale Layouts mit 320, 390 und 640 CSS-Pixeln geprüft. Die erste Automatisierung musste zuerst auf den Canvas warten. Das schmale Layout wurde nach Sichtung neu gerahmt und erneut gerendert. |
| `$env:CHESS_AND_CHAINS_REQUIRE_DISPLAY = '1'`, danach `python -m unittest discover -s tests -v` bzw. `-q` | Erster Lauf vor den fünf neuen Tests mit 172 bestandenen Tests, Exitcode 0. In einem Lauf parallel zur Browserprüfung mit 177 Tests überschritt der bestehende Tk-Timingtest `test_tk_event_loop_keeps_running_while_bot_thinks` die Grenze von 0,25 s mit 0,319 s, Exitcode 1. Der abschließende Lauf ohne parallele Browserprüfung bestand alle 177 Tests in 70,010 s, Exitcode 0. |

## Greifen, Ablegen und individuelle Marmorfelder

Der Owner beauftragte den Griff mit der Maus, das Weiterdrehen auf
freien Feldern und mehr Variation im Marmormuster des Bretts. Beim
Ziehen einer eigenen beweglichen Platte rendert die Szene dasselbe
Mesh angehoben unter dem Zeiger. In der Starthöhe wird das Mesh
ausgeblendet. Ein Rahmen zeigt das legale Feld unter der Platte.
Beim Loslassen verwendet die 3D-Ansicht dieselbe Zugauswahl wie
beim Anklicken eines Zielfelds. Ein Drop auf ein ungültiges Feld,
ein Drop außerhalb des Bretts oder Escape entfernt den Griffzustand.
Die Browser-Zeiger `grab` und `grabbing` kennzeichnen offene und
geschlossene Hand. Ziehen ausgehend von einem freien Feld bleibt
eine Kamerageste.

`SVG/Brett.svg` enthält für die 64 Felder jetzt deterministisch
erzeugte, individuelle SVG-Pfade mit unterschiedlicher Aderrichtung,
Dichte, Breite und Verzweigung. Die hellen und dunklen Paletten
folgen dem kühlen Marmor. Grundfläche, Wolken und Adern eines Felds
sind getrennt bearbeitbar. Die Figuren-SVGs und beide Satzübersichten
sind bytegleich mit der vorherigen Ausgabe. Die frühere Brettgrafik
wurde im lokalen Prüfverzeichnis gesichert.

### Prüfnachweis der Folgeänderung

Gleiche Windows-Umgebung und gleicher Checkout-HEAD wie oben.
Der Paketordner und seine Vorschauen wurden lokal aktualisiert.
Der laufende Spielprozess lieferte das neue `Brett.svg` und behielt
beim Austausch die Spielrevision 10.

| Prüfung | Ergebnis |
| --- | --- |
| `python "$env:TEMP/chess-chains-plate-20261121/verify_marble_carry.py" <Checkout> <Prüfpaket> "$env:TEMP/chess-chains-plate-20261121"` | Exitcode 0 nach Korrektur der Browser-Fokusbehandlung beim Mausdruck. Chrome meldete `grab` vor dem Griff und `grabbing` währenddessen. Eine angehobene Modellinstanz folgte dem Zeiger über zwei Felder. Der Zustand blieb bis zum Drop gleich. Legale Ablage, ungültiges Zielfeld, Escape, Loslassen außerhalb, Drehen vom freien Feld, Ablage auf dem gewendeten Brett und Umwandlung beim Drop wurden ausgeführt. |
| `python "$env:TEMP/chess-chains-plate-20261121/verify_playable_marble.py" <Checkout> <Prüfpaket> "$env:TEMP/chess-chains-plate-20261121"` | Exitcode 0. Bedienung per Klick und Tastatur, Umwandlung, Zurück und Wiederholen, Ansichtswechsel und schmale Layouts erneut geprüft. |
| `python -m unittest discover -s tests -q` mit `PYTHONPATH=src`, `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`, `PYTHONWARNINGS=error::ResourceWarning` und `PYTHONFAULTHANDLER=1` | Exitcode 0. 244 Tests in 101,085 s, einschließlich der Tk-Tests. |
| `node --check app/marble_3d/scene.js`, `node --check app/marble_3d/game.js`, `python -m unittest discover -s tests -p test_marble_3d.py -v` | Exitcode 0. Fünf gezielte Tests bestanden. Der Grafiktest prüft 64 verschiedene Aderpfade und das Vorliegen direkt editierbarer SVG-Elemente ohne wiederverwendete Feldinstanzen. |
| `python "$env:TEMP/chess-chains-plate-20261121/publish_marble_drag_locally.py" <Prüfpaket> <Materialordner> "$env:TEMP/chess-chains-plate-20261121"` | Exitcode 0. Zwölf Einzel-SVGs, beide Übersichten und Provenienz gegen die vorige Ausgabe abgeglichen. Die reine Vektorvorschau mit 64 Feldmustern wurde gerendert, die neue Board-Datei beim laufenden Dienst abgerufen. Der erste Austauschversuch endete vor dem Schreiben wegen eines abweichend übergebenen Hash-Literals. |
| `$env:CHESS_AND_CHAINS_REQUIRE_DISPLAY = '1'`, danach `python -m unittest discover -s tests -q` | Exitcode 0. Alle 177 Tests in 102,261 s bestanden. |

## Gleichmäßige Kameraführung und fester Maßstab

Die frühere Perspektivkamera hat den Abstand bei jedem Winkel neu
ermittelt und ihn bei Bedarf in Schritten von sechs Prozent erhöht.
Dadurch konnte das Brett während einer Drehung in der Größe springen.
Die orthografische Kamera berechnet jetzt den Abbildungsmaßstab des
Bretts aus der Fenstergröße. Winkeländerungen beim Ziehen, beim Wenden
und bei der Draufsicht verwenden denselben Maßstab.

Der Renderer fasst Zeigerereignisse je Bildschirmbild zusammen. Die
Kamera gleicht Winkeländerungen zeitbasiert an und stellt nach dem
Auslaufen das Rendern ein. Beim Wenden aus der Draufsicht senkt sich
die Kamera vorübergehend, damit das Brett im Rahmen bleibt. Die
Systemeinstellung für reduzierte Bewegung wird berücksichtigt. Wenn
eine Platte gehalten wird, verwendet die Trefferberechnung die
angehaltene Kamerapose. Bewegungen der Platte werden bildweise direkt
aus den Zeigerkoordinaten berechnet. Während Bewegung begrenzt der
Renderer die WebGL-Zeichenfläche auf etwa 830.000 Bildpunkte. Das
Standbild nutzt die vorgesehene Geräteauflösung. Die geometrische
Projektion verwendet in beiden Fällen dieselbe CSS-Fenstergröße.
Figuren- und Brett-SVGs stammen weiterhin aus dem lokalen Materialpaket.

### Prüfnachweis der Kameraführung

Gleiche Windows-Umgebung und gleicher Checkout-HEAD wie oben. Die
Chrome-Prüfung lief mit lokalem Software-WebGL. `$t` bezeichnet das
bisherige temporäre Prüfverzeichnis, `<Prüfpaket>` die lokale Kopie der
freigegebenen SVGs.

| Prüfung | Ergebnis |
| --- | --- |
| `python "$t/verify_steady_marble_camera.py" <Checkout> <Prüfpaket> "$t"` | Exitcode 0. Je 280 Eingaben bei 1360 × 900, 820 × 700 und 390 × 844 CSS-Pixeln. Keine synchronen Aufrufe zum Zeichnen aus den Eingaben und keine zusätzlichen Bilder im Stillstand. Spannweite des gemessenen Maßstabs unter 0,000006 CSS-Pixel pro Welteinheit. Das Brett blieb im Bild, auch beim Wenden. Reduzierte Bewegung und unveränderter Partiezustand im Prüflauf bestätigt. Gemessene Desktop-Intervalle bei 1360 × 900 CSS-Pixeln im letzten Lauf 17,7 ms im Median und 19,4 ms im 95. Perzentil. |
| `python "$t/verify_steady_marble_camera_2x.py" <Checkout> <Prüfpaket> "$t"` | Exitcode 0. Bei 1360 × 900 CSS-Pixeln und Geräte-Pixelfaktor 2 sank der Median der Bildintervalle im lokalen WebGL-Test von 41,9 auf 19,3 ms. Das 95. Perzentil sank von 48,9 auf 21,5 ms. Fester Maßstab, Rahmen und Stillstand wurden erneut geprüft. |
| `python "$t/verify_marble_carry_camera.py" <Checkout> <Prüfpaket> "$t"` | Exitcode 0. Kamera hielt die Pose beim Griff. Plattenführung, Drop, Escape, Loslassen außerhalb des Bretts, Bedienung auf dem gewendeten Brett sowie Umwandlung beim Drop geprüft. |
| `python "$t/verify_playable_marble_camera.py" <Checkout> <Prüfpaket> "$t"` | Exitcode 0. Klick- und Tastaturzüge, Zurück/Wiederholen, Partie-Reset, Draufsicht, Seitenwechsel, Drehen auf einem tatsächlich leeren Feld und Umwandlung überprüft. Der erste Lauf hatte den Drehversuch auf einem inzwischen belegten Feld begonnen. |
| `python -m unittest discover -s tests -q` mit `PYTHONPATH=src`, `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`, `PYTHONWARNINGS=error::ResourceWarning` und `PYTHONFAULTHANDLER=1` | Exitcode 0. 244 Tests in 101,085 s, einschließlich der Tk-Tests. |
| `node --check app/marble_3d/scene.js`, `node --check app/marble_3d/game.js`, `python -m unittest discover -s tests -p test_marble_3d.py -v` | Exitcode 0. Beide JavaScript-Dateien syntaktisch gültig, fünf Spiel- und SVG-Vertragstests bestanden. |

## Grenzen und Anschluss

1. Der Prototyp läuft lokal mit zwei Personen am selben Gerät und hält
   die Partie im Speicher des lokalen Prozesses. Tk-Desktop-App,
   Partiebibliothek, Puzzle-Lab und Bot-Modus sind in diesem
   Browserlauf nicht eingebunden. Laufzeit- und Paketierungstests
   auf weiteren Systemen stehen aus.
2. Für die öffentliche Auslieferung bleiben die Herkunfts- und
   Nutzungsrechte für die ursprünglichen Figuren gemäß
   [Q-003](../questions/OPEN_QUESTIONS.md) und
   [ADR-005](../decisions/ADR-005_BRAND_ASSETS.md) offen.
3. Keine Veröffentlichung, kein Commit und kein Push. Zum Beenden
   des Prototyps genügt es, den lokalen Spielprozess zu schließen.

## Auf GitHubs Stand nach PR #18 übernommen

Basis des Arbeitsbranches ist GitHubs `main` mit
`3407b3326335f6bb2b3fce1aaab1189c3ade966f`. Darin enthalten ist auch
der aktuelle Regelkern für tote Stellungen mit unbeweglichen
Bauernbarrieren. Der separate Startpunkt `python app/marble_3d/server.py`
lädt den eingecheckten Spielsatz direkt. Der Export liefert die PGN der
laufenden Partie. Das Brett kennt die deutsche Meldung für die neue
Remisart. Der 3D-Server verwendet dieselbe SVG-Satzvalidierung wie die
Tk-App. Der Prüfworkflow führt die Tests für die 3D-Ansicht ohne Browser auf allen sechs
System- und Python-Kombinationen der bestehenden Matrix aus.

Der KI-gestützt aufbereitete [Grafikstand](../../design/source/marmor-3d/README.md)
enthält 12 Figuren-SVGs und das Brett mit 64 individuellen Feldern.
Die historische Angabe zum Upload im vorherigen Abschnitt betrifft
den ursprünglichen lokalen Stand. Die Beschlüsse zur App-Lizenz und
die Freigabe für diesen GitHub-Arbeitsbranch sind in
[ADR-005](../decisions/ADR-005_BRAND_ASSETS.md) dokumentiert.

### Validierung auf der neuen Basis

Die Prüfung erfolgte unter Windows NT 10.0.26300.0 mit Python 3.15.1,
Node.js 26.13.1 und Chrome 158 mit Software-WebGL. Die Ausgangsbasis
war `3407b33`. Der Grafikcommit war `8a0380a05168fda423a942186733c71f908808a4`.
Für den Testlauf lag der 3D-Code bereits im Index. Dessen Baum vor
Ergänzung dieses Berichts war `2679455c52359c1732ebb894c1ff09457189ac68`.

| Prüfung | Ergebnis |
| --- | --- |
| `python -m unittest discover -s tests -p test_marble_3d.py -v` mit `PYTHONPATH=src` und `PYTHONWARNINGS=error::ResourceWarning` | Exitcode 0, sieben Tests. Enthält u. a. PGN-Rundlauf, totes Bauernbarrieren-Remis, SVG-Satz und Schutz vor veralteten Änderungen. |
| `python -m unittest discover -s tests -q` mit `PYTHONPATH=src`, `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`, `PYTHONWARNINGS=error::ResourceWarning` und `PYTHONFAULTHANDLER=1` | Exitcode 0. 244 Tests in 101,085 s, einschließlich der Tk-Tests. |
| `node --check app/marble_3d/scene.js`, `node --check app/marble_3d/game.js` | Je Exitcode 0. |
| `python scripts/check_policy.py`, `python scripts/verify_starter.py`, `python scripts/verify_document_links.py`, `python -m compileall -q src app scripts tests` | Je Exitcode 0. Die Linkprüfung umfasst relative Ziele. |
| `python app/marble_3d/build_art.py design/source/marmor-3d/spielsatz <Temp-Ausgabe>` und SHA-256-Abgleich per Python | Exitcode 0. Alle 15 neu erzeugten Spiel-SVGs stimmen bytegenau überein. 100 Prüfsummen stimmten im Checkout und im Git-Objekt überein. |
| `python -u "$t/verify_playable_marble_camera_github.py" <Checkout> <Temp-Ausgabe> <Temp-Ausgabe>` | Exitcode 0. Start ohne `--assets`, 13 geladene SVG-Texturen, echter PGN-Download nach e4, Klick- und Tastaturzug, Rückgängig/Wiederholen, Ansichtswechsel, Neustart, Umwandlung und Layout bei 320, 390 und 640 CSS-Pixel Breite. |
| `python -u "$t/verify_marble_carry_camera_github.py" <Checkout> <Temp-Ausgabe> <Temp-Ausgabe>` | Exitcode 0. Handcursor, Plattenführung, legaler Drop, Abbruch, Drehung ab leerem Feld, gewendetes Brett und Umwandlung. |
| `python -u "$t/verify_steady_marble_camera_github.py" <Checkout> <Temp-Ausgabe> <Temp-Ausgabe>` und gleicher Aufruf mit `verify_steady_marble_camera_2x_github.py` | Je Exitcode 0. Vier Läufe mit je 280 Eingaben. Keine zusätzlichen Bilder im Stillstand, Maßstabsspanne unter 0,000006 CSS-Pixel pro Welteinheit. Bei 1360 × 900 lagen Median und 95. Perzentil bei 16,6 und 18,4 ms. Bei Pixelfaktor 2 lagen sie bei 19,4 und 23,3 ms. |

Die temporären Browserprüfskripte lagen unter
`$env:TEMP/chess-chains-plate-20261121` (`$t`). Der Workflow prüft
Regelbrücke und SVG-Vertrag. Der Browserlauf prüft Windows mit
Software-WebGL. Native Sichtprüfung auf Linux und macOS, Hardware-
WebGL, reale Touchgeräte und Freigabe für Produktpakete sind offen.

### Geordneter Anschluss

1. Die GitHub-Prüfmatrix für den Arbeitsbranch auswerten.
2. Kamera und Plattenführung auf realen Zielgeräten sichten.
3. Die Auswahl des finalen Produktbretts und die Paketierung gemäß
   [ADR-005](../decisions/ADR-005_BRAND_ASSETS.md) mit dem Inhaber entscheiden.

Der Prototyp startet separat und schreibt keine persistenten
Partiedaten. Zum Rückbau die beiden Marmor-Commits in umgekehrter
Reihenfolge zurücknehmen. Ein Datenformatwechsel ist dafür nicht erforderlich.
