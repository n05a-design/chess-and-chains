# Chess & Chains

**Play. Think. Connect.**

> **Project status: early implementation, not release-ready.** The repository contains an independent chess-rules domain and a local Tk desktop prototype (two players, bot mode against a project-owned **mock** engine, demo Puzzle Lab) with explicitly temporary geometric test pieces. No real chess engine is bundled or tested, no Lichess puzzle data is shipped, and there is no installer.

**Chess & Chains** is a planned free, open-source, offline-first desktop chess experience featuring configurable local computer opponents, tactical puzzle training and a distinctive, customizable board designed around original SVG chess pieces.

**[Deutsch](README.de.md)** · [Roadmap](docs/roadmap/ROADMAP.md) · [Project Manifest](MANIFEST.md) · [Open Questions](docs/questions/OPEN_QUESTIONS.md) · [Contributing](CONTRIBUTING.md)

## Product direction

- **Play offline:** standard chess against locally controlled UCI engines; no required account or cloud service.
- **Choose your challenge:** selectable strength presets, with actual strength to be measured and calibrated.
- **Solve meaningful puzzles:** planned local tactical collections with a minimum **puzzle rating of 1000**, using legally sourced material.
- **Make the board your own:** original, modular SVG piece sets, boards and application themes.
- **Own your progress:** local game and puzzle history, optional PGN/FEN interoperability, privacy by design.
- **Work across desktops:** Windows and macOS are initial release targets; Linux is a subsequent acceptance target.

## Current implementation status

| Capability | Status |
| --- | --- |
| Product requirements, folder structure and initial documentation | Scaffolded / proposed |
| Headless rules domain (legal moves, FEN/SAN/PGN, draw rules, undo/redo) | Implemented and tested (perft + golden tests); owner acceptance open |
| Desktop board and local two-player UI | Prototype implemented; native check on macOS only; not release-ready |
| UCI process adapter | Implemented; tested only against a project-owned mock engine |
| Game controller + asynchronous bot (play as White or Black) | Implemented; tested with the mock engine, which is **not a chess AI** |
| Real engine (e.g. Stockfish) bot play | Not bundled, not tested; user-configured engine path supported but unverified (ADR-001 open) |
| Bot difficulty presets | Six data-driven presets; options only sent if the engine advertises them; strengths **not calibrated** |
| Draw claims | Claim threefold repetition or the 50-move rule in the current position or by declaring a legal move. |
| Puzzle Lab (importer, packs, solving) | Five project-authored demo puzzles. Filter by theme and rating and see progress for the selection. Import enforces Rating ≥ 1000. |
| Local storage (SQLite games, puzzle progress, settings) | Save and reopen games in two-player mode, including local resignation and draw-claim details. Import or export one UTF-8 PGN file per action in the local library. |
| English/German UI | Implemented catalogues with parity tests |
| Windows/macOS/Linux installers | Not implemented |
| WinGet / Homebrew distribution | Not published |

## Technology direction (subject to decisions)

Python desktop project with an original MPL-2.0 headless rules domain and a Tkinter/Tk desktop prototype (owner-selected W06 direction). Glide Shell remains gated. A UCI adapter, game controller, puzzle pipeline and SQLite storage exist; original SVG pieces and visual themes are pending owner assets. **Stockfish is GPLv3.** Bundling it with this app is gated by licensing review; the MPL-2.0 repository license alone does not license third-party components. See [License Strategy](docs/legal/LICENSE_STRATEGY.md).

## Quick start for contributors

Requires **Python 3.11+** with Tk support for the desktop prototype.

```sh
python -m unittest discover -s tests -v
python scripts/verify_starter.py
python -m chess_and_chains --headless-check
python -m chess_and_chains
```

To try a locally installed UCI engine during development (never downloaded by the app), set `CHESS_AND_CHAINS_ENGINE=/path/to/engine` or use *Engine settings…* in the app. Without it, bot mode uses the clearly labelled mock engine.

Install the package first with `python -m pip install -e .`, or set `PYTHONPATH=src` when running from a checkout. The default command opens the local Tk prototype; `--headless-check` reports its availability without opening a window. The chess domain has no runtime chess-library dependency.

## Licensing and third-party rights

Original starter source files are offered under [MPL-2.0](LICENSE). Engine binaries, libraries, fonts, artwork, puzzle data and third-party references may carry **separate terms**; nothing here grants rights to those materials. Official builds are intended to remain free of charge. Review [Third-Party Notices](THIRD_PARTY_NOTICES.md) and [Asset Register](docs/design/ASSET_REGISTER.csv) before redistribution. This repo is **not affiliated with Stockfish, Lichess or other chess services**.

## Project and development

- [Work orders and dependency gates](docs/roadmap/WORK_PACKAGES.md)
- [GitHub Copilot prompts](prompts/README.md)
- [Technical architecture](docs/architecture/ARCHITECTURE.md)
- [Competition research](docs/research/COMPETITOR_ANALYSIS.md)
- [Design and branding brief](docs/design/DESIGN_SYSTEM_BRIEF.md)
- [GitHub release strategy](docs/release/RELEASE_STRATEGY.md)

*The name and visual identity are working assets pending trademark and rights review.*
