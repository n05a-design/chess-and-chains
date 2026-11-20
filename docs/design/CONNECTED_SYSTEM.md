# Chess & Chains · Connected System

**Stand 20.11.2026 · Designkandidat für den lokalen Tk-Prototyp · KI-unterstützt**

Chess & Chains ist eine lokale Werkstatt für Schach und taktisches Training. „Think in connections.“ verbindet die Konzentration am Brett mit dem Blick auf die Zugfolge und den Lernfortschritt. Für die App-Vorschau wähle ich **Connected System**. Die Marke beginnt mit zwei ineinandergreifenden Gliedern und wird im Puzzle Lab als Route weitergeführt. Brett und Bedienflächen bleiben ruhig. Die kräftigsten Farben markieren die Marke, die aktive Ansicht, Primäraktionen und den Rätselstatus.

## Synthese der Referenzen

| Referenz | Beobachtung | Entscheidung im Kandidaten |
| --- | --- | --- |
| Link Lab | Gerundete, horizontal versetzte Rechtecke. Konturbreite 14, Radius 14, Blau `#2447D8` und Gelb `#FBBA20`. Der Export zeigt Überlagerung ohne alternierende Durchgänge. | Blau und modulare Kontur übernommen. Für das Signet wird ein Glied um 90° ausgerichtet. Zwei reale Unterbrechungen machen die Über-/Unterführung auch einfarbig lesbar. Die parallele Lösung ist als *Precision Engine* sichtbar. |
| Atlas of Moves | Orthogonale Route mit gerundeten Richtungswechseln, 32er Raster, Stationen, Monoziffern und kartografischer Farbwelt. | Route, Knotensprache und Nummerierung übernommen. Für die App ordnen Gelb, Blau und Rot die Zustände. *Atlas Studio* erprobt die gedämpfte Kartografie als Hauptmarke. |
| Bauhaus-Moodboard | Schwarz und Creme, Primärfarben, Viertelkreise und klare Raster. Die Schachfigur tritt im Hero als großes Motiv auf. | Raster und Viertelkreise tragen die Kampagne. Das App-Brett nutzt zwei ruhige Sand- und Steintöne. *Modular Bauhaus* setzt die kräftigen Flächen als führende Form ein. |
| Schachfiguren | Original-SVG und PNG zeigen je sechs Vorder-/Draufsichten. Die Vorderformen teilen eine Schulter, einen kompakten Fuß und differenzieren sich vor allem über Einschnitte. | Wiederholung und Differenzierung gehen ins Gestaltungssystem ein. Der Bildvergleich zeigt nahe Silhouetten bei Turm/Läufer und Dame/König. Der Vorschaulauf nutzt die vorhandenen Testfiguren. Für die Originale sind die Rechte und der Einsatzmaßstab in Q-003 offen. |
| Prompt.txt und Langbriefing | Geometrische Werkstatt, orthogonale Verkettung, Space Grotesk und IBM Plex Mono, Variantenentwicklung und Owner-Review. | Die SVG-Master verwenden Live-Text. Der direkte Auftrag delegiert die Entwurfsauswahl und lokale Integration. ADR-005 führt die Marken- und Rechtefreigabe weiter. |

## Vergleich und Auswahl

Die [Vergleichstafel](../../design/concepts/connected-system-v01/00-variantenvergleich.svg) nutzt dieselben Zeichen, Farbrollen und Knotenzustände wie die fünf Brandboards. Die Einschätzungen beruhen auf Gestaltungsanalyse und lokaler Sichtprüfung.

| Richtung | Konstruktion / Typografie | Stärke | Trade-off |
| --- | --- | --- | --- |
| [Connected System](../../design/concepts/connected-system-v01/01-connected-system.svg) | Orthogonale Verkettung, Space Grotesk, IBM Plex Mono | Zwei lesbare Durchgänge, flexibel einfarbig einsetzbar, klarer Bezug zu Atlas und Raster | Schach wird im kompakten Zeichen erst durch Produktname oder Anwendung eindeutig. Gold braucht eine dunkle Text- oder Konturfarbe. |
| [Precision Engine](../../design/concepts/connected-system-v01/02-precision-engine.svg) | Horizontaler Offset Link und parallele Linien | Kompakt und sachlich, gut für Werkzeugleisten | Stärkerer Eindruck eines generischen Link- oder Technikzeichens. |
| [Atlas Studio](../../design/concepts/connected-system-v01/03-atlas-studio.svg) | Route mit zwei Endknoten und freiem Rasterfeld, Georgia und Mono | Eigenständige Trainingssprache und starke Leserichtung | Schachspiel und Werkstatt treten hinter der Kartenmetapher zurück. |
| [Modular Bauhaus](../../design/concepts/connected-system-v01/04-modular-bauhaus.svg) | Rechte Winkel, gegenläufige Viertelkreise und Negativräume | Expressive, gut skalierbare Kampagnenflächen | Die Verbindung der Glieder liest sich abstrakter. Großflächen benötigen Distanz zum aktiven Spielfeld. |
| [Connected Atelier](../../design/concepts/connected-system-v01/05-connected-atelier.svg) | Zwei gegenläufige C-Module und diagonaler Steg | Variable Wiederholung und gute Eignung für Erscheinungsvarianten | Die Silhouette kann beim ersten Blick als Schalter gelesen werden. |

