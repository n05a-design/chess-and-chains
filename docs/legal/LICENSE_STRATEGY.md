# License, dependency and distribution strategy

**Version:** Foundation F0 · **Status: OPEN (release-blocking)**. Keine verbindliche juristische Beratung.

## Projektziel

Offizielle Downloads dauerhaft kostenfrei. Für **eigene Starter-Quelltexte MPL-2.0**. Rechte an von Nutzern hinzugefügten SVGs, Schriftdateien, Stockfish, Regelbibliotheken und Rätseldatensätzen jeweils separat prüfen.

## Unterschiedliche rechtliche Fragen

1. **Quellcode-Lizenz**: eigene MPL-2.0-Dateien unter MPL; bei MPL-Dateien bleiben die Bedingungen selbst bei Larger-Work-Distribution relevant.
2. **Dritt-Engine**: Stockfish ist GPLv3. Bereits eine unveränderte Weiterverbreitung erfordert GPL-Nachweise und Zugang zu entsprechenden Quellen.
3. **Kombiniertes Produkt**: Einzelprozess-UCI ist ein technisches Architekturargument, keine automatische Garantie, dass ein gebündeltes Produkt ausschließlich unter MPL-2.0 vertrieben werden darf.
4. **Schachlogik**: `python-chess` GPL; alternativ `Chessnut` Unlicense nach technischer Abnahme oder eigenes Regelmodul nach eigenem Design und umfassenden Tests.
5. **Puzzle-Daten**: Lichess Puzzle Database CC0; eigene aufbereitete Daten mit Provenienz/Updatezeit, keine impliziten Bild-/Markenrechte.
6. **Artwork, Schrift, Marke**: Code-Lizenz nicht automatisch dafür gültig. Rechte und Design-Originaldateien einzeln nachweisen.
7. **Kostenloskeit**: Die offiziellen n05a-design-Versionen sollen kostenlos sein; Open-Source-Lizenzen erlauben ggf. auch Dritten Verkauf, es besteht keine weltweite Preisbindung.

## Erlaubte Vorarbeiten vor Entscheidung

Ordnerstruktur, eigene UI-Prototypen ohne GPL-Code, reiner UCI-Protokollvertrag als Spezifikation, lokale fiktive Testdaten, Recherche, Dependency-/Compliance-Inventar.

## Bis zur Entscheidung NICHT tun

Keinen Stockfish-Binary, kein python-chess als eingebaute Runtime-Dependency, keine heruntergeladenen Maia-Modellgewichte, keine konkurrierenden Screenshots, keine unbekannten SVG-/Fontdateien in die öffentlichen Release-Artefakte packen. Keine Rechtslage aus nur einer Blogmeinung ableiten.

## Entscheidungsgate vor erstem Installer

1. Owner-ADR-001 wählt A/B/C und belegt konkrete Paketgrenzen.
2. Inventar jeder Runtime-Datei inklusive separater Ausführungsdateien, Buildwerkzeuge, Fonts, Assets, Rätsel und SHA-256.
3. Alle erforderlichen Lizenztexte, Notices, Source-Links bzw. entsprechenden Quellen und nötigen Offer-/Informationspflichten in den tatsächlichen Downloads.
4. Windows/macOS/Linux-Installations-/Start-/Deinstallationsweg rechtlich und technisch gegengeprüft.
5. `THIRD_PARTY_NOTICES.md` auf tatsächlichen Lieferstand bringen; nicht auf Kandidatenliste beschränken.
6. Owner erteilt öffentliche Freigabe separat vom technischen Test-Grün.

**Quellen:** https://www.mozilla.org/en-US/MPL/2.0/FAQ/ ; https://www.mozilla.org/en-US/MPL/2.0/combining-mpl-and-gpl/ ; https://github.com/official-stockfish/Stockfish ; https://github.com/niklasf/python-chess ; https://www.gnu.org/licenses/gpl-faq.en.html
