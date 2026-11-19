# Konkurrenzanalyse – Chess & Chains

**Desk Research vom 19.11.2026.** Quellen: jeweilige offizielle Produktseiten/Repositories; keine eigene Produktinstallation, keine vollständigen Usability-Tests. Kennzeichnung von Chancen als **Hypothese**, nicht als nachgewiesene Marktlücke.

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
