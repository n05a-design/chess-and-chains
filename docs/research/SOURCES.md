# Research Sources & Provenance

**Erstaufnahme:** 2026-11-19. Links sind Hinweise auf die jeweiligen Primärquellen; vor Implementierung/Vertrieb Quelle erneut prüfen. Keine heruntergeladenen Fremd-Quellcodes oder Bilddateien enthalten.

| Themenfeld | Primärquelle | Wofür verwendet | Zu verifizieren |
| --- | --- | --- | --- |
| Stockfish Engine/Lizenz | https://github.com/official-stockfish/Stockfish | UCI/GPLv3 | aktuelle Release-Version und Lieferpflichten |
| Stockfish UCI | https://official-stockfish.github.io/docs/stockfish-wiki/UCI-%26-Commands.html | Protokoll/Level | tatsächliche unterstützte Optionen je Version |
| MPL 2.0 | https://www.mozilla.org/en-US/MPL/2.0/ | Originale Lizenz | Code-/Asset-Grenzen |
| MPL/GPL Kombination | https://www.mozilla.org/en-US/MPL/2.0/combining-mpl-and-gpl/ | Larger Work | konkretes Distributionsmodell |
| GPL FAQ | https://www.gnu.org/licenses/gpl-faq.en.html | GPL-Einordnung | Rechtsprüfung abhängig von Bundling |
| python-chess | https://github.com/niklasf/python-chess | Schachregel-Alternative / GPL | aktuelle Abhängigkeit und Lizenz |
| Chessnut | https://github.com/cgearhart/Chessnut | Unlicense-Regelwerk-Kandidat | Funktion, Maintenance, vollständige Regeln |
| Lichess Puzzle DB | https://database.lichess.org/#puzzles | CC0-Rätsel, Feldschema, FEN/Moves-Konvention | Änderungen/Update, Ratingdaten |
| Lucas Chess | https://lucaschess.pythonanywhere.com/index?lang=de | Vergleich Desktop/Training | aktuelle Version, Offline-Test |
| En Croissant | https://encroissant.org/ | Engine/UX-Vergleich | aktuelle Funktionen und Plattformen |
| ChessX | https://chessx.sourceforge.io/ | Datenbank-Vergleich | aktuelle Version |
| Scid vs PC | https://scidvspc.sourceforge.net/ | DB-/Analyse-Vergleich | aktuelle Version |
| PyChess | https://github.com/pychess/pychess | Client-Vergleich | Release, Lizenz |
| Lichess | https://lichess.org/ | Trainingsmarkt | Offline-Grenzen |
| Chess.com | https://www.chess.com/ | Mainstream-Bots und Puzzles | Preis, Features, Plattform |
| WinGet-Submission | https://learn.microsoft.com/en-us/windows/package-manager/package/repository | Veröffentlichungsweg | Policy bei Submission |
| WinGet-Manifest | https://learn.microsoft.com/en-us/windows/package-manager/package/manifest | Felder, Prüfsummen | aktuelle Schema-Version |
| Homebrew Tap | https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap | Eigener Cask-Tap | Trust-/Audit-Regeln |
| Apple Notarisierung | https://developer.apple.com/developer-id/ | macOS Release Gate | Programmmitgliedschaft/Signatur |
| Glide Shell | https://github.com/n05a-design/glide-to-do/blob/main/01_Repository/Glide/docs/GLIDE_SHELL_FRAMEWORK_KONZEPT.md | mögliche Shell | aktueller Commit / Reifegrad |
| Glide Systemregister | https://github.com/n05a-design/glide-to-do/blob/main/01_Repository/Glide/src/glide/README.md | Modul-Reuse | tatsächlicher Upstream-Stand |
| Steps Agentvertrag | https://github.com/n05a-design/steps/blob/main/AGENTS.md | Verfahren | nur Konventionen übernehmen |
| Steps Reuse-Matrix | https://github.com/n05a-design/steps/blob/main/docs/architecture/REUSE_AND_MIGRATION_MATRIX.md | Erfahrungen | historische Baseline, aktuelle prüfen |

