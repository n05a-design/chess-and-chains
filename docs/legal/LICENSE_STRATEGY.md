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

**Owner-Eingaben und aktueller Prüfauftrag (2026-11-20):** Weg B wurde
zunächst als Implementierungsrichtung gewählt. Danach bestätigte der Owner,
dass ein Bot direkt nach der App-Installation offline spielbereit sein muss,
und beauftragte die Prüfung von Weg A als möglichem GPL-konformen
Gesamtvertrieb. A ist **noch nicht** ausgewählt oder rechtlich freigegeben.
Bis zu einer fachkundigen Prüfung der konkreten Anwendung und Lieferform wird
nichts gebündelt, heruntergeladen oder als freigegeben dargestellt. Kein
Engine-Binary, Modellgewicht oder GPL-Regelwerk wurde aufgenommen. Q-002 ist
als Anforderung geschlossen; Umsetzung und Distribution bleiben offen.

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

## W02-Nachtrag – möglicher GPL-Gesamtvertrieb (2026-11-20; Recherche, keine Freigabe)

Der Owner verlangt einen direkt nach Installation offline verfügbaren Bot und
beauftragte die Prüfung von Weg A als möglichem Vertriebsweg. Offizielle
Mozilla-Hinweise zur MPL 2.0 beschreiben in FAQ Q14 die Kombination von
MPL-Code mit einer vorhandenen GPL-Arbeit unter MPL §3.3: Die MPL-Arbeit darf
nicht als inkompatibel markiert sein, es muss eine tatsächliche Kombination
mit der Sekundärlizenz-Arbeit geben, und MPL-Code muss den Empfängern
zusätzlich auch unter der GPL angeboten werden. Die offizielle Mozilla-
Anleitung verlangt außerdem sorgfältige Erhaltung von Datei-Hinweisen und
GPL-kompatible MPL-Änderungen. Das ist eine mögliche Lizenzmechanik, keine
Aussage, dass Chess & Chains und eine konkrete Engine rechtlich eine
zulässige Kombination bilden.

Die offizielle GPLv3-Fassung definiert in §5 eine Ausnahme für Aggregate aus
getrennten und unabhängigen Werken, die nicht zu einem größeren Programm
kombiniert sind. Die Einordnung einer App, die eine Engine gezielt startet,
und eines gemeinsamen Installers/Bundles ist damit nicht aus „separate
Prozesse“, UCI, Dateigrenzen oder einem gemeinsamen Download allein
abzuleiten. Bei Weitergabe von Objektcode verlangt §6 eine zulässige Form der
Bereitstellung des maschinenlesbaren Corresponding Source; die Definition
umfasst insbesondere nötige Quellen zum Erzeugen, Installieren, Ausführen und
Ändern sowie Build-Skripte. GPLv3 §5(d) enthält außerdem Anforderungen an
„Appropriate Legal Notices“ bei erfassten interaktiven Oberflächen; die
konkrete Anwendbarkeit ist Teil der Rechtsprüfung.

Stockfishs offizielle README der Version `sf_19` (Commit
`edb0d9db6731067ec50ce619ff372b463bc4dd5d`) nennt GPLv3 und listet
`Copying.txt`, `AUTHORS`, vollständigen `src`-Quellcode mit Makefile und
Netzwerkdatei mit Endung `.nnue` als Distributionsbestandteile; bei
Binärdistributionen kann das Netz eingebettet sein. Die README verlangt für
weitergegebene Stockfish-Kopien die Lizenz und vollständigen Quellcode oder
einen Verweis auf den Quellcode, der genau die verteilte Binary erzeugt.
Sie nennt außerdem LCZero-Trainingsdaten unter ODbL. Daraus wird keine
unabhängige Lizenzbewertung des jeweiligen NNUE-Artefakts oder Trainings-
materials abgeleitet; beides muss in der konkreten Stückliste getrennt
verifiziert werden.

**Prüfergebnis:** Weg A ist als Prüfoption technisch plausibel, aber nicht
als rechtlich abgenommen. Vor jeder Implementierung/Bündelung sind mindestens
die konkrete Engine/Version/Architektur, NNUE-Provenienz, Patch- und
Buildkette, Corresponding Source, Lizenztexte/Notices, MPL-Datei- und
Copyright-Inhaberschaft, GPL-Anzeige in der UI sowie die Abgrenzung
„Aggregate vs. kombinierte Arbeit“ für genau den Installer von fachkundiger
Rechtsberatung zu prüfen. Die offizielle kostenlose Preisgestaltung beseitigt
keine GPL-Pflichten. Es wurden weder Stockfish-Dateien noch GPL-Komponenten
heruntergeladen oder hinzugefügt. `ADR-001` bleibt OPEN/RELEASE BLOCKER.

## Tatsächlicher lokaler IV-A-Bestand (28.11.2026)

