# W11 – Abgleich von Projektablage, Code und GitHub

**V.0.0.1 · 21.11.2026 · KI-gestützt.** Der Integrationsbranch
`codex/chess-chains-ablageabgleich` startete am lokalen W09-Stand
`4e50c7b`. Grundlage des PR ist GitHub-`main` bei
`6bcd9ada580be10f289c34dd0040be62297597d2`. Die sieben lokalen Commits
auf dieser Basis enthalten W05, W09, den W10-Fokusfix und die
Überprüfung des Paketstatus. Die bisherige OneDrive-Historie bei
`f8c30052a7e7115c55ae67f3e02f0d05029e7621` ist Vorfahr von `main`.

## Bestandsaufnahme und Übernahme

Der Vergleich nutzte `git diff --name-only HEAD`, `git ls-files --others
--exclude-standard` und `git rev-list --objects origin/main HEAD`.
Dateiinhalte wurden über Git-Blob-Hashes verglichen. Beim Vergleich von
Text wurden zusätzlich die Zeilenenden berücksichtigt. Die sechs
gestagten Pfade des OneDrive-Index wurden separat mit den Arbeitsdateien
und der erreichbaren Git-Historie verglichen.

| Befund | Behandlung |
| --- | --- |
| 95 unterschiedliche geänderte oder unversionierte Projektpfade im OneDrive-Arbeitsverzeichnis | 69 Dateiinhalte sind in GitHub-`main` oder im bereits vorhandenen lokalen Entwicklungsbranch erreichbar. Dazu gehören die beiden SVG-Master für Originalfiguren und V.02 an ihren kanonischen Pfaden. |
| 26 zusätzliche Dateiinhalte | 19 Designquellen übernommen, sechs ältere Code-, Test- und Dokustände archiviert. Eine temporäre Affinity-Sperrdatei bleibt in der ursprünglichen Ablage. |
| Gestagte Versionen | Kein eigener Inhalt jenseits Arbeitsverzeichnis und erreichbarer Historie. Der OneDrive-Index bleibt als Ausgangspunkt erhalten. |
| Früherer Claude-Worktree in der OneDrive-Ablage | Seine Git-Verknüpfung verweist auf einen nicht erreichbaren Rechnerpfad. Der Inhaltsvergleich erfasste 168 Projektdateien. Alle 168 sind in der erreichbaren Historie enthalten. |
| Lokale Hilfsdateien | Buildordner, Python-Caches, Toolzustand und Sperrdatei bleiben in der lokalen Arbeitsablage. |

Im erneuten Vergleich gegen den konsolidierten Branch blieben nur die
Sperrdatei und die vollständigen Bytes des Berichts mit dem gekürzten
Rechnerpfad ohne identischen Git-Blob. Der Bericht selbst ist im Archiv
erhalten. Die 19 Designquellen umfassen 15.557.810 Byte.

Die GitHub-Veröffentlichung der Projektinhalte folgt dem aktuellen
Inhaberauftrag. Die Dateien der Designexploration wurden kopiert und
byteweise geprüft. Die aktiven OneDrive-Dateien und der Index blieben
erhalten. Die [Designquellen](../../design/brand_exploration/README.md)
enthalten editierbare SVG-/Affinity-Dateien, historische Rastervorschauen,
das Briefing und die Schrift mit OFL-Hinweis. Die [Archivliste](../archive/onedrive-2026-11-21/SOURCES.csv)
belegt die sechs Zwischenstände und eine Kürzung eines absoluten
Rechnerpfads im historischen Bericht.

Die Datei Manufacturing Consent in der ursprünglichen Ablage trägt
Version 3.000 und SHA-256
`dcc1b6804f77479e7e259d28574fabbdfac4b6cef95a443102cde5b663291b54`.
Die am Upstream-Commit `80c3d822` verifizierte Quelldatei der
App-Wortmarke trägt SHA-256
`5a965329cc99d7b8b22ddbdbf98ee3dfef111c68b5e7aba80128dbefb5427db3`.
Das [Assetregister](../design/ASSET_REGISTER.csv) führt sie eigenständig.
Die öffentliche Ablage der Entwürfe ist ein Projektnachweis. Die
Vertriebsfreigaben für die App folgen ADR-005 und ADR-006.

