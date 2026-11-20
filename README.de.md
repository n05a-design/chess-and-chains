# Chess & Chains

**Play. Think. Connect. – Schach offline spielen, verstehen und gestalten.**

> **Status: frühe Implementierung, noch keine spielbare Desktop-App.** Das Repository enthält jetzt einen unabhängigen, GUI-freien Schachregel-Kern, aber noch kein Brett-UI, keine Engine, kein Rätselpaket und keinen Installer. Der übrige Funktionsumfang ist weiterhin Zielbild, sofern nicht ausdrücklich als implementiert markiert.

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

Dokumentierte Projektbasis, Arbeitsaufträge und ein **GUI-freier Python-Regelkern** mit legalen Zügen, FEN/PGN und Spielhistorie (W05-Validierung läuft). Engine, Brett-UI, Puzzle-Datenbank und Installer sind noch nicht implementiert.

## Entwicklerstart

```bash
python -m unittest discover -s tests -v
python scripts/verify_starter.py
python -m pip install -e .
python -m chess_and_chains
```

Der letzte Aufruf zeigt nur einen Hinweis zum Projektstatus und startet keine Partie. Regeltests laufen mit `python -m unittest discover -s tests -v`; der Regeldomänenkern hat keine Laufzeitabhängigkeit auf eine Schachbibliothek.

## Lizenz

Eigene Quelltexte sind als **MPL-2.0** vorgesehen. Der W05-Regelkern wird eigenständig implementiert. **Stockfish ist GPLv3**, ebenso sind weitere Drittkomponenten separat zu prüfen. Eine vollständig gebündelte Offline-Distribution darf erst nach schriftlicher Lizenz- und Architekturentscheidung erfolgen. Die offiziellen Downloads sollen stets kostenlos bleiben; MPL/GPL verbieten Dritten jedoch keine entgeltliche Weitergabe.

[Rechte- und Lizenzstrategie](docs/legal/LICENSE_STRATEGY.md) · [Dritthinweise](THIRD_PARTY_NOTICES.md) · [Design-/Asset-Verzeichnis](docs/design/ASSET_REGISTER.csv) · [Copilot-Aufträge](prompts/README.md)

*Chess & Chains ist ein unabhängiges Projekt und nicht mit Lichess, Stockfish oder Drittanbietern verbunden.*