## Geometrie und SVG-Bibliothek

- Das 64er Signet arbeitet mit `u = 2` SVG-Einheiten. Das horizontale Grundglied misst außen 48 × 31 bei einem Steg von 8. Der Außenradius beträgt nominell 10 und der Innenradius 2. Durchgang 1 unterbricht den oberen horizontalen Steg, Durchgang 2 den unteren vertikalen Steg. Die vertikale Form ist zur optischen Einpassung mit 33 × 46 Außenmaßen angepasst. Die beiden Lücken bestehen aus echter Pfadgeometrie.
- App-Kachel und Signet sind als [laufzeitgenutzte SVGs](../../src/chess_and_chains/ui/brand_assets/) editierbar. Die farbige Kachel verwendet Creme und Gold auf dunklem Grund. Der blaue horizontale Steg bleibt der hellen Fläche vorbehalten.
- Die [Masterbibliothek](../../design/source/connected-system/) enthält horizontale, gestapelte und kompakte Wort-/Bildmarke, reine Wortmarke, Mono- und Invers-Signet, Konstruktion, Muster, Rahmen, Icons, Atlas und drei Brettstudien.
- Laufweiten und Konstanten stehen in den SVGs und in [brand-tokens.json](brand-tokens.json). Das Signet benötigt vier Einheiten Abstand zu seiner unmittelbaren Umgebung. Die 16er App-Kachel verliert in der Rastervorschau feine Spaltzeichnung. Für häufigen Einsatz bei 16 px bleibt ein optisch vereinfachter Export als eigener Freigabepunkt offen.
- Die [Oberflächenstudien](../../design/concepts/connected-system-v01/06-oberflaechen.svg) zeigen Home, Play, Puzzle Lab und Appearance im selben System. Die dunkle Appearance-Fläche ist eine Studie. Die [Marketing-SVGs](../../marketing/source/) decken Hero, Social Preview, Release-Banner und Quadrat ab.

## Schrift und Farben

Space Grotesk 700 trägt die Wortmarke und Headlines, 400 den Lesetext. IBM Plex Mono 400/700 trägt Nummern, Status und technische Labels. Überschriften verwenden bei engen Wortmarken `−0,5` SVG-Einheiten Laufweite, kleine Versalien in Brandboards `+1` bis `+3`. Beide Schriftprojekte nennen die SIL Open Font License 1.1. Der Render auf Windows verwendet lokale Fallbacks wie Segoe UI und Consolas. Die Tk-App verwendet ihre nativen Systemschriften `TkDefaultFont` und `TkFixedFont`. [Space Grotesk](https://floriankarsten.github.io/space-grotesk/), [IBM Plex](https://github.com/IBM/plex/blob/master/LICENSE.txt)

Gold hebt Aktionen und das aktive Register hervor, ergänzt durch Unterstreichung. Blau steht für das Markenzeichen und abgeschlossene Stationen. Rot mit Kreuz markiert die aufgedeckte Lösung der aktuellen Station. Creme und Schwarz bilden die Grundflächen und Textrollen. Die geometrischen Marker des Bretts bleiben in der Canvas-Implementierung. Die [Runtime-Tokens](../../src/chess_and_chains/ui/theme.py) verwenden das vorhandene Tk-Theme-Modul. Die JSON-Datei dokumentiert den Entwurf für weitere Medien.

## Atlas in der App

Der Atlas zeigt bis zu fünf benachbarte Stationen der tatsächlich gefilterten Auswahl. Nummern sind Positionen in dieser Auswahl. Der Doppelring markiert die aktuelle Station. Ein Haken markiert eine lokal gespeicherte Lösung oder die gerade gelöste Aufgabe in einer Sitzung ohne Speicher. Ein Kreuz markiert die aufgedeckte aktuelle Lösung, sofern das Rätsel noch nie erfolgreich gelöst wurde. Der bestehende Text zeigt aktuelle Aufgabe, Feedback und bei verfügbarer Datenbank die Gesamtzahl gelöster Rätsel der Auswahl. Bei leerem Filter wird der Atlas ausgeblendet.

Tk 9 zeichnet Signet und Fenster-Icon direkt aus SVG. Wenn der SVG-Decoder fehlt, lädt Tk die aus denselben Dateien erzeugten PNGs. Das Prüfprotokoll dokumentiert Renderer, Auflösungen und Windows-Smoke. [Prüfprotokoll](../reports/2026-11-20_N02-connected-system.md)
