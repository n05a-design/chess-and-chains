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

## Prüfgrenzen und Übergabe

Für weitere Paketarbeit gelten die [Roadmap](../roadmap/ROADMAP.md) und das
[Statusmodell](../governance/STATUS_MODEL.md). Die aktuellen Abnahmen
betreffen vor allem native Skalierung und Screenreader, finale Brett-SVGs,
die echte Offline-Engine und den produktiven Rätselimport. Diese Arbeiten
benötigen die dort benannten Nachweise und Entscheidungen.

Die Archivdateien und der Code-Fix lassen sich unabhängig zurückführen.
Für ein Release bleiben Plattform-Builds, Lizenznachweise und
Inhaberfreigabe eigene Schritte.
