# Chess & Chains

**Play. Think. Connect. – Schach offline spielen, verstehen und gestalten.**

> **Status: frühe Implementierung, noch nicht veröffentlichungsreif.** Das Repository enthält einen unabhängigen Schachregel-Kern und einen lokalen W06-Desktopprototyp für zwei Personen mit ausdrücklich provisorischen geometrischen Testfiguren. Engine, Rätselpaket und Installer fehlen.

Chess & Chains soll eine **dauerhaft kostenlos angebotene, quelloffene und offlinefähige Desktop-Schach-App** werden: lokal spielbare Computergegner mit einstellbarer Schwierigkeit, anspruchsvolle Taktikaufgaben und ein eigenständiges Design auf Basis eigener SVG-Schachfiguren und Bretter.

[English](README.md) · [Manifest](MANIFEST.md) · [Roadmap](docs/roadmap/ROADMAP.md) · [Offene Fragen](docs/questions/OPEN_QUESTIONS.md)

## Geplanter Funktionsumfang

- Offline gegen lokale UCI-Engines spielen, ohne Benutzerkonto oder Pflichtserver.
- Mehrere einstellbare Spielstärken und später unterschiedliche Bot-Charakteristiken.
- Lokale Rätselpakete mit **Lichess-Puzzle-Rating ab 1000**; das Rating ist nicht mit persönlicher Schach-Elo gleichzusetzen.
- Eigenes visuelles Erscheinungsbild mit modularen SVG-Figurensets, Brettdesigns und Themes.
- Lokale Partien, Trainingsverlauf, PGN/FEN und langfristig eine Taktik-Analyse.
- Windows und macOS zuerst, Linux nach gesonderter Qualitätssicherung.

## Was bereits vorhanden ist

Dokumentierte Projektbasis, ein **GUI-freier Python-Regelkern** (legale Züge, FEN/SAN/PGN, Remisregeln, Undo/Redo; Perft- und Golden-Tests) und ein lokaler Tk-Prototyp mit:

- Partie für zwei Personen und **Bot-Modus** (Bot spielt Weiß oder Schwarz) über einen asynchronen Game-Controller,
- UCI-Prozessadapter, getestet **nur mit einer projekteigenen Mock-Engine** – diese ist **keine Schach-KI**,
- sechs datengetriebenen Bot-Stufen (Optionen nur, wenn die Engine sie anbietet; Spielstärke **nicht kalibriert**),
- **Puzzle Lab** mit Streaming-Importer für das Lichess-CSV-Format, Rating ≥ 1000, Paketen und fünf projekteigenen Demo-Rätseln,
- lokaler SQLite-Speicherung (Partien, Rätselfortschritt), JSON-Einstellungen und DE/EN-Oberfläche.

Nicht vorhanden: gebündelte oder getestete echte Engine (z. B. Stockfish, ADR-001 offen), Lichess-Rätseldaten, Original-SVG-Figuren, Installer. Der Prototyp ist nicht release-fertig.

## Entwicklerstart

```bash
python -m unittest discover -s tests -v
python scripts/verify_starter.py
python -m pip install -e .
python -m chess_and_chains --headless-check
python -m chess_and_chains
```

Eine bereits lokal installierte UCI-Engine kann zur Entwicklung über `CHESS_AND_CHAINS_ENGINE=/pfad/zur/engine` oder *Engine-Einstellungen…* genutzt werden; die App lädt niemals Engines herunter. Der Standardaufruf öffnet den lokalen Tk-Prototyp; `--headless-check` prüft die Verfügbarkeit ohne Fenster. Für Tk-Unterstützung muss die Python-Installation Tk enthalten. Der Regeldomänenkern hat keine Laufzeitabhängigkeit auf eine Schachbibliothek.

## Lizenz

Eigene Quelltexte sind als **MPL-2.0** vorgesehen. Der W05-Regelkern wird eigenständig implementiert. **Stockfish ist GPLv3**, ebenso sind weitere Drittkomponenten separat zu prüfen. Eine vollständig gebündelte Offline-Distribution darf erst nach schriftlicher Lizenz- und Architekturentscheidung erfolgen. Die offiziellen Downloads sollen stets kostenlos bleiben; MPL/GPL verbieten Dritten jedoch keine entgeltliche Weitergabe.

[Rechte- und Lizenzstrategie](docs/legal/LICENSE_STRATEGY.md) · [Dritthinweise](THIRD_PARTY_NOTICES.md) · [Design-/Asset-Verzeichnis](docs/design/ASSET_REGISTER.csv) · [Copilot-Aufträge](prompts/README.md)

*Chess & Chains ist ein unabhängiges Projekt und nicht mit Lichess, Stockfish oder Drittanbietern verbunden.*
