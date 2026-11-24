# Copilot instructions

Read `START_HERE.md`, `MANIFEST.md`, `AGENTS.md`, `docs/questions/OPEN_QUESTIONS.md`,
`docs/roadmap/WORK_PACKAGES.md`, and the relevant ADRs before changing the project.

Chess & Chains is a development prototype (V.0.0.1): local two-player play,
a mock UCI engine, a demo Puzzle Lab and a SQLite game library. It is not
released and has no real engine. Fetch `origin/main` before starting, because
local branches and the OneDrive folder are not synchronized automatically, and
do not commit file-mode-only changes caused by OneDrive. Preserve the documented work-package order, acceptance gates, and
open owner decisions. Do not mark proposals as accepted or tests as passed
without evidence.

Keep the app independent, Python-based, and offline-first. Do not add Stockfish,
`python-chess`, or other GPL runtime components before the applicable review and
owner approval. Chess & Chains uses the owner-approved neutral **Glide Shell 0.6.2**
(`src/glide_shell/`, pinned to `v1.0.2` commit `7dcd8dc04366f88943fa17827882cef4d81421b8`);
never edit `src/glide_shell/` manually and never import Glide product/to-do models.
Do not add unlicensed assets, access or modify other checkouts, push, or merge without
explicit authorization.

For changes, update the canonical documentation and tests in the same work
package. Run the relevant Foundation checks and record exact commands, runtime,
exit codes, and remaining gaps in a dated report under `docs/reports/`.
