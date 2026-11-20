# ADR-001 – Engine- und Lizenzarchitektur

**Status: OPEN – RELEASE BLOCKER; GPL-Gesamtvertrieb A wird geprüft.**

## Ausgangslage

Eigener Code soll möglichst MPL-2.0 bleiben. Stockfish ist GPLv3; `python-chess` ist GPLv3. Kommunikation per UCI und separate Prozesse sind **keine automatische Freistellung** von möglichen Pflichten bei einer eng verbundenen gemeinsamen Distribution.

## Zu entscheidende Wege

- **A (einfacherer Integrationsrahmen):** GPLv3-konforme kombinierte Anwendung/Distribution; eigene Quelldateien ggf. weiterhin mit ihren ursprünglichen MPL-Hinweisen, kompatible Gesamtvertriebsbedingungen und sämtliche Drittpflichten erfüllen.
- **B (MPL-Ziel):** ausschließlich eigene/MPL-kompatible App plus z. B. Unlicense-Regelwerk; Engines als eigenständige, austauschbare UCI-Programme. Getrennte Installation oder ggf. getrennte Bundles; rechtlich prüfen, ob konkrete Veröffentlichungsart eine kombinierte Arbeit ist.
- **C (Zwischenlösung):** Open-Source-UCI-Host ohne vorinstallierten Engine-Binary; Benutzer bringt lokal bereits installierte Engine mit. Für „sofort offline spielbar nach Installation“ reicht das allein NICHT.

## Empfehlung / Sperre

Der Owner wählte zunächst Weg B als Implementierungsrichtung: engine-agnostisch
mit konfiguriertem externem UCI-Prozess. Danach bestätigte er die Anforderung,
dass ein Bot direkt nach App-Installation offline spielbereit sein muss, und
beauftragte die Prüfung von Weg A als möglichem GPL-konformen Gesamtvertrieb.
A ist **noch nicht** ausgewählt oder rechtlich freigegeben. Kein Stockfish-
Binary im Repo/Installer und kein `python-chess` als Dependency. Vor jeder
konkreten Distribution ist fachkundige Lizenzprüfung erforderlich; UCI und
separate Prozesse garantieren keine rechtliche Trennung.

## Quellen

https://github.com/official-stockfish/Stockfish · https://www.mozilla.org/en-US/MPL/2.0/FAQ/ · https://www.mozilla.org/en-US/MPL/2.0/combining-mpl-and-gpl/ · https://www.gnu.org/licenses/gpl-faq.en.html

## Owner-Entscheid

**Owner-Eingaben (2026-11-20):** Zunächst Weg B als Implementierungsrichtung;
danach die Pflichtanforderung, direkt nach App-Installation offline gegen
einen Bot spielen zu können, sowie die Beauftragung, Weg A als möglichen
GPL-konformen Gesamtvertrieb zu untersuchen. Dies ist ein Rechercheauftrag,
keine Annahme oder Vertriebsfreigabe von A.

Für W07 umfasst die Freigabe weiterhin nur einen konfigurierten externen
UCI-Prozess und lokale Mock-Tests. Sie genehmigt weder eine bestimmte Engine
noch deren Binary, Download, Installer, GPL-Komponente oder gemeinsame
Distribution. Q-001 bleibt offen; Q-002 ist als Produktanforderung
entschieden. ADR-001 bleibt Release-Gate, bis die konkrete Engine,
Quelldateien, Netzdateien, Lieferartefakte und Vertriebsform fachkundig
geprüft und vom Owner freigegeben sind.

[Rechtsprüfung und konkreter Engine-Lieferumfang: OFFEN]

## W02-Technikaufnahme (2026-11-20; nicht als Freigabe)

- Geprüfte Quellstände und Lizenzdateien sind in
  `docs/legal/LICENSE_STRATEGY.md` und `docs/research/SOURCES.md` datiert
  dokumentiert.
- Stockfish und `python-chess` führen die GPLv3; Stockfish dokumentiert NNUE
  Dateien als Teil seiner Distribution. Kein Kandidat wurde übernommen.
- Chessnut führt Unlicense und hat laut Upstream-README einfache FEN- und
  Zugvalidierungsfunktionen. Die gesichteten Tests reichen nicht als Nachweis
  vollständiger Remis-/Wiederholungsregeln oder als Freigabe für den
  Chess-&-Chains-Regelkern.
- Eine UCI-/Prozessgrenze ist eine Architekturinformation und entscheidet
  nicht, ob eine konkrete Gesamtverteilung eine kombinierte Arbeit darstellt.

**Status zum Zeitpunkt der W02-Aufnahme:** Optionen noch nicht ausgewählt;
keine Rechtsmeinung, Dependency oder Distribution wurde erzeugt. Die spätere
Owner-Richtung ist im Abschnitt „Owner-Entscheid“ festgehalten und bleibt
ebenfalls ohne Rechtsfreigabe.

## Begrenzte Owner-Entscheidung für W05 (2026-11-20)

Der Owner hat den Start eines **eigenständig implementierten Schachregel-Kerns
unter MPL-2.0** autorisiert. W05 verwendet daher keine externe Schachbibliothek
und übernimmt keinen fremden Regelcode. Das ist keine Rechtsberatung und keine
Freigabe für Stockfish, python-chess, andere GPL-Komponenten, Engine-Binaries,
NNUE-Dateien oder eine kombinierte Distribution.

Q-001 bleibt offen, weil die Auswahl zwischen A und B noch nicht abgeschlossen
ist. Q-002 ist als Produktanforderung entschieden; der Umsetzungsweg bleibt
offen. Der Regelkern wird separat bewertet; ADR-001 bleibt Release-Gate und
blockiert eine gebündelte GPL-Auslieferung.
