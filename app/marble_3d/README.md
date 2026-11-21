# Lokales Marmorbrett in 3D

Die Tk-App bietet über dem Brett den direkten Ansichtswechsel
**Marmorbrett in 3D**. Diese Ansicht nutzt dieselben Marmor-SVGs als
Grafikquelle und bleibt mit der geöffneten Tk-Partie verbunden.
Die folgenden Hinweise gelten für den separaten WebGL-Prototyp.

Der Browser-Prototyp stellt eine Partie für zwei Personen mit der vorhandenen
Schachdomäne und dem vorhandenen `GameController` dar. Das separate
Startskript öffnet einen Browser mit WebGL. Der Python-Prozess lauscht
ausschließlich auf `127.0.0.1` und hält die laufende Partie im Speicher.

## Start

Aus der Wurzel des Checkouts mit Python 3.11 oder neuer starten.

```powershell
python app/marble_3d/server.py
```

Der Starter verwendet den [Spielsatz aus dem Checkout](../../design/source/marmor-3d/spielsatz/).
Mit `--assets <Ordner>` lässt sich ein eigener Satz laden. Mit `--no-browser`
wird die lokale Adresse ausgegeben. `--fen` nimmt eine vom Regelkern
validierte Startstellung an. Beim Schließen des Python-Prozesses
endet die lokale Sitzung. **Partie als PGN speichern** exportiert die
aktuelle Zugfolge, Startstellung, Ergebnis und vorhandene PGN-Kopfdaten.
Die Datei lässt sich in der Partiebibliothek der Tk-App öffnen. Unter
**Dateien** können einzelne PGNs bis 256 KiB und FEN-Dateien bis 4 KiB
geladen werden. Vor dem Ersetzen einer begonnenen Partie fragt der
Browser nach. **Stellung als FEN speichern** exportiert die aktuelle
Brettstellung mit Zugrechten und Zählern.

Eine eigene ziehbare Platte mit der Maus greifen, über das markierte
Zielfeld führen und loslassen. Beim Halten zeigt der Mauszeiger eine
geschlossene Hand. Escape sowie Loslassen außerhalb des Bretts beenden
das Halten ohne Zug. Wer klicken oder die Tastatur verwenden möchte,
wählt Figur und Zielfeld nacheinander.

Ziehen auf einem freien Feld dreht das Brett mit festem Abbildungsmaßstab.
Draufsicht und Seitenwechsel gehen fließend in die gewünschte Ansicht
über. Die Systemeinstellung für reduzierte Bewegung verkürzt den Übergang
auf ein Bild. Während eine Platte gehalten wird, pausiert die Kamera.
Die Zugliste folgt dem lokalen Spielzustand. Umwandlungen und
beanspruchbare Remisoptionen werden vom Regelkern geliefert.

**Partie nachspielen** zeigt einen Schnappschuss der Anfangsstellung
und der gespielten Züge. Der Stellungsregler reagiert auf Pfeiltasten.
Die Zugliste markiert den betrachteten Halbzug. **Zur laufenden Partie**
lädt den aktuellen Stand der lokalen Sitzung.

## Editierbare Grafik

`Brett.svg` enthält 64 einzelne Feldgruppen mit eigenständigen
Haupt- und Nebenadern in zwei kühlen Marmorpaletten. Grundfläche, Wolken
und Adern sind pro Feld editierbar. Die zwölf SVGs unter `Figuren/` enthalten Ring,
Figur und Marmorgruppen. Der 3D-Renderer erzeugt seine Texturen beim Start
aus diesen Dateien. Nach einer Bearbeitung genügt ein Neuladen der
Browseransicht, um den Grafikstand zu übernehmen. Läuft derselbe lokale
Server weiter, bleibt dabei die Partie erhalten.

Für neue Ableitungen aus dem hellen Master einen neuen Zielordner verwenden.

```powershell
python app/marble_3d/build_art.py design/source/marmor-3d/spielsatz Marmor-SVG-Neu
```

Die Vorschau verwendet eine eigene lokale Browser-Ansicht. Bot-Modus,
Partiebibliothek und Puzzle-Lab gehören zur Tk-App. Für die öffentliche
Auslieferung gelten [Q-003](../../docs/questions/OPEN_QUESTIONS.md) und
[ADR-005](../../docs/decisions/ADR-005_BRAND_ASSETS.md).
