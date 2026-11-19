# Agent Contract – Chess & Chains (Copilot, Codex, Claude, Gemini)

**Priority: safety, provenance, reproducible evidence, respect for owner decisions.** Read `START_HERE.md`, `MANIFEST.md`, `docs/questions/OPEN_QUESTIONS.md`, `docs/roadmap/WORK_PACKAGES.md` and relevant ADRs before editing.

1. **Inventory before edits.** Confirm repo path/remote, branch, HEAD SHA, git status, tests, file owners and license markers. Never assume a OneDrive folder or another clone is automatically synchronized.
2. **Preservation first.** No silent deletion, `git reset --hard`, `git clean -fd`, force push, rebases that rewrite shared history, moving archival material, secret dumps or giant binary commits.
3. **No automatic external writes.** Do not create GitHub repositories, push, merge, publish releases, alter other repositories or move files in OneDrive unless explicitly authorized in the current task.
4. **Status honesty.** Distinguish PROPOSED / DECIDED / IMPLEMENTED / TESTED / RELEASED / BLOCKED. Never claim a passed test without executing it and recording command, environment, exit code and commit.
5. **License gate.** Stockfish GPLv3; python-chess GPL; MPL-2.0 own source. Never add, vendor or bundle GPL code/binaries before the decision in `docs/legal/LICENSE_STRATEGY.md`. No unreviewed model weights or copyrighted puzzle screenshots.
6. **No premature framework.** `integrations/glide_shell/` is reserved. Glide Shell is not yet independently approved. Do not copy `app.pyw`, import Glide models or silently bring over vendor code.
7. **Chess correctness.** Only legal moves, full game-state undo, verified FEN/PGN and draw rules. Engine computations must not block the UI event loop.
8. **Puzzle integrity.** `Rating >= 1000` for published standard packs; official Lichess FEN is before the first opponent move; apply first UCI move before asking player to solve. Validate every imported line.
9. **Assets.** Use user's own original SVGs when supplied. Store editable originals separately, track provenance and license of every bundled asset, font and screenshot. Never scrape copyrighted competitor assets.
10. **Privacy.** Local-first. No analytics, telemetry, remote models, forced network access, auto-install or fetching engines without opt-in and owner decision.
11. **Scope.** Follow the work order's acceptance gate and dependencies; log attractive extras to backlog. Ask or mark OPEN when an Owner decision blocks work. Never invent approvals.
12. **PR discipline.** Small isolated changes, docs + tests in same PR, include tradeoffs and rollback. Do not merge without explicit user instruction.
13. **Agent handoff.** Update `docs/reports/`, decision/question status, tests evidence, file references and an ordered next-actions list so another AI tool can continue from the same committed state.
14. **AI transparency.** Disclose AI-assisted work in commit/PR documentation when relevant; maintain human review responsibility for legal claims, design originality and release readiness.

**Canonical handoff:** `docs/governance/AGENT_HANDOFF_TEMPLATE.md`; **first task:** `prompts/00_MASTER_BOOTSTRAP.md`.