## Geschlossene Lücken

- Der Foundation-Check prüft die 66 Assetregister-Einträge auf
  doppelte IDs, vorhandene Repository-Pfade und eingetragene SHA-256-Werte.
  Die Git-Einstellungen erhalten die Dateibytes der Originale und legen
  für die SVG-Laufzeitdateien LF fest.
- Beim Start einer App mit beschädigter Bibliothek legte SQLite bereits
  eine neue Bibliothek an und behielt die alte Datei unter einem
  `.corrupt-…`-Namen. Die App zeigt nun den Sicherungsnamen an und
  erhält gleichzeitig die Meldung zu fehlerhaften Einstellungen. Die
  neue Regression zeigte vor der Korrektur, dass die Datenbankmeldung
  fehlte (Exitcode 1). Beide ursprünglichen Dateien wurden im
  temporären Testprofil erhalten.
- Dokumentationsindex, Marken-ADR, Datenvertrag und Drittquellenhinweise
  verweisen auf die übernommenen Quellen und den aktuellen Laufzeitstand.
  Für Einstiegsdokumente, Quellversion und Paketmetadaten gilt V.0.0.1.

## Prüfergebnisse

Geprüfter Commit nach Quellenübernahme ist `64063b13fea389da360aa1642a31ece72c84fa5e`,
Tree `b0414d4eb1ba845628588bbbd6f27ef3a4563532`. Der Startfix ist
`de193afdb7c23a9ad76282ad0b8e5d35dc0110c5`.

- `python -m unittest discover -s tests -q` unter Windows 11 Pro x64
  mit Python 3.15.1/Tk 9.0.4, `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`,
  `PYTHONWARNINGS=error::ResourceWarning` und `PYTHONFAULTHANDLER=1`.
  **204 Tests bestanden**, Exitcode 0 (103,868 Sekunden).
- Mit Python 3.14.7 bestanden
  `tests.test_app_integration.StorageAndLocaleUiTests.test_startup_reports_database_recovery_alongside_settings_warning`,
  `tests.test_storage` und `tests.test_i18n` in einem gezielten
  `py -3.14 -m unittest … -q`-Lauf. 36 Tests, Exitcode 0.
- `verify_starter.py`, `verify_document_links.py`, `check_policy.py`,
  `python -m compileall -q src app scripts tests` und
  `git diff --cached --check` endeten mit Exitcode 0.
  57 Asset- und sechs Archiv-Prüfsummen wurden gegen die Bytes im
  Git-Index geprüft. Der Index enthielt 126 Markdown-Dateien.
- `pip wheel --no-build-isolation --no-deps --no-index` auf einem
  temporären `git archive` des geprüften Trees erzeugte
  `chess_and_chains-0.0.1-py3-none-any.whl`. Die Inhaltsprüfung bestätigte
  24 Figuren-SVGs und die Ablagegrenze der Designquellen.
  `pip install --no-deps --no-index --target <Temp>` und
  `python -m chess_and_chains --version` bestanden. Der gemessene
  SHA-256 des Wheels war
  `9e61318881e8501a798da45051831cf3b3e6b43a14a1de5b49c35baa9668dcca`.

## Prüfgrenzen und Übergabe

Für weitere Paketarbeit gelten die [Roadmap](../roadmap/ROADMAP.md) und das
[Statusmodell](../governance/STATUS_MODEL.md). Die aktuellen Abnahmen
betreffen vor allem native Skalierung und Screenreader, finale Brett-SVGs,
die echte Offline-Engine und den produktiven Rätselimport. Diese Arbeiten
benötigen die dort benannten Nachweise und Entscheidungen.

Die Archivdateien und der Code-Fix lassen sich unabhängig zurückführen.
Für ein Release bleiben Plattform-Builds, Lizenznachweise und
Inhaberfreigabe eigene Schritte.
