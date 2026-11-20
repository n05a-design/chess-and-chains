# MASTER MANIFEST – Chess & Chains

**Stand:** 2026-11-20 (N02) · **Version:** Foundation F0 + N02 Functional Core · **Status:** PROTOTYPE_LOCAL_PLAY_NOT_RELEASED. Nicht als Produktrelease verstehen. Arbeitspaket-Status siehe `project-manifest.json` und `docs/governance/STATUS_MODEL.md`; F0-Planungsstand bleibt dort als `foundation_baseline` erhalten.

## Single Sources of Truth (SSOT)

| Gegenstand | Kanonische Datei |
| --- | --- |
| Produktvision, Zielgruppen, Scope | `docs/product/PRODUCT_BRIEF.md` |
| Scope und Abgrenzung MVP/Später | `docs/product/MVP_CONTRACT.md` |
| Architektur-/Schnittstellengrenzen | `docs/architecture/ARCHITECTURE.md` |
| Glide-Shell-Integration | `integrations/glide_shell/INTEGRATION_GATE.md` |
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

## Reihenfolge

`W00` (Repository/SSOT) → `W01` (Owner-Fragen und MVP) → `W02` (Rechte & Engine-Strategie) / `W03` (Shell-Audit) / `W04` (Konkurrenz & UX) → `W05` (Schachregeln) → `W06` (UI-Board) → `W07` (lokale UCI-Engine) → `W08` (Rätselimport) → `W09` (Lokalspeicher) → `W10` (i18n/Accessibility) → `W11` (CI/Sicherheit/QA) → `W12` (Release-Vorbereitung).

**Regel:** Parallelität nur wenn Abhängigkeiten und Berechtigungen geklärt sind. Für W05-W07 muss die Regeln-/Engine-Lizenzentscheidung abgeschlossen sein. Publikumsrelease ist bis zum Rechte-Gate blockiert.

## Artefaktgrenzen

`design/source/` = editierbare Originaldateien, `assets/` = ausgewählte Laufzeitressourcen, `references/inspiration/` = nur Linklisten & Notizen, `marketing/` = eigene Marken-/PR-Unterlagen, `data/source/` = Rohdaten (externe Datensätze nicht versionieren; nur kleine projekteigene Demo-CSV), `integrations/glide_shell/` = dokumentierte, freigegebene Wiederverwendung. **Keine automatischen OneDrive-Kopien, keine fremden Repo-Kopien in diesem Repository.**

## Starter-Zustand (dieses ZIP)

- Dokumentationsgrundlagen und Copilot-Prompts: **enthalten**.
- Minimales Python-Paket, Testbasis und GitHub-Prüfworkflow: **enthalten**, aber erst lokal/CI auf realen Systemen verifizieren.
- Vollständige App, Engines, Rätsel, Designassets, Installer: **nicht enthalten**.
- Das Vorhandensein eines Ordners oder einer Beispielkonfiguration bedeutet **keine fachliche Umsetzung**.
