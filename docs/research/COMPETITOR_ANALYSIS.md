# Konkurrenzanalyse – Chess & Chains

**Desk Research vom 19.11.2026; Quellengegenprobe 20.11.2026.** Die
Erstaufnahme unten ist eine qualitative Hypothesenliste, keine vollständige
Feature-Verifikation. Quellen-/Featuregrenzen stehen in der datierten
Gegenprobe und im W04-Bericht. Es gab keine Produktinstallation und keine
vollständigen Usability-Tests. Chancen sind **Hypothesen**, keine
nachgewiesenen Marktlücken.

| Produkt | Primärer Schwerpunkt (Quelle) | Konsequenz für Chess & Chains | Was nicht kopieren |
| --- | --- | --- | --- |
| **Lucas Chess** | Kostenloser Desktop-Schach- und Trainingsclient mit Engine-Gegnern und Trainingswerkzeugen ([Website](https://lucaschess.pythonanywhere.com/index?lang=de)) | Wettbewerber bei offline Training; Einfachheit und eigene Designsprache priorisieren; Funktionsdichte bewusst begrenzen | Dialoge, Icons, Aufgaben-/Fensteranordnung als fremde Originale |
| **En Croissant** | Open-Source-Cross-Platform-GUI, Engines und Partien-/Analyse-Workflow ([Homepage](https://encroissant.org/)) | Überschneidung bei Engine/GUI; Differenzierung durch kuratiertes Offline-Puzzle-Onboarding und SVG-/UI-Personalisierung | Layout-/Branding-Originale |
| **ChessX** | Freie Schach-Datenbank, Analyse und Partiemanagement ([Homepage](https://chessx.sourceforge.io/)) | Keine 1:1-Konkurrenz beim einfachen Offline-Puzzle-first-Produkt; PGN-Interoperabilität sicherstellen | Dichte Datenbank-UX in MVP |
| **Scid vs. PC** | Tiefes Schach-Datenbanktool mit Engine-Analyse, Statistik, Eröffnungen ([Website](https://scidvspc.sourceforge.net/)) | Lernquelle für PGN/FEN-/Analyse-Interoperabilität, nicht MVP-Scope übernehmen | komplexe Menüs/Informationsdichte |
| **PyChess** | Freier Desktop-Schachclient ([GitHub](https://github.com/pychess/pychess)) | Referenz für plattformübergreifende Schach-Workflows; eigene Bedienhypothesen validieren | Quellcode ohne Lizenzanalyse oder UI-Designkopie |
| **Lichess** | Freier Schachserver mit Training, Analyse, Online-Spiel ([Website](https://lichess.org/)) | Datenquelle für freie CC0-Rätsel; lokale Offline-first-Nutzung als Produktziel | Lichess-Markenzeichen, UI oder Bildassets ungeprüft |
| **Chess.com** | Umfangreiche Online-Schachplattform mit Bots, Rätseln, Training ([Website](https://www.chess.com/)) | Zielgruppe erwartet Politur und klares Stärke-Feedback; keine ungesicherten Premium-Preis-/Funktionsaussagen | Branding, Bots, Bilder, Texte |

## Differenzierungshypothese

**„Beautiful offline tactical chess“**: bewusst fokussierte Bot-/Rätsel-App, keine Loginpflicht, kontrollierbare Daten, echte Design-Freiheit, niedrige UI-Reibung und anspruchsvolle Übungen ab Rating 1000. Das ist eine **Produktpositionierung zur Validierung**, keine empirisch bewiesene Nische.

## Benchmarks für spätere UX-Studie

- Time-to-first-game nach Installation und Offline-Test (Ziel als Hypothese: <60 s).
- Time-to-first-puzzle, Sichtbarkeit des Rating-Filters, Verständlichkeit von Hinweis/Lösung.
- Zugbedienung per Klick + Drag, Fokuszustände, Zoom/DPI, Farberkennung, Tastatursteuerung.
- Fehlermeldung bei fehlender/abgestürzter Engine.
- Verständlichkeit des Lizenz-/Download-Modells und Datenspeicherorts.

## Leitfaden für Copilot-Recherche

1. Gegenprobe für jedes Feature mit datierten Produktdokumenten oder realem Test; keine Vermutung als Verifikation.
2. Pro Wettbewerber Stärken, Schwächen (nur belegte), relevante Bedienpfade, Plattform-/Offlinefähigkeit und Lizenz in separate Research-Matrix.
3. Nur Links/selbst angefertigte abstrakte Skizzen speichern. **Keine fremden Screenshots ins öffentliche Repo übernehmen**, wenn Nutzungsrecht ungeklärt.
4. Jede Hypothese in einen überprüfbaren, späteren UX-Test übersetzen; keine ungeprüfte Behauptung „besser als X“.

## Datierte Quellengegenprobe (2026-11-20)

Die folgenden Angaben stammen aus den offiziellen, am Datum der Aufnahme
abrufbaren Seiten und Projektmetadaten. Es wurden keine Apps installiert und
keine Offline-, Barrierefreiheits- oder Usability-Tests durchgeführt; wo
Plattform oder Offline-Verhalten nicht ausdrücklich belegt sind, bleibt der
Punkt **unverifiziert**. Details und SHAs: `docs/reports/2026-11-20_W04_competitor-design.md`.

| Produkt | Auf der offiziellen Quelle beobachtbar | Nicht belegt / Bedeutung für Chess & Chains |
| --- | --- | --- |
| Lucas Chess | Offizielle Seite nennt 57 vorbereitete Engines, konfigurierbare Engine-Stärke und umfangreiche Trainingsarten. | „PC“ steht auf der Seite, konkrete aktuelle Plattformmatrix und Offline-Erststart wurden nicht getestet. Funktionsbreite macht fokussierte Onboarding-Hypothesen relevant, nicht eine nachgewiesene Lücke. |
| En Croissant | Offizielle Seite beschreibt eine Open-Source-Cross-Platform-GUI, Analyse, persönliche Datenbank und einen Download-Manager für Engines/Datenbanken; Repository-Metadaten nennen GPL-3.0. | Keine eigene Prüfung, ob/wie der Client ohne Netzwerk und bereits installierte Daten nutzbar ist. Die Download-Funktion ist kein Beleg für ausschließlich offlinefähige Erstinstallation. |
| ChessX | Offizielle Seite bewirbt Windows, macOS und Linux, PGN-Datenbanken, Engines und Open-Source-Quellcode. | Aktuelle Release-/Offline-/Accessibility-Abnahme wurde nicht geprüft. PGN-Austausch bleibt ein sinnvoller Interoperabilitätsmaßstab. |
| Scid vs. PC | Offizielle Seite beschreibt Datenbanken, Engines und Spiel gegen Computer; sie führt Version 4.27, Windows-Pakete und ältere macOS-/Linux-Hinweise auf. | Seitenaktualität und heutige Plattformunterstützung sind unklar; keine Installations- oder Offline-Prüfung. |
| PyChess | GitHub-Projektbeschreibung nennt einen Desktop-Schachclient für Linux/Windows/macOS; Repo-Metadaten nennen GPL-3.0. | Diese Metadaten belegen nicht die heutige Funktions-/Offline-Abnahme. Kein Quellcode wird übernommen. |
| Lichess | Offizielle Website bezeichnet sich als Online-Schachserver. Die Open Database stellt rated Puzzle-CSV unter CC0 bereit; ihre Seite nennt 6,193,530 Rätsel, Felder und die Position-vor-Gegnerzug-Konvention. | Die Web-App ist keine Offline-GUI-Referenz. Rätseldaten sind nicht in diesem Repository; Offline-Import, Filterung und Rechte an sonstigen Assets bleiben separate Arbeit. |
| Chess.com | Offizielle Startseite stellt Community, Bots, Rätsel und mobile Apps heraus. | Die gelesene Seite belegt keine Offline-Desktop-Funktion. Keine Aussage über bezahlte Produktgrenzen oder Bot-Qualität abgeleitet. |

Die Position „offline, fokussiert, visuell anpassbar“ bleibt eine zu prüfende
Produkthypothese. Eine Marktlücke oder ein Wettbewerbsvorteil ist nicht
nachgewiesen.

### Vergleich der für W04 geforderten Kriterien

| Produkt | Offline / Plattform | Bots, Engines und Puzzle-Suche | Themes / Datenexport | Zielgruppe und UX-Komplexität |
| --- | --- | --- | --- | --- |
| Lucas Chess | Seite beschreibt Desktop-/PC-Produkt; heutige OS-Matrix und Offline-Erststart **nicht getestet**. | 57 vorbereitete Engines und verschiedene Trainingsarten laut Produktseite; Puzzle-Suchfelder nicht verifiziert. | Theme-Freiheit und Exportformat nicht verifiziert. | Breite Trainingsauswahl ist Quelle/Produktumfang; „dicht“ ist eine UX-Hypothese, keine Nutzungsbeobachtung. |
| En Croissant | Website nennt Cross-Platform; Offline-Verhalten **nicht getestet**. | Engine-/Datenbank-Downloadmanager und Analyse laut Website; Bot-Auswahl und Puzzle-Suche nicht verifiziert. | Theme-Freiheit und Exportformat nicht verifiziert. | Analyse-/Datenbank-Workflow laut Website; Komplexität nicht getestet. |
| ChessX | Website listet Windows, macOS und Linux; Offline-Verhalten **nicht getestet**. | Engines und Datenbank laut Website; Puzzle-Suche nicht verifiziert. | PGN ist der beschriebene Datenbankkontext; konkrete Exportfunktion und Theme-Freiheit nicht getestet. | Datenbank-/Partieverwaltung als Produktbereich; Dichte-Einschätzung ist Hypothese. |
| Scid vs. PC | Website führt Windows, macOS und Linux-Hinweise auf; Aktualität unklar; offline nicht getestet. | Spiel gegen Computer, Engines und Datenbanken auf Website beschrieben; Puzzle-Suche nicht verifiziert. | Theme-Freiheit und Exportformat nicht verifiziert. | Umfangreiche Datenbank-/Analysefunktionen; „komplex“ bleibt ungeprüfte UX-Hypothese. |
| PyChess | Repo-Beschreibung nennt Linux, Windows und macOS; offline nicht getestet. | Konkrete Bot-/Puzzle-Funktionen in dieser Quellenaufnahme nicht verifiziert. | Themes und Export nicht verifiziert. | Desktop-Client; Komplexität mangels UI-Test nicht bewertet. |
| Lichess | Offizielle Seite beschreibt Online-Schachserver; keine Offline-Desktop-GUI verifiziert. | Puzzle-CSV-Datenbank (CC0) vorhanden; interaktive Puzzle-Suchfunktionen dieser Web-App nicht untersucht. | Puzzle-CSV-Schema dokumentiert; UI-Themes und sonstiger Export nicht verifiziert. | Online-Community/Training, wie die Website sich darstellt; Komplexität nicht getestet. |
| Chess.com | Startseite bewirbt Web-/Mobile-Angebot; offline nicht belegt. | Bots und Rätsel auf der Startseite beworben; Auswahl-/Suchumfang nicht untersucht. | Themes und Export nicht verifiziert. | Community und Training laut Startseite; Komplexität nicht getestet. |

„Nicht verifiziert“ bedeutet, dass es in dieser zeitlich begrenzten Recherche
keinen ausreichenden Primärquellenbeleg gab; es ist keine Aussage, dass das
Produkt die Funktion nicht besitzt. Kein Export-, Bot-Elo-, Offline- oder
Accessibility-Vergleich wurde praktisch ausgeführt.
