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

## Definition of Done

Quell-Commit festgehalten; Testbefehl/Exitstatus/Umgebung belegt; keine unerwarteten Dateilöschungen; neue Dateien lizenziert; Dokumentationsindizes geprüft; lokale Änderungen gepusht und Remote-Head explizit geprüft **nur wenn Benutzer den Push beauftragt**; keine Release-Freigabe impliziert.
