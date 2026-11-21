# W00–W12 – Abgleich der Arbeitspakete

**V.0.0.1 · 21.11.2026 · Codex, KI-gestützt.**
Geprüfte Basis ist `main` bei `6bcd9ada580be10f289c34dd0040be62297597d2`
im Codex-Worktree. Der GitHub-Stand entspricht dem extern gemergten PR #9.
Der lokale Folgebranch `codex/chess-chains-native-qa` trägt die Code- und
Teständerungen `e975fc8d3c354c0c6a3ec4bb7dcc682fbab8ea09` und
`027c2163fb401ca95d925e9ab2c5d708f92a5eb6`.

## Status und tatsächliche Abnahmelücken

Alle 13 Paket-Gates wurden mit den zugehörigen Aufträgen, aktiven
Entscheidungen und geprüften Ergebnissen abgeglichen. Sieben Pakete waren
bereits für ihren jeweiligen Umfang als `TESTED` geführt. W10 erreicht
diesen Stand für den automatisiert geprüften Umfang von PR #9. Aktuell
sind **acht Pakete getestet**, **vier in Arbeit** und **eines blockiert**.
Eine vollständige Paketabnahme ist für **0 von 13** dokumentiert.
[Statusmodell](../governance/STATUS_MODEL.md) · [Maschinenmanifest](../../project-manifest.json)

| Paket | Nachweis | Bis zur vollständigen Abnahme offen |
| --- | --- | --- |
| W00 · Foundation | Struktur, Versionierung und Linkziele automatisiert geprüft. [W00-Bericht](2026-11-20_W00_bootstrap.md) | Inhaberabnahme der Übergabe. |
| W01 · MVP | Produktvertrag, Nicht-Ziele und offene Entscheidungen dokumentiert. [MVP-Vertrag](../product/MVP_CONTRACT.md) | ADR-000 und verbleibende MVP-Entscheidungen, etwa Spielzeitmodi. |
| W02 · Rechte | Rechte-/Engine-Matrix und Freigabegrenzen dokumentiert. Der Quellstand enthält eigenen Regelkern und Mock-UCI. [Lizenzstrategie](../legal/LICENSE_STRATEGY.md) | ADR-001 und konkretes Lieferinventar für echtes Offline-Bot-Spiel. |
| W03 · Glide Shell | Kandidaten, Herkunft, Lizenzen und Testplan erfasst. Heutiger SHA-Abgleich siehe unten. [W03-Bericht](2026-11-20_W03_glide-audit.md) | Q-006 und isolierte Schnittstellen-/Plattformtests vor einer Übernahme. |
| W04 · Design und Recherche | Wettbewerbsquellen, Varianten, Connected System, editierbare Master und Assetregister vorhanden. [Design und Varianten](../design/CONNECTED_SYSTEM.md) · [Register](../design/ASSET_REGISTER.csv) | Freigabe konkreter Markenexporte sowie offene Schriftrollen und Atlas-Details nach ADR-005. Launch-Materialien sind für später vorgesehen. |
| W05 · Regeln | Perft, legale Züge, Zustandswiederherstellung, Remisansprüche und PGN-Hauptvariante geprüft. [Regelkernbericht](2026-11-20_W05_chess-core.md) | Allgemeine tote Stellungen mit nachgewiesener Lücke unten. Die Behandlung von PGN-Kommentaren und Nebenvarianten ist als Scope-Grenze dokumentiert. |
| W06 · Brett und Figuren | V.02, freigegebene Draufsicht, PNG-Fallback und Vorschau mit Projekt-SVG in der App geprüft. [W06-Prüfbericht](2026-11-21_W10-W11-tastatur-und-skalierung.md) | Finale Inhaber-Brettmotive, motivbezogener Kontrast, native Sichtprüfung und Skalierung. |
| W07 · Bots | UCI-Handschlag, Timeouts und Fehlerbehandlung mit Mock-Prozess belegt. [W07-Bericht](2026-11-21_W07-uci-verbindungstest.md) | Reale Engine, echte Offline-Partie, Kalibrierung und native Abnahme nach ADR-001/007. |
| W08 · Rätsel | Importlogik, erster gegnerischer Zug und Rating-Untergrenze mit eigenen Daten getestet. [N02-Funktionsnachweise](2026-11-20_N02_functional-core.md) | Realimport nach Q-022, Rating-Obergrenze Q-008 und Packgröße Q-009. |
| W09 · Datenhaltung | SQLite-Migration und Wiederherstellung automatisiert geprüft. Windows-Systemdialoge für PGN mit einem Datei-Roundtrip belegt. | Native Dialog-/Plattformabnahme auf macOS und Linux, ADR-004 und Profilmodell Q-012. |
| W10 · Bedienqualität | DE/EN und Tastaturabläufe auf der PR-#9-Matrix geprüft. Windows-Sichtprobe bei 96 DPI und ergänzende Regression zur Fokusmeldung. | Native Skalierung bei 150/200 %, vollständige Sichtprüfung, Screenreader und CI des lokalen Folgestands. |
| W11 · QA | Push, Pull Request und Merge von PR #9 mit je 14 Jobs geprüft. Windows-Wheel und lokale Regressionsläufe belegt. | Native Offline-Installer, Upgrade und erneute Plattform-CI für Änderungen nach PR #9. |
| W12 · Distribution | Strategie und geplante Paketierung liegen vor. [Vertriebsstrategie](../release/RELEASE_STRATEGY.md) | ADR-001/005/006, abgenommene signierte Plattformpakete, Quellen-/Lizenzlieferung und separate Inhaberfreigabe. |

