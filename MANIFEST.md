# MASTER MANIFEST – Chess & Chains

**V.0.0.1 · Stand 21.11.2026 · Entwicklungsprototyp.** Der Stand umfasst den lokalen Regelkern, Tk mit Figurensatz V.02, Mock-UCI mit lokalem Bereitschaftstest, Demo-Puzzle-Lab und SQLite-Bibliothek. [Work Packages](docs/roadmap/WORK_PACKAGES.md) und [Statusmodell](docs/governance/STATUS_MODEL.md) erklären Umfang und Abnahme. `foundation_baseline` im Maschinenmanifest bleibt der historische Planungsstand.

## Single Sources of Truth (SSOT)

| Gegenstand | Kanonische Datei |
| --- | --- |
| Produktvision, Zielgruppen, Scope | `docs/product/PRODUCT_BRIEF.md` |
| Scope und Abgrenzung MVP/Später | `docs/product/MVP_CONTRACT.md` |
| Architektur-/Schnittstellengrenzen | `docs/architecture/ARCHITECTURE.md` |
| Glide-Shell-Integration | `integrations/glide_shell/INTEGRATION_GATE.md` + `src/glide_shell/SHELL_MANIFEST.json` |
| Produkt-/Technik-/Lizenzentscheidungen | `docs/decisions/ADR_INDEX.md` + ADR-Dateien |
| Nicht entschiedene Fragen | `docs/questions/OPEN_QUESTIONS.md` |
| Aktive Aufträge und Abnahmen | `docs/roadmap/WORK_PACKAGES.md` |
| Roadmap, Releases | `docs/roadmap/ROADMAP.md` |
| Gestaltung und Herkunft | `docs/design/DESIGN_SYSTEM_BRIEF.md`, `docs/design/ASSET_REGISTER.csv` |
| Drittkomponenten, Lizenzfreigabe | `docs/legal/LICENSE_STRATEGY.md` + `THIRD_PARTY_NOTICES.md` |
| Markt-/Konkurrenzrecherche | `docs/research/COMPETITOR_ANALYSIS.md` |
| Quellen (mit Datum) | `docs/research/SOURCES.md` |
| Releases / Paketmanager | `docs/release/RELEASE_STRATEGY.md` |
| Branch-/PR-/Dokumentationspflege | `docs/governance/GOVERNANCE.md` |
| Projektversion und Änderungen | `src/chess_and_chains/__init__.py`, `CHANGELOG.md` |
| Arbeitsverträge für Agenten | `AGENTS.md` + `.github/copilot-instructions.md` |
| Maschinenlesbares Paketverzeichnis | `project-manifest.json` |
| Statusmodell und Nachweispflichten | `docs/governance/STATUS_MODEL.md` |

## Reifegrad und Definitionen

- **IDEA**: Anforderungsidee; darf ohne Owner-Freigabe nicht als Produktentscheidung gelten.
- **PROPOSED**: begründete Empfehlung; noch nicht beschlossene Ausgestaltung.
- **DECIDED**: Owner-Entscheidung mit datiertem ADR.
- **IMPLEMENTED**: Code auf überprüftem Commit vorhanden; Funktion noch nicht zwingend geprüft.
- **TESTED**: mit Kommandos, Umgebung, Exitcode und Befund nachgewiesen.
- **RELEASED**: herunterladbares, korrekt paketiertes und getestetes Artefakt, separat öffentlich freigegeben.
- **BLOCKED**: Sicherheits-, Lizenz- oder Qualitätsgate offen.

## Abhängigkeiten

`W00` (Repository/SSOT) → `W01` (Owner-Fragen und MVP) → `W02` (Rechte & Engine-Strategie) / `W03` (Shell-Audit) / `W04` (Konkurrenz & UX) → `W05` (Schachregeln) → `W06` (UI-Board) → `W07` (lokale UCI-Engine) → `W08` (Rätselimport) → `W09` (Lokalspeicher) → `W10` (i18n/Accessibility) → `W11` (CI/Sicherheit/QA) → `W12` (Release-Vorbereitung).

**Regel:** Die Freigabe für den eigenen MPL-2.0-Regelkern und die Entwicklung mit projekteigener Mock-Engine sind in der [Lizenzstrategie](docs/legal/LICENSE_STRATEGY.md) dokumentiert. Engine-Bündelung und Release warten auf ADR-001. Die [Nacharbeit zu N02](docs/reports/2026-11-20_N02-follow-up.md) dokumentiert die lokale Implementierung und die Baseline-CI getrennt.

Die [Roadmap](docs/roadmap/ROADMAP.md) führt die nächsten Aufgaben in ihrer aktuellen Reihenfolge. Die Datenformate behalten ihre eigenen Schemaversionen. [Versionspflege](docs/governance/GOVERNANCE.md#projektversion)

## Artefaktgrenzen

`design/source/` = editierbare Originaldateien, `assets/` = ausgewählte Laufzeitressourcen, `references/inspiration/` = nur Linklisten & Notizen, `marketing/` = eigene Marken-/PR-Unterlagen, `data/source/` = Rohdaten (externe Datensätze nicht versionieren; nur kleine projekteigene Demo-CSV), `integrations/glide_shell/` = dokumentierte, freigegebene Wiederverwendung. **Keine automatischen OneDrive-Kopien, keine fremden Repo-Kopien in diesem Repository.**

## Historische Foundation-Baseline (F0)

- Dokumentationsgrundlagen und Copilot-Prompts: **enthalten**.
- Minimales Python-Paket, Testbasis und GitHub-Prüfworkflow: **enthalten**, aber erst lokal/CI auf realen Systemen verifizieren.
- Vollständige App, Engines, Rätsel, Designassets, Installer: **nicht enthalten**.
- Das Vorhandensein eines Ordners oder einer Beispielkonfiguration bedeutet **keine fachliche Umsetzung**.
