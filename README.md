# Chess & Chains

**Play. Think. Connect.**

> **Project status: early implementation, not release-ready.** The repository contains an independent chess-rules domain and a W06 local two-player desktop prototype with explicitly temporary geometric test pieces. It has no engine, puzzle pack, or installer.

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
| Headless rules domain (legal moves, FEN/PGN, game history) | Implemented locally; W05 validation in progress |
| Desktop board and local two-player UI | W06 prototype implemented locally; not release-ready |
| Offline bot engine connection | Not implemented |
| Offline puzzle catalog | Not implemented |
| Windows/macOS/Linux installers | Not implemented |
| WinGet / Homebrew distribution | Not published |

## Technology direction (subject to decisions)

Python desktop project. An original MPL-2.0 headless rules domain is under W05 validation. Tkinter/Tk may be evaluated independently; Glide Shell remains gated. A graphical board, UCI engine interface, local puzzle storage and separate visual themes are planned. **Stockfish is GPLv3.** Bundling it with this app is gated by licensing review; the MPL-2.0 repository license alone does not license third-party components. See [License Strategy](docs/legal/LICENSE_STRATEGY.md).

## Quick start for contributors

Requires **Python 3.11+** with Tk support for the desktop prototype.

```sh
python -m unittest discover -s tests -v
python scripts/verify_starter.py
python -m chess_and_chains --headless-check
python -m chess_and_chains
```

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