Stockfish 19 stammt aus dem offiziellen macOS-Universalarchiv
`stockfish-macos-universal.tar.gz` für `sf_19`, Commit
`edb0d9db6731067ec50ce619ff372b463bc4dd5d`. Das lokal freigegebene Binary
ist unverändert. Das Inventar und die SHA-256-Werte wurden am lokal
vorhandenen Archiv und an den extrahierten Dateien geprüft.

| Bestandteil | Lokale Identität und Herkunft | Lizenz- und Quellenbezug |
| --- | --- | --- |
| Engine | `binary/stockfish`, arm64/x86_64, SHA-256 `8eed61129d1493c5d1f2fd9323f0c54c47ac49319911fbde18c6b9c87e8b13c5` | Stockfish nennt GPLv3. Der Quellenstand ist der obige Commit. Der Quellbaum im Archiv enthält `src/Makefile` mit `macos-lipo` und die Skripte zum Netzbezug und zur Einbettung. |
| Eingebettetes NNUE | Ein SFNNv16-Netz. `src/evaluate.h` und der UCI-Standardwert identifizieren `nn-1a298aa575a0.nnue`. Das macOS-Buildziel bindet das Netz für den Universal-Build ein. | Die Ressource gehört zur Stockfish-Distribution. `scripts/net.sh` nennt den Stockfish-Netzwerkdienst und das offizielle Netzarchiv als Quellen. |
| Exportiertes NNUE | `binary/exported.nnue`, über `export_net` aus genau dieser Binary gewonnen, SHA-256 `1a298aa575a085434d29027978dc36867fe9c5bcea9376654b7a8eba1e52dfc2`. Der Präfix stimmt mit dem Upstream-Dateinamen überein. Die Registry prüft den vollständigen Hash für `EvalFile`. | Separat als Lieferbestandteil erfassen, falls die Ressource als eigene Datei weitergegeben wird. Die Upstream-README nennt ODbL für LCZero-Trainingsdaten. Für die Netzdatei und deren Trainingsmaterial bleibt eine gesonderte Rechteprüfung offen. |
| Lizenz, Autoren und Herkunft | `licenses/Copying.txt` `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986`, `licenses/AUTHORS` `59c7a457f0665f26453ad90f474db7cd328f0983a7e8031cded5d6f25e1a1eb6`, `licenses/README.md` `ae3ef5c2282400d643c6e923d0b8b8d8fe35cf98762701f0379c79bde16c3a26` | Lizenztext, Autoren- und Copyright-Hinweise bei Weitergabe erhalten. |

Für eine etwaige Online-Weitergabe von Objektcode kommen die Pflichten
aus GPLv3 §§ 4–6 und insbesondere der Quellenzugang gemäß § 6(d) in
Betracht. Dazu das genaue Lieferbinary mit maschinenlesbarem
Corresponding Source verknüpfen, den gleichwertigen Zugang ohne
Zusatzkosten gewährleisten und Quellenzugang sowie Lizenz- und
Urheberhinweise am Download ausweisen. Der Quellumfang umfasst das
zugehörige Netz und alle benötigten Build- und Installationsskripte.
Anwendbare Installationsinformationen nach § 6 für ein User Product
und gegebenenfalls § 5(d) für interaktive Oberflächen sind am konkreten
Liefermodell zu prüfen. Die Quellen und Bauregeln des Releases sind
identifiziert. Der Release-Build wurde lokal weder nachgebaut noch
bitweise reproduziert.

Für **A** bleibt zu prüfen, ob die konkrete gemeinsame Distribution
unter GPLv3 erfolgen kann und wie MPL § 3.3 auf die betroffenen
Dateien anzuwenden ist. Für **B** sind getrennte Beschaffung,
Installergrenzen und die Pflichten bei jeder Weitergabe eigener
Engine-Artefakte zu prüfen. **C** erfordert eine vom Nutzer bereitgestellte
Engine. Die Pflicht aus Q-002 zur Offline-Spielbereitschaft direkt nach
Installation bleibt für B und C eine offene Produktfrage. ADR-001 und
Q-001 bleiben das Gate für die Auswahl. IV-A betrifft die genehmigte
lokale Nutzung. Die Projektlizenz bleibt MPL-2.0.

[Offizieller Release](https://github.com/official-stockfish/Stockfish/releases/tag/sf_19) ·
[Quellcommit](https://github.com/official-stockfish/Stockfish/commit/edb0d9db6731067ec50ce619ff372b463bc4dd5d) ·
[NNUE-Bezug im Upstream-Skript](https://github.com/official-stockfish/Stockfish/blob/sf_19/scripts/net.sh) ·
[GPLv3-Lizenztext des Releases](https://github.com/official-stockfish/Stockfish/blob/sf_19/Copying.txt) ·
[Mozilla-Leitfaden zu MPL und GPL](https://www.mozilla.org/en-US/MPL/2.0/combining-mpl-and-gpl/) ·
[Abnahme und Prüfsummen](../reports/2026-11-28_IV-A-stockfish-integration-compliance.md)
