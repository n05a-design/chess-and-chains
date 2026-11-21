# Chess & Chains – Einstieg

**V.0.0.1 · Stand 21.11.2026 · Entwicklungsprototyp, nicht veröffentlicht.**
Das Repository `n05a-design/chess-and-chains` besteht seit dem 20.11.2026.
Gearbeitet wird über Branches und Pull Requests gegen `main`.

## In fünf Minuten startklar

```bash
python -m pip install -e .
python -m chess_and_chains --version
python -m chess_and_chains
```

Voraussetzung ist Python 3.11 oder neuer mit Tk. Ohne Installation genügt
`PYTHONPATH=src`. Die vollständigen Prüfungen:

```bash
python -m unittest discover -s tests
python scripts/verify_starter.py
python scripts/verify_document_links.py
python scripts/check_policy.py
```

## Lesepfad

| Wer | Zuerst lesen | Danach |
| --- | --- | --- |
| Inhaber | [Roadmap](docs/roadmap/ROADMAP.md) mit den nächsten Entscheidungen | [Offene Fragen](docs/questions/OPEN_QUESTIONS.md), [ADR-Index](docs/decisions/ADR_INDEX.md) |
| Entwicklung | [README](README.de.md), [Architektur](docs/architecture/ARCHITECTURE.md) | [Datenverträge](docs/architecture/DATA_CONTRACTS.md), [Testplan](docs/qa/TEST_PLAN.md) |
| KI-Agenten | [AGENTS.md](AGENTS.md), [Mastermanifest](MANIFEST.md) | [Work Packages](docs/roadmap/WORK_PACKAGES.md), [Statusmodell](docs/governance/STATUS_MODEL.md), [Übergabevorlage](docs/governance/AGENT_HANDOFF_TEMPLATE.md) |
| Design | [Designsystem](docs/design/DESIGN_SYSTEM_BRIEF.md) | [Assetregister](docs/design/ASSET_REGISTER.csv), [Brett-Lieferformate](assets/boards/source/README.md) |

Alle Dokumente mit Zuständigkeit stehen im [Dokumentationsindex](docs/governance/DOC_INDEX.md).
Prüfnachweise liegen unter [docs/reports](docs/reports/README.md).

## Arbeitsablauf

1. Vor jeder Änderung `git fetch origin` ausführen und von aktuellem
   `origin/main` abzweigen. Lokale Branches und der OneDrive-Ordner
   gleichen sich **nicht** automatisch mit GitHub ab.
2. Arbeitspaket (W00–W12) und Gate in den [Work Packages](docs/roadmap/WORK_PACKAGES.md)
   nachschlagen. Owner-Entscheidungen nie selbst setzen.
3. Code, Tests und Dokumentation im selben PR ändern. Die
   [Pflege-Matrix](docs/governance/GOVERNANCE.md#pflege-matrix) sagt, welche
   Dateien mitzuziehen sind.
4. Nachweis unter `docs/reports/JJJJ-MM-TT_Wxx-kurz.md` ablegen und im
   [Berichtsindex](docs/reports/README.md) verlinken.
5. Push und PR nur mit Auftrag im Chat, Merge nur auf ausdrückliche
   Anweisung des Inhabers ([Q-019](docs/questions/OPEN_QUESTIONS.md)).

## Statuskennzeichnung

`PROPOSED` = Arbeitsrichtung, `DECIDED`/`ACCEPTED` = nur durch den Inhaber,
`IMPLEMENTED` = Code vorhanden, `TESTED` = mit Befehl, Umgebung und Exitcode
belegt, `BLOCKED` = wartet auf eine Entscheidung. Einzelheiten im
[Statusmodell](docs/governance/STATUS_MODEL.md).

## Lokale Ablage in OneDrive

Git-Repositories in OneDrive erzeugen Konfliktkopien mit Gerätenamen und
verändern Dateirechte. Vor dem Commit deshalb `git status` prüfen und reine
Moduswechsel nicht übernehmen (`git -c core.fileMode=false status`).
Befunde und Empfehlungen: [Dokumentations- und Ablageaudit](docs/reports/2026-11-21_W11-dokumentations-und-ablageaudit.md).

Die ursprüngliche ZIP-Anleitung zur Neuanlage (F0) ist
[archiviert](docs/archive/f0-2026-11-19/START_HERE_F0.md).
