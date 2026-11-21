# Governance, SSOT und Dokumentationspflege

Status: **PROPOSED**. Aus den bewährten Prinzipien von Steps/Glide abgeleitet, aber nicht als kopierte Implementierung.

## Repo-Regeln

- `main` ist der freigegebene Integrationsstand; PRs statt Direktänderungen. Keine Force-Pushes, Historienrewrites, automatischen Löschungen oder Merge ohne Auftrag.
- Agenten inventarisieren vor Änderung `git status`, `git branch`, `git log -1`, Repository-URL, Quelle und offenen PR-/Branch-Stand.
- Wichtige Änderungen über Issues/Arbeitspakete/ADRs; jeder PR enthält Scope, betroffene SSOT-Dateien, Tests, Risiken, Rollback und Quellen-/Lizenznachweise.
- Dokumentation und Code sind unabhängig zu prüfen. `README` als Beschreibung eines Features genügt nicht als Testnachweis.
- Eigenständige `docs/reports/YYYY-MM-DD_Wxx_<kurz>.md` als Arbeitsnachweis; historische Berichte nie still überschreiben.
- Neue offene Fragen in `docs/questions/OPEN_QUESTIONS.md` mit Owner, Gate, Entscheidungstermin.
- Public-Dokumente bevorzugt Englisch; interne operative Dokumente Deutsch; `README.md`/`README.de.md` müssen in Funktionsstatus und Lizenzlage übereinstimmen.

## Pflege-Matrix

| Änderung | Verbindlich synchronisieren |
| --- | --- |
| Neues User-Feature | Produktvertrag, Work Packages, Tests, README-Status |
| Neue Dependency/Engine | Legal, Third-Party Notices, Architektur, SBOM-Plan, Tests |
| Neue Figur/Board/Font | Asset Register, Designsystem, Lizenz, Packager |
| Storage-/Formatänderung | Domain-/Storage-Vertrag, Migration, Backup-Tests |
| Shell-Portierung | Integration Gate, Source-Commit, Hash, Lizenz, Contract-Tests |
| Veröffentlichung | Release-Strategie, Changelog, Artefakt-Hashes, Plattformnachweise |
| Konkurrenz-Aktualisierung | Research, Source-URL, Beobachtungsdatum, Differenzierung |

## Projektversion

Die erste konsolidierte Entwicklungsfassung heißt **V.0.0.1**. Python und
Paketmetadaten führen sie numerisch als `0.0.1`. Das Feld `__version__` in
[`src/chess_and_chains/__init__.py`](../../src/chess_and_chains/__init__.py) ist
die Quelle für Wheel-Metadaten, `--version` und Fenstertitel. Das Maschinenmanifest
und die zentralen Einstiegsdokumente geben diesen Stand wieder.

- Bei einer neuen konsolidierten Entwicklungsfassung Quellversion, Maschinenmanifest und die aktuellen Übersichten im selben PR aktualisieren. `VERSIONED_DOCS` in `scripts/verify_starter.py` enthält die in CI geprüften Dokumente. Die Prüfung zeigt konkrete Abweichungen an.
- Datierte Berichte, alte Designs und frühere Planung behalten ihre Versions- und Commitreferenzen. Der [Dokumentationsindex](DOC_INDEX.md) führt zum aktuellen Stand. Eine Entwicklungsnummer ersetzt den Commitnachweis nicht.
- Datenbankschema, Settings-, Puzzle-Pack- und Projektmanifest-Schema haben eigene Nummern. Figurensatz V.02 ist eine Asset-Revision. Diese Nummern werden nur geändert, wenn sich das jeweilige Format oder Asset ändert. [Datenvertrag](../architecture/DATA_CONTRACTS.md)
- Ein Git-Tag und ein öffentlicher Release folgen der separat genehmigten [Vertriebsstrategie](../release/RELEASE_STRATEGY.md).

## Definition of Done

Quell-Commit festgehalten; Testbefehl/Exitstatus/Umgebung belegt; keine unerwarteten Dateilöschungen; neue Dateien lizenziert; Dokumentationsindizes geprüft; lokale Änderungen gepusht und Remote-Head explizit geprüft **nur wenn Benutzer den Push beauftragt**; keine Release-Freigabe impliziert.
