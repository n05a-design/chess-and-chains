# Copilot-Auftragskette

Die Prompts beschreiben Aufträge und Abnahmeziele. Für einen neuen Checkout zuerst `00_MASTER_BOOTSTRAP.md` als Inventur verwenden. Vor einer Fortsetzung den tatsächlichen [Status je Paket](../docs/roadmap/WORK_PACKAGES.md) und die [aktuelle Reihenfolge](../docs/roadmap/ROADMAP.md) prüfen. Das [Dokumentations- und Ablageaudit](../docs/reports/2026-11-21_W11-dokumentations-und-ablageaudit.md) beschreibt den aktuellen Stand, der [Standabgleich V.0.1.0](../docs/reports/2026-11-21_W11-v0.0.1-standsaudit.md) die Einführung der Version.

| Reihenfolge | Prompt | Ergebnis |
| --- | --- | --- |
| 00 | `00_MASTER_BOOTSTRAP.md` | Iststand und Arbeitsumgebung als Basis |
| 01 | `01_PRODUCT_SCOPE.md` | MVP, Blocker, Produktvertrag |
| 02 | `02_LICENSE_ENGINE_GATE.md` | Rechts-/Regelwerk-/Engine-Matrix |
| 03 | `03_GLIDE_SHELL_AUDIT.md` | unabhängiges Shell-Reuse-Gate |
| 04 | `04_COMPETITOR_DESIGN_RESEARCH.md` | UX-Vergleich, kreative Leitplanken |
| 05 | `05_CHESS_CORE.md` | korrekte Schachdomäne nach Lizenzentscheidung |
| 06 | `06_BOARD_UI.md` | SVG-Board-Vertical-Slice |
| 07 | `07_UCI_BOTS.md` | Offline-Bots nach Lizenzentscheidung |
| 08 | `08_PUZZLE_PIPELINE.md` | Lichess-CSV-Validierung + offline Katalog |
| 09 | `09_STORAGE_PROFILES.md` | Datenhaltung und Wiederherstellung |
| 10 | `10_I18N_ACCESSIBILITY.md` | DE/EN, Tastatur, visuelle Qualität |
| 11 | `11_QA_CI_AUDIT.md` | Nachweise und reale System-Checks |
| 12 | `12_RELEASE_HANDOFF.md` | unverbindlicher Veröffentlichungsplan oder genehmigter Release |

## Umsetzungsprinzip

Jeder Prompt: erst `AGENTS.md`, `MANIFEST.md`, relevante ADRs/Fragen lesen; keine implizite Owner-Freigabe; Branch + nachvollziehbare Arbeitsstücke; bei Ende tatsächlichen `git status`, Tests, Commit/Push getrennt dokumentieren. Zu Arbeitsstand/Handover: `docs/reports/`.
