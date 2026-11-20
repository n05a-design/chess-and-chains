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

## W05-Regeltests am 2026-11-20

| Quelle | Verwendung | Grenze |
| --- | --- | --- |
| [Chess Programming Wiki – Perft Results](https://www.chessprogramming.org/Perft_Results) | Referenz-FENs und Perft-Knotenstände für Initialstellung sowie Positionen 2–6; als unabhängige Move-Generation-Golden-Tests in `tests/test_chess_core.py` verwendet | Kein Lizenzbeleg und keine vollständige Schachregeln-/Remissemantik-Abnahme; nur die dokumentierten Tiefen wurden als Fixture übernommen |

Es wurden keine fremden Regelimplementierungen, Tests, Bibliotheken oder
Schachpartien kopiert. Die Referenzwerte werden nicht als Beleg für
Plattform-/GUI-/Engine- oder Release-Reife ausgegeben.

## W06-SVG-Rendererquellen am 2026-11-20

| Quelle | Geprüfter Stand | Verwendet für / Grenze |
| --- | --- | --- |
| [CairoSVG auf PyPI](https://pypi.org/project/CairoSVG/) und [Dokumentation](https://cairosvg.org/documentation/) | CairoSVG 2.9.1; PyPI-Metadaten nennen LGPL-3.0-or-later und Abhängigkeiten `cairocffi`, `cssselect2`, `defusedxml`, Pillow und `tinycss2` | SVG-zu-PNG-PoC und Prüfhinweis, dass Cairo-/FFI-Bibliotheken je Plattform installiert oder paketiert werden müssen. Keine Runtime-Freigabe. |
| [cairocffi auf PyPI](https://pypi.org/project/cairocffi/) und [Installationsdokumentation](https://doc.courtbouillon.org/cairocffi/stable/overview.html) | cairocffi 1.7.1, BSD; Dokumentation nennt dynamisches Laden von Cairo, `LD_LIBRARY_PATH` auf Linux und `CAIROCFFI_DLL_DIRECTORIES`/PATH auf Windows | Plattformpfad der nativen Cairo-Abhängigkeit; konkrete Bundle-/Launcher-Integration noch offen. |
| [PySide6-Essentials auf PyPI](https://pypi.org/project/PySide6-Essentials/) | PySide6-Essentials 6.12.0; PyPI nennt QtSvg/QtSvgWidgets und Lizenz-Auswahl LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | QtSvg-Prototyp und installierter Größenvergleich; keine Lizenz- oder Distributionfreigabe. |
| [Qt OSS-Lizenzpflichten](https://www.qt.io/development/open-source-lgpl-obligations) | abgerufen 2026-11-20 | Offizielle Herstellerhinweise zu LGPL-/GPL-Modulen, korrespondierenden Quellen, Nutzerhinweisen und Relinking/Installation; keine konkrete Rechtsprüfung für das Produkt. |
| [Qt 6 Drittkomponenten](https://doc.qt.io/qt-6/licenses-used-in-qt.html) | Qt-Dokumentation 6.12.0, abgerufen 2026-11-20 | Hinweis, dass tatsächlich ausgelieferte Module und enthaltene Drittkomponenten getrennt inventarisiert werden müssen. |
| [PyInstaller auf PyPI](https://pypi.org/project/pyinstaller/) und [Dokumentation](https://pyinstaller.org/en/stable/operating-mode.html) | PyInstaller 6.22.3; Dokumentation sagt, Builds seien an aktives OS/Python/Wortbreite gebunden und Systembibliotheken aus `/lib` bzw. `/usr/lib` würden nicht mitgebündelt; PyPI nennt GPLv2-or-later mit besonderer Ausnahme für erzeugte Programme | Temporärer macOS-Einordner-Smoke-Test; Build-Tool, nicht als Produkt-Runtime aufgenommen. Keine Release- oder Installerwahl. |

Der lokale Messaufbau, seine exakten Laufzeitdaten und Grenzen stehen in
`scripts/benchmark_svg_backends.py` und
`docs/reports/2026-11-20_W06_board-ui.md`. Verwendet wurde ausschließlich
eine neu geschriebene SVG-Geometrie-Fixture; keine Owner- oder Fremdassets.

## W02-GPL-Gesamtvertriebsrecherche am 2026-11-20

| Quelle | Geprüfter Stand | Verwendet für / Grenze |
| --- | --- | --- |
| [GNU GPLv3 Originaltext](https://www.gnu.org/licenses/gpl-3.0.txt) | Version 3, 29.06.2007; abgerufen 2026-11-20 | §§5–6: „work based on“, Aggregate und zulässige Wege für Corresponding Source; §5(d): UI-Rechtsnotizen. Keine Einordnung der konkreten Chess-&-Chains-Bündelung. |
| [Mozilla MPL 2.0 FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/) und [MPL/GPL-Kombinationsanleitung](https://www.mozilla.org/en-US/MPL/2.0/combining-mpl-and-gpl/) | FAQ zuletzt aktualisiert 2024-01-30; abgerufen 2026-11-20 | FAQ Q14 erläutert MPL §3.3 und die Bedingungen für eine zusätzliche GPL-Distribution; Anleitung behandelt Erhaltung der MPL-Dateihinweise. Lizenzgeber-Hinweise, keine fallbezogene Rechtsberatung. |
| [Stockfish 19 README](https://raw.githubusercontent.com/official-stockfish/Stockfish/sf_19/README.md), [Copying.txt](https://raw.githubusercontent.com/official-stockfish/Stockfish/sf_19/Copying.txt) und [Release](https://github.com/official-stockfish/Stockfish/releases/tag/sf_19) | Tag `sf_19`, Release-Commit `edb0d9db6731067ec50ce619ff372b463bc4dd5d`; abgerufen 2026-11-20 | README nennt GPLv3, `Copying.txt`, `AUTHORS`, `src`/Makefile und `.nnue`-Netz als Distributionsbestandteile und verlangt Lizenz plus Quellcode oder passenden Quellverweis. Sie nennt LCZero-Trainingsdaten unter ODbL. Keine Binary heruntergeladen; keine eigenständige Bewertung der Netz-/Datensatzrechte. |

Der Bericht `docs/reports/2026-11-20_W02_license.md` hält die Anwendung,
Prüffragen und noch fehlenden Rechtsentscheidungen fest. Die Quellen stützen
eine weitere Prüfung von Weg A, nicht dessen Annahme oder Auslieferung.
