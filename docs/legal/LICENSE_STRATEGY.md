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

## W02-Quellenaufnahme (2026-11-20)

Die folgenden Stände wurden an diesem Datum anhand der Upstream-Metadaten und
der jeweiligen Lizenz-/README-Dateien geprüft. Das ist eine technische
Quellenaufnahme, keine Prüfung der konkreten Vertriebsform:

| Kandidat | Geprüfter Upstream-Stand | Feststellung | Status für Chess & Chains |
| --- | --- | --- | --- |
| Stockfish | `official-stockfish/Stockfish` `5d03b6e578a5eedc822e4563bdbb89e762fc2a59` | Upstream nennt GPLv3. Die Distribution enthält u. a. Quellcode, Lizenz, Autorenliste und NNUE-Datei; README verlangt bei Weitergabe GPL-Nachweise und den passenden Quellcode bzw. einen Verweis darauf. README nennt außerdem ODbL für die von Leela Chess Zero bereitgestellten Trainingsdaten. | Nicht eingebunden oder gebündelt; ADR-001 offen |
| python-chess | `niklasf/python-chess` `0c6bdaccfcb3b09cdbe94b0f81e948cb2a356015` | `LICENSE.txt` ist GPLv3. README dokumentiert Regelprüfung, FEN/PGN und Varianten; dadurch wird die Lizenzfrage nicht vermieden. | Keine Dependency; ADR-001 offen |
| Chessnut | `cgearhart/Chessnut` `8af90b93f8a10437495c65733c25cde94b615bb7` | `UNLICENSE.txt` widmet den Code der Gemeinfreiheit. README und Testdateien zeigen einfache Zuggenerierung, FEN, Rochade, en passant, Umwandlung, Schach, Matt und Patt. Die geprüften Quellen belegen keine vollständige Wiederholungs-/Remisregel-Abdeckung; dies ist keine unabhängige Regelkonformitätsprüfung. Letzter Upstream-Push laut GitHub-Metadaten: 2024-11-28. | Kandidat für spätere Isolationstests; nicht installiert oder übernommen |

### Nicht bindender Optionsvergleich

| Weg | Offline-Nutzung / UX | Technik, Build und Pflichten | Hauptunsicherheit / Betriebssysteme |
| --- | --- | --- | --- |
| **A – GPL-konformer Gesamtvertrieb** | Gebündelter lokaler Engine-Betrieb kann Erststart ohne Netz ermöglichen. | Exakte Engine-/NNUE-Version, Lizenztexte, vollständige passende Quellen und Build-/Installationsinformationen inventarisieren; App-Code-Dateien mit MPL-Hinweisen getrennt erhalten und die Anwendbarkeit von MPL 2.0 §3.3 mit GPLv3 prüfen. | Ob und wie die konkrete kombinierte Anwendung vertrieben werden darf, ist keine technische Feststellung. Windows/macOS/Linux benötigen jeweils eigene Engine- und Installer-Nachweise. |
| **B – MPL-App plus getrennt installierte UCI-Engine** | Offline nach separater lokaler Installation oder Konfiguration; nicht zwingend spielbereit direkt nach Erstinstallation. | Engine-agnostische UCI-Grenze; Engine separat beziehen/aktualisieren und keine GPL-Dateien in diesem Repo/Installer bündeln, solange die Vertriebsform nicht geprüft ist. | Separater Prozess, UCI oder getrennte Installer garantieren keine rechtliche Trennung. Links/Anweisungen und Plattformpakete sind ebenfalls auf die konkrete Verteilung zu prüfen. |
| **C – ausschließlich vom Nutzer bereitgestellte Engine** | Kein Bot nach Erstinstallation, bis der Nutzer eine kompatible lokale Engine bereitstellt; danach offline verwendbar. | Lokalen Pfad auswählen und UCI-Kompatibilität/Architektur prüfen; App liefert weder Engine noch Download/Auto-Installer. | Schwächere Erststart-UX; lokaler Pfad, Version und Rechte bleiben nutzer- bzw. plattformspezifisch. |

**Vorläufige technische Leitlinie, keine Owner-Entscheidung:** Die App kann
engine-agnostisch und UCI-orientiert vorbereitet werden. Keine der Optionen wird
ausgewählt; kein Binary, Modellgewicht oder GPL-Regelwerk wird aufgenommen.
Wenn „sofort nach Erstinstallation offline gegen einen Bot“ zwingend ist, muss
der Owner zusammen mit fachkundiger Rechtsberatung insbesondere A und B anhand
des konkreten Distributionspakets entscheiden. C bleibt eine UX-Alternative,
keine Erfüllung dieses strengeren Erststartziels.

### Inventarvorlage für spätere Prüfung

| Datei/Komponente | Version / SHA-256 | Herkunft / Upstream-SHA | Lizenzquelle / SPDX | Geändert? | Runtime-/Installer-Ziel | Notices / korrespondierende Quelle | Freigabestatus |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

Die drei geprüften Projekte sind **Research-Kandidaten**, keine
Projektabhängigkeiten. Die `THIRD_PARTY_NOTICES.md`-Kandidatenliste ist kein
Nachweis einer Freigabe.

**Quellen:** https://www.mozilla.org/en-US/MPL/2.0/FAQ/ ; https://www.mozilla.org/en-US/MPL/2.0/combining-mpl-and-gpl/ ; https://github.com/official-stockfish/Stockfish ; https://github.com/niklasf/python-chess ; https://www.gnu.org/licenses/gpl-faq.en.html

## W06-SVG-Renderer-Kandidat (2026-11-20; keine Runtime-Freigabe)

CairoSVG 2.9.1 wurde für einen isolierten Renderer-/Paketierungs-PoC
evaluiert. PyPI nennt LGPL-3.0-or-later; die Laufzeit zieht u. a. cairocffi,
Pillow, cssselect2, tinycss2 und defusedxml ein. PyPI nennt für cairocffi
1.7.1 BSD. Die genaue Lizenz-/Versionsinventarisierung der gesamten
transitiven Kette und der gebündelten nativen Cairo-/Font-/Bildbibliotheken
ist **nicht abgeschlossen**. Für eine Veröffentlichung reicht die
Laufzeit-Metadatenangabe einzelner PyPI-Seiten nicht als vollständiger
Notice-/Source-/Binary-Nachweis.

Es wurde keine Abhängigkeit in `pyproject.toml` aufgenommen. CairoSVG und
cairocffi sind lokale Evaluationskandidaten; ihre temporäre Installation
erfolgte außerhalb des Repositories. Eine Integration benötigt vorher eine
vollständige Drittkomponenten-BOM, Lizenztexte/Notices, native
Bibliotheksversionen sowie echte Paketierungsprüfungen für alle freigegebenen
Zielsysteme. Details und Grenzen: `docs/reports/2026-11-20_W06_board-ui.md`,
Quellen: `docs/research/SOURCES.md`.