## GitHub und macOS

Der erste [Push-Job mit macOS und Python 3.14](https://github.com/n05a-design/chess-and-chains/actions/runs/44861119209/job/136714495083)
war im Unterverwandlungstest rot. Der Fehler trat beim zeitgesteuerten
synthetischen Enter im neuen Dialog auf. `6fc505e` wartet im Test auf
sichtbaren Button und bestätigten Tk-Fokus und stellt Enter in die
Ereigniswarteschlange. Der [Push](https://github.com/n05a-design/chess-and-chains/actions/runs/44861369434)
und der [PR-Lauf](https://github.com/n05a-design/chess-and-chains/actions/runs/44861373488)
bestanden danach je 14 von 14 Jobs. Den externen Merge belegt der
GitHub-PR-Status. Der [Lauf auf main](https://github.com/n05a-design/chess-and-chains/actions/runs/44869510471)
bestand ebenfalls 14 von 14 Jobs. Die Logs aller drei Läufe belegen je
53 native GUI-Tests mit CPython 3.11.9 und 3.14.10 auf macOS. GitHub-Leseabfragen
mit `gh run view` und `gh api …/actions/jobs/<ID>/logs` endeten mit Exitcode 0.

## Windows und lokale Korrekturen

- Windows 11 Pro x64, Python 3.15.1/Tk 9.0.4, V.0.0.1 aus `main`.
  Fenster 1020 × 740 px, Anzeige 2560 × 1440 px, effektives Fenster-DPI
  und Tk-DPI je 96. Die Windows-Eingabeprobe zeigte den Rahmen auf e2 und
  den Text zur Belegung nach Tab. Windows UI Automation meldete den
  Brettfokus als generische Fläche. Koordinate und Belegung waren im
  gelesenen Baum nicht als zugängliche Feldnamen erkennbar. Tatsächliche
  Screenreader-Ausgaben wurden nicht geprüft.
- W09. In einem temporären Testprofil startete `python -` ein Tk-Fenster
  mit den regulären Import-/Exportfunktionen. Die Aufrufhülle setzte
  temporäres Startverzeichnis und Dateiname für die echten
  `tkinter.filedialog`-Dialoge. Öffnen und Speichern wurden in den
  Windows-Dialogen ausgelöst. Einlesedatei `1. e4 e5 2. Nf3 *` mit
  Event-Tag. SQLite und erneut eingelesene Exportdatei lieferten
  `e2e4, e7e5, g1f3` und denselben Event-Tag. Backup und Restore in eine
  zweite Testdatenbank erhielten den Datensatz. Die Sicherung vor dem
  Restore enthielt die ursprünglich leere Datenbank. Exitcode 0.
- W10. Beim Verlassen des Bretts verschwand der Rahmen, während die
  alte Meldung sichtbar blieb. Die erweiterte Tk-Regression scheiterte
  zuvor an dieser Meldung (Exitcode 1). `e975fc8` löscht sie beim
  Fokuswechsel und erhält neuere App-Meldungen wie einen PGN-Import.
  Tab und Shift+Tab wurden im Gegenlauf geprüft.
- W00/W11. Ein synthetischer Manifest-Eintrag mit `ACCEPTED` und
  `blocked_by` blieb zuvor ohne Fehler. `027c216` prüft beide
  Felder für offene Gates. Die Regression prüft den Widerspruch ohne
  echte Abnahme im Manifest.
- `py -3.14 -m unittest tests.test_foundation tests.test_app_integration.StorageAndLocaleUiTests.test_board_shows_localized_focus_until_tab_moves_on -v`
  bestand mit Python 3.14.7, Tk 9.0.4 und verpflichtendem Display.
  14 Tests, Exitcode 0.
- Der erste Gesamtlauf las während der Dokumentationsarbeit bereits neue
  Manifest-Links, bevor die referenzierte Berichtsdatei existierte.
  192 Tests mit einem Fehler in der Strukturprüfung, Exitcode 1.
- Der abschließende `python -m unittest discover -s tests -q` prüfte
  Tree `577e49c8d60a62c48d7e1ca54181d8ccbf261d4e` vor Ergänzung dieses
  Ergebnisabsatzes. Windows 11 Pro x64, Python 3.15.1/Tk 9.0.4,
  `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`, `PYTHONWARNINGS=error::ResourceWarning`
  und `PYTHONFAULTHANDLER=1`. **192 Tests bestanden**, keine Skips,
  Exitcode 0. Foundation-/Versionsprüfung, relative Dokumentlinks,
  Policy, Kompilierung und der Vergleich der 13 Statuszeilen mit dem
  Manifest ergaben ebenfalls Exitcode 0.

## W03 und W05 – nachgeprüfte Grenzen

Die Leseabfrage `git ls-remote <Repo> HEAD` und die Git-Tree-Abfrage
bestätigten für Glide `0efa33ae751f626b9e2e92497808c867d51a49dc` und für
Steps `e73c6bdefafe691d1ba709e986d9e82947a3d643`, Exitcode 0. Gegenüber
dem W03-Inventar haben sich zwei der zehn aufgeführten aktiven Datei-Blobs
geändert. Glide-`appearance.py` delegiert an `glide_shell.system_appearance`.
`modal_session.py` führt weiterhin MPL-2.0 und nur Standardbibliothek/Tk als
direkte Laufzeitimporte. Das Konzept beschreibt die Glide-Fassade und führt
die separate Fensterverwaltung als Vorschlag. Die aktuelle Steps-Matrix
kennzeichnet sich als Entwurf und Prüfauftrag. Der Versionsvergleich
belegt die Quellenlage. Ein unabhängig abgenommener Übernahmevertrag
steht aus. [Glide-Konzept](https://github.com/n05a-design/glide-to-do/blob/0efa33ae751f626b9e2e92497808c867d51a49dc/01_Repository/Glide/docs/GLIDE_SHELL_FRAMEWORK_KONZEPT.md) · [Steps-Matrix](https://github.com/n05a-design/steps/blob/e73c6bdefafe691d1ba709e986d9e82947a3d643/docs/architecture/REUSE_AND_MIGRATION_MATRIX.md)

W05-Gegenprobe mit dem eigenen FEN
`8/8/8/8/8/8/r1k5/K7 w - - 0 1`. `ChessGame.outcome()` liefert
`ACTIVE`. Der einzige legale Zug ist `a1a2`, danach sind nur die Könige
übrig. Die Stellung ist damit bereits tot nach Art. 5.2.2. Der aktuell
eingelesene PGN mit `1. Kxa2 1/2-1/2` lässt sich laden und endet mit
`DRAW_INSUFFICIENT_MATERIAL`. Die Probe per Python auf `main` lief mit
Exitcode 0. Eine Korrektur muss den Zeitpunkt des automatischen Remis und
das Wiedereinlesen bisher gültiger lokaler Aufzeichnungen gemeinsam testen.
[FIDE Laws of Chess, Art. 5.2.2](https://handbook.fide.com/chapter/E012023)

## Reihenfolge für die Übergabe

1. Lokalen Folgebranch in die Plattform-CI bringen, sobald sein Push
   beauftragt ist. W10 mit nativer Skalierung und Screenreader prüfen.
2. W05-Befund als Regel- und Wiedereinlesetest aufgreifen. W09-Dateidialoge
   auf macOS und Linux mit temporären Daten prüfen.
3. W06-Inhaber-SVGs nach Eingang prüfen. Parallel die offenen Entscheidungen
   zu ADR-001, Q-006, Q-012 und Q-022 im Entscheidungsregister nachziehen.
4. Nach den Geräte-, Daten- und Lizenzabnahmen den W12-Installerpfad prüfen.

Der Folgebranch ist lokal. Die Quellstände der anderen Repositories wurden
lesend abgeglichen. Für einen Rollback lassen sich die beiden lokalen
Code-Commits unabhängig voneinander revertieren und die dokumentierten
Nachweise auf den unveränderten Merge-Stand von PR #9 zurückführen.
