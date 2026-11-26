# Agent Contract – Chess & Chains (Copilot, Codex, Claude, Gemini)

**Priority: safety, provenance, reproducible evidence, respect for owner decisions.** Read `START_HERE.md`, `MANIFEST.md`, `docs/questions/OPEN_QUESTIONS.md`, `docs/roadmap/WORK_PACKAGES.md` and relevant ADRs before editing.

1. **Inventory before edits.** Confirm repo path/remote, branch, HEAD SHA, git status, tests, file owners and license markers. Never assume a OneDrive folder or another clone is automatically synchronized.
2. **Preservation first.** No silent deletion, `git reset --hard`, `git clean -fd`, force push, rebases that rewrite shared history, moving archival material, secret dumps or giant binary commits.
3. **No automatic external writes.** Do not create GitHub repositories, push, merge, publish releases, alter other repositories or move files in OneDrive unless explicitly authorized in the current task.
4. **Status honesty.** Distinguish PROPOSED / DECIDED / IMPLEMENTED / TESTED / RELEASED / BLOCKED. Never claim a passed test without executing it and recording command, environment, exit code and commit.
5. **License gate.** Stockfish GPLv3; python-chess GPL; MPL-2.0 own source and Glide Shell 0.6.2. Never add, vendor or bundle GPL code/binaries before the decision in `docs/legal/LICENSE_STRATEGY.md`. No unreviewed model weights or copyrighted puzzle screenshots.
6. **Glide Shell 0.6.2 foundation (`src/glide_shell/`).** Owner-approved integration from `n05a-design/glide-to-do` tag `v1.0.2` (Commit `7dcd8dc04366f88943fa17827882cef4d81421b8`, `SHELL_VERSION = 0.6.2`, `ADR-002` / `Q-006`). Never modify files inside `src/glide_shell/` manually — updates happen strictly via `shell_uebernehmen.py`. Never import Glide application/to-do models, and keep `chess_and_chains.chess` / `game` / `engines` / `puzzles` completely free of `tkinter` and `glide_shell` imports.
7. **Chess correctness.** Only legal moves, full game-state undo, verified FEN/PGN and draw rules. Engine computations must not block the UI event loop. `GameController` remains the single authoritative undo/redo source for chess moves.
8. **Puzzle integrity.** `Rating >= 1000` for published standard packs; official Lichess FEN is before the first opponent move; apply first UCI move before asking player to solve. Validate every imported line.
9. **Assets.** Logos: the three owner masters in `design/01_Logo/svg/` are binding (01 in-app signet tinted by theme, 02 full-colour About emblem, 03 app icon and public identity). Derive everything with `scripts/build_brand_assets.py` and follow [`design/01_Logo/README.md`](design/01_Logo/README.md); never hand-edit derived icons or revive the old orthogonal signet. Use the owner's original SVGs when supplied. Prefer editable SVG or other vector masters wherever the format permits. Keep masters when a runtime raster fallback is needed. Store editable originals separately and track provenance and license of every bundled asset, font and screenshot. Never scrape copyrighted competitor assets.
10. **Privacy.** Local-first. No analytics, telemetry, remote models, forced network access, auto-install or fetching engines without opt-in and owner decision.
11. **Scope.** Follow the work order's acceptance gate and dependencies; log attractive extras to backlog. Ask or mark OPEN when an Owner decision blocks work. Never invent approvals.
12. **PR discipline.** Small isolated changes, docs + tests in same PR, include tradeoffs and rollback. Do not merge without explicit user instruction.
13. **Agent handoff.** Update `docs/reports/`, decision/question status, tests evidence, file references and an ordered next-actions list so another AI tool can continue from the same committed state.
14. **AI transparency.** Disclose AI-assisted work in commit/PR documentation when relevant; maintain human review responsibility for legal claims, design originality and release readiness.

## Glide Shell 0.6.2 Integration & Agent Skills

This project uses the neutral **Glide Shell** (`src/glide_shell/`) as its Tk desktop foundation (`SHELL_VERSION = 0.6.2`, pinned to `v1.0.2` commit `7dcd8dc04366f88943fa17827882cef4d81421b8`).

- **KI-Anleitung für neue Projekte:** [`src/glide_shell/KI_ANLEITUNG_NEUE_PROJEKTE.md`](src/glide_shell/KI_ANLEITUNG_NEUE_PROJEKTE.md) (English: [`src/glide_shell/AI_GUIDE_NEW_PROJECTS.md`](src/glide_shell/AI_GUIDE_NEW_PROJECTS.md))
- **Startprompt für KI-Sitzungen:** [`src/glide_shell/STARTPROMPT_KI.md`](src/glide_shell/STARTPROMPT_KI.md)
- **Portabler Designvertrag:** [`src/glide_shell/DESIGN_RICHTLINIEN.md`](src/glide_shell/DESIGN_RICHTLINIEN.md) & [`docs/design/GLIDE_DESIGN_CONTRACT.md`](docs/design/GLIDE_DESIGN_CONTRACT.md)
- **Shell-Manifest:** [`src/glide_shell/SHELL_MANIFEST.json`](src/glide_shell/SHELL_MANIFEST.json)
- **Selbsttest:** `cd src && python3 -m glide_shell.selftest` (must report 13/13 checks passed)
- **Skills:** `.agents/skills/glide-shell/`, `.agents/skills/chess-design-system/`, `.agents/skills/chess-ui-engineering/`, `.agents/skills/chess-quality/`

**Canonical handoff:** `docs/governance/AGENT_HANDOFF_TEMPLATE.md`; **first task:** `prompts/00_MASTER_BOOTSTRAP.md`.
