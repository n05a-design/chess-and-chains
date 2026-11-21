# Chess & Chains

**V.0.0.1 · Entwicklungsstand.** [Änderungsverlauf](CHANGELOG.md) · [Versionspflege](docs/governance/GOVERNANCE.md#projektversion)

**Play. Think. Connect. – Schach offline spielen, verstehen und gestalten.**

Chess & Chains soll eine **dauerhaft kostenlos angebotene, quelloffene und offlinefähige Desktop-Schach-App** werden: lokal spielbare Computergegner mit einstellbarer Schwierigkeit, anspruchsvolle Taktikaufgaben und ein eigenständiges Design auf Basis eigener SVG-Schachfiguren und Bretter.

[English](README.md) · [Manifest](MANIFEST.md) · [Roadmap](docs/roadmap/ROADMAP.md) · [Offene Fragen](docs/questions/OPEN_QUESTIONS.md)

## Geplanter Funktionsumfang

- Offline gegen lokale UCI-Engines spielen, ohne Benutzerkonto oder Pflichtserver.
- Mehrere einstellbare Spielstärken und später unterschiedliche Bot-Charakteristiken.
- Lokale Rätselpakete mit **Lichess-Puzzle-Rating ab 1000**; das Rating ist nicht mit persönlicher Schach-Elo gleichzusetzen.
- Eigenes visuelles Erscheinungsbild mit modularen SVG-Figurensets, Brettdesigns und Themes.
- Lokale Partien, Trainingsverlauf, PGN/FEN und langfristig eine Taktik-Analyse.
- Windows und macOS zuerst, Linux nach gesonderter Qualitätssicherung.

GitHub ist der Entwicklungsort und beschreibt, wie das fertige Produkt funktionieren soll. Nach Fertigstellung und Freigabe erscheint die App auch auf GitHub und steht zusammen mit den anderen Programmen im hauseigenen Software-Katalog kostenlos zum Download bereit.

## Was bereits vorhanden ist

Der **GUI-freie Python-Regelkern** unterstützt legale Züge, FEN/SAN/PGN, Remisregeln und Rückgängig/Wiederholen. Perft- und Golden-Tests decken die Umsetzung ab. Der Regelkern erkennt tote Stellungen in kurzen Zwangsfolgen zu Patt oder ungenügendem Material. Die allgemeine Erkennung und die Inhaberabnahme stehen aus.

Der lokale Tk-Prototyp umfasst folgende Funktionen.

- Partie für zwei Personen und **Bot-Modus** (Bot spielt Weiß oder Schwarz) über einen asynchronen Game-Controller,
- **Connected System** mit eigener Wortmarke, Vorderansichten V.02 und separatem Draufsichtssatz als Original-SVGs,
- UCI-Prozessadapter, getestet **nur mit einer projekteigenen Mock-Engine** – diese ist **keine Schach-KI**,
- sechs datengetriebenen Bot-Stufen (Optionen nur, wenn die Engine sie anbietet; Spielstärke **nicht kalibriert**),
- **Puzzle Lab** mit Streaming-Importer für das Lichess-CSV-Format, Rating ≥ 1000, Paketen und fünf projekteigenen Demo-Rätseln. Filter für Thema und Rating zeigen im Atlas of Moves den Fortschritt je Auswahl,
- Remisanspruch bei dreifacher Wiederholung oder nach der 50-Züge-Regel, auch durch Ansage eines legalen Zugs,
- lokaler SQLite-Speicherung für Rätselfortschritt und Partien. Die Partiebibliothek öffnet gespeicherte Partien im Zweispielermodus und übernimmt das PGN-Ergebnis. Bei neu gespeicherten Partien bleiben Aufgabe, Remisanspruch und ein eventuell angesagter Zug erhalten. Über die Bibliothek lässt sich pro Vorgang eine UTF-8-PGN-Datei importieren oder exportieren. Einstellungen liegen in JSON, die Oberfläche ist auf Deutsch und Englisch verfügbar.

Der Inhaber hat die Original-SVG-Figuren unter MPL-2.0 freigegeben. Tk 9 zeichnet ihre SVGs direkt. Ältere Tk-Versionen verwenden die daraus erzeugte PNG-Grafiktafel. Die eigenen Brettdesigns, eine getestete echte Engine, das geplante Rätselangebot und ein Installer gehören zur weiteren Entwicklung.

## Entwicklerstart

```bash
python -m unittest discover -s tests -v
python scripts/verify_starter.py
python -m pip install -e .
python -m chess_and_chains --version
python -m chess_and_chains --headless-check
python -m chess_and_chains
```

Eine bereits lokal installierte UCI-Engine kann zur Entwicklung über `CHESS_AND_CHAINS_ENGINE=/pfad/zur/engine` oder *Engine-Einstellungen…* genutzt werden; die App lädt niemals Engines herunter. Der Standardaufruf öffnet den lokalen Tk-Prototyp; `--headless-check` prüft die Verfügbarkeit ohne Fenster. Für Tk-Unterstützung muss die Python-Installation Tk enthalten. Der Regeldomänenkern hat keine Laufzeitabhängigkeit auf eine Schachbibliothek.

*Engine testen* prüft den UCI-Handshake und wartet auf `readyok`. Bei Erfolg zeigt der Dialog den Namen und die Zahl der gemeldeten Optionen. Der Testlauf beendet seinen Prozess. Die Schaltfläche *Speichern* übernimmt den Pfad.

Mit Tk 9 lässt sich ein lokaler Brettentwurf für einen Programmaufruf in der App anzeigen. Beispiel: `python -m chess_and_chains --board-design assets/boards/source/board-template.svg`. Die [SVG-Lieferanleitung](assets/boards/source/README.md) beschreibt die Formate für Gesamtbretter und einzelne Felder.

`python -m chess_and_chains --piece-view top` zeigt die Draufsicht der Figuren in Partie und Rätsel. Beim normalen Start erscheint die Vorderansicht. Beide Ansichten verwenden [editierbare Einzel-SVGs mit einem gemeinsamen Figurenmaß pro Ansicht](assets/chess_pieces/source_svg/README.md) und einen lokalen PNG-Fallback für Tk ohne SVG-Unterstützung.

## Lizenz

Eigene Quelltexte sind als **MPL-2.0** vorgesehen. Der W05-Regelkern wird eigenständig implementiert. **Stockfish ist GPLv3**, ebenso sind weitere Drittkomponenten separat zu prüfen. Eine vollständig gebündelte Offline-Distribution darf erst nach schriftlicher Lizenz- und Architekturentscheidung erfolgen. Die offiziellen Downloads sollen stets kostenlos bleiben; MPL/GPL verbieten Dritten jedoch keine entgeltliche Weitergabe.

[Rechte- und Lizenzstrategie](docs/legal/LICENSE_STRATEGY.md) · [Dritthinweise](THIRD_PARTY_NOTICES.md) · [Design-/Asset-Verzeichnis](docs/design/ASSET_REGISTER.csv) · [Copilot-Aufträge](prompts/README.md)

*Chess & Chains ist ein unabhängiges Projekt und nicht mit Lichess, Stockfish oder Drittanbietern verbunden.*