## GitHub-Quellaufnahme am 19.11.2026 (nur für Handover, nicht als dauerhafte HEAD-Behauptung)

- Steps `main`: `3a5c5add70172318979cac6518a923372c5fd193`.
- Glide `main`: `a53e779026295d315983c421bfbc9f42124037f5`.
- **Zum Zeitpunkt jeder Weiterentwicklung HEAD/Status erneut erfassen.** Lokale Änderungen, OneDrive-Platzhalter oder ungemergte Branches wurden durch diese reine Remote-Recherche nicht überprüft.

## W02-Lizenzquellenaufnahme am 2026-11-20

Upstream-Metadaten und Lizenz-/README-Dateien wurden am Datum der Aufnahme
abgerufen; Branch-SHAs sind reproduzierbare Prüfreferenzen, keine
Versions-/Vertriebsfreigaben:

| Repository / geprüfte Dateien | Commit | Befund / Verwendung |
| --- | --- | --- |
| [official-stockfish/Stockfish](https://github.com/official-stockfish/Stockfish), `Copying.txt`, `README.md` | `5d03b6e578a5eedc822e4563bdbb89e762fc2a59` | GPLv3; README listet die NNUE-Datei als Distributionsbestandteil, beschreibt Source-/Lizenzpflichten und nennt ODbL für LCZero-Trainingsdaten |
| [niklasf/python-chess](https://github.com/niklasf/python-chess), `LICENSE.txt`, `README.rst` | `0c6bdaccfcb3b09cdbe94b0f81e948cb2a356015` | GPLv3; README-Funktionsliste für Regeln, Formate, Engines |
| [cgearhart/Chessnut](https://github.com/cgearhart/Chessnut), `UNLICENSE.txt`, `README.md`, `Chessnut/tests/` | `8af90b93f8a10437495c65733c25cde94b615bb7` | Unlicense; einfache Regel-/FEN-Unterstützung dokumentiert, aber keine unabhängige Vollständigkeitsprüfung; Upstream-Push-Zeit laut API 2024-11-28 |
| [Mozilla MPL 2.0 FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/) und [MPL/GPL-Kombinationshinweise](https://www.mozilla.org/en-US/MPL/2.0/combining-mpl-and-gpl/) | Seitenstand laut FAQ: 2024-01-30; abgerufen 2026-11-20 | Primärquellen zur Datei-Copyleft-Grenze und MPL §3.3 Larger-Work-Bedingungen; konkrete Anwendung bleibt Rechtsprüfung |
| [GNU GPL FAQ](https://www.gnu.org/licenses/gpl-faq.en.html) | abgerufen 2026-11-20 | Primärquelle der Lizenzautoren für Aggregation/Kombination; keine automatische Einordnung der geplanten App |

Direkte Lizenzquellen: [Stockfish Copying.txt](https://raw.githubusercontent.com/official-stockfish/Stockfish/5d03b6e578a5eedc822e4563bdbb89e762fc2a59/Copying.txt), [python-chess LICENSE.txt](https://raw.githubusercontent.com/niklasf/python-chess/0c6bdaccfcb3b09cdbe94b0f81e948cb2a356015/LICENSE.txt), [Chessnut UNLICENSE.txt](https://raw.githubusercontent.com/cgearhart/Chessnut/8af90b93f8a10437495c65733c25cde94b615bb7/UNLICENSE.txt).

## W03-Glide-Quellenaufnahme am 2026-11-20

Nur lesende GitHub-API-/Dateiprüfung; es wurde kein weiteres Repository geklont,
keine OneDrive-Datei gelesen und kein externer Quelltext in dieses Projekt
kopiert.

| Quelle | Geprüfter Commit | geprüfte Pfade / Aussage |
| --- | --- | --- |
| [n05a-design/glide-to-do](https://github.com/n05a-design/glide-to-do) | `a53e779026295d315983c421bfbc9f42124037f5` | `01_Repository/Glide/docs/GLIDE_SHELL_FRAMEWORK_KONZEPT.md`, `01_Repository/Glide/src/glide/README.md`, `01_Repository/Glide/src/glide/app.pyw`; Konzept datiert 17.11.2026, Systemregister V1.54 datiert 19.11.2026. Das Konzept sagt ausdrücklich, dass ein eigenständiges Shell-Paket und die Schnittstellen noch nicht abgenommen sind. |
| [n05a-design/steps](https://github.com/n05a-design/steps) | `5c66183bc9833d2fa6cbdeb1be54ebc307ed6f3d` | `docs/architecture/REUSE_AND_MIGRATION_MATRIX.md`, `AGENTS.md`; die Matrix enthält einen Aktualitätshinweis, dass ihr großer Basisteil historische Stände beschreibt. Sie wird daher nicht als aktuelle Komponentengenehmigung benutzt. |

Die älteren Snapshot-SHAs in `project-manifest.json` und die
Quellenaufnahme vom 19.11.2026 bleiben als historische Referenzen erhalten.
Der aktuelle W03-Vergleich und seine Grenzen stehen in
`docs/reports/2026-11-20_W03_glide-audit.md`.

## W04-Wettbewerbs- und Designquellenaufnahme am 2026-11-20

Produktmerkmale wurden nur anhand der gelesenen offiziellen Produktseiten oder
Repository-Metadaten dokumentiert. Keine Apps installiert, Offline-Eigenschaft
nicht praktisch getestet und keine Bilder/Logos/Quelltexte übernommen.

| Quelle | Geprüfter Stand | Verwendet für / Grenze |
| --- | --- | --- |
| [Lucas Chess](https://lucaschess.pythonanywhere.com/index?lang=en) | Offizielle Produktseite, abgerufen 2026-11-20 | Seite nennt u. a. 57 Engines und Trainingsmodi. Plattform-/Offline-Aussagen nicht praktisch verifiziert. |
| [En Croissant](https://encroissant.org/) / [GitHub](https://github.com/franciscoBSalgueiro/en-croissant) | `master` `c8473936129bb6f1a919882e45527daa4d3a1e34`, Commit vom 2026-11-10; GitHub-API-Metadaten melden `GPL-3.0`, letzter Push 2026-11-10 | Website-Aussagen zu Cross-Platform, Analyse, Datenbank und Download-Manager; keine Offline-Abnahme. |
| [ChessX](https://chessx.sourceforge.io/) | Offizielle Produktseite, abgerufen 2026-11-20 | Windows/macOS/Linux, PGN-Datenbanken, Engines wie auf der Seite beworben; aktuelle Release-/Offline-Prüfung offen. |
| [Scid vs. PC](https://scidvspc.sourceforge.net/) | Offizielle Produktseite, abgerufen 2026-11-20 | Seitenstand führt Version 4.27 sowie Plattform-/Datenbank-/Engine-Informationen; Aktualität der Plattformangaben nicht geprüft. |
| [PyChess](https://github.com/pychess/pychess) | `master` `0dcc199970f24c75c2f113db5f59c7705c836670`, Commit vom 2026-11-19; GitHub-API-Metadaten melden `GPL-3.0`, letzter Push 2026-11-19 | Repo-Beschreibung nennt Desktopclient für Linux/Windows/macOS; keine Offline-/Featureabnahme. |
| [Lichess](https://lichess.org/) und [Puzzle Database](https://database.lichess.org/#puzzles) | Website abgerufen 2026-11-20; Datenbankseite nennt Update 2026-11-11 | Online-Produktkontext; Puzzle-CSV unter CC0, 6,193,530 rated puzzles auf der Seite, dokumentiertes Schema/FEN-Konvention. Nicht heruntergeladen. |
| [Chess.com](https://www.chess.com/) | Offizielle Startseite, abgerufen 2026-11-20 | Community, Bots, Rätsel und mobile Apps wie beworben; keine Offline- oder Produktgrenzenprüfung. |

Repository-Metadaten wurden nur als Quellenhinweis aufgenommen, nicht als
Freigabe einer Lizenz-/Codeübernahme. Detaillierte Beobachtungen,
Nicht-Verifikationen und Designhypothesen sind in
`docs/reports/2026-11-20_W04_competitor-design.md` festgehalten.
