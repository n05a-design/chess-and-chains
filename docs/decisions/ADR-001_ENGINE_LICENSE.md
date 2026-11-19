# ADR-001 – Engine- und Lizenzarchitektur

**Status: OPEN – BLOCKIERT gebündelte Stockfish-Auslieferung und GPL-Schachbibliotheken.**

## Ausgangslage

Eigener Code soll möglichst MPL-2.0 bleiben. Stockfish ist GPLv3; `python-chess` ist GPLv3. Kommunikation per UCI und separate Prozesse sind **keine automatische Freistellung** von möglichen Pflichten bei einer eng verbundenen gemeinsamen Distribution.

## Zu entscheidende Wege

- **A (einfacherer Integrationsrahmen):** GPLv3-konforme kombinierte Anwendung/Distribution; eigene Quelldateien ggf. weiterhin mit ihren ursprünglichen MPL-Hinweisen, kompatible Gesamtvertriebsbedingungen und sämtliche Drittpflichten erfüllen.
- **B (MPL-Ziel):** ausschließlich eigene/MPL-kompatible App plus z. B. Unlicense-Regelwerk; Engines als eigenständige, austauschbare UCI-Programme. Getrennte Installation oder ggf. getrennte Bundles; rechtlich prüfen, ob konkrete Veröffentlichungsart eine kombinierte Arbeit ist.
- **C (Zwischenlösung):** Open-Source-UCI-Host ohne vorinstallierten Engine-Binary; Benutzer bringt lokal bereits installierte Engine mit. Für „sofort offline spielbar nach Installation“ reicht das allein NICHT.

## Empfehlung / Sperre

Technik **engine-agnostisch** planen; kein Stockfish-Binary im Repo/Installer, kein `python-chess` als Abhängigkeit, bis der Owner und ggf. fachkundige Lizenzprüfung Weg A/B/C freigeben. Licensing checklist vor jeder Release: genaue Dateien, Prozesse, Patches, separierbare Distribution, Lizenztexte, komplette korrespondierende Quellen, Notices, Installer/UI-Verweise.

## Quellen

https://github.com/official-stockfish/Stockfish · https://www.mozilla.org/en-US/MPL/2.0/FAQ/ · https://www.mozilla.org/en-US/MPL/2.0/combining-mpl-and-gpl/ · https://www.gnu.org/licenses/gpl-faq.en.html

## Owner-Entscheid

[OFFEN: A / B / C; Datum; Freigebender; konkreter Lieferumfang; Rechtsprüfung]

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

**Status bleibt OPEN.** Keine Rechtsmeinung, Owner-Freigabe, Dependency oder
Distribution wurde hierdurch erzeugt.
