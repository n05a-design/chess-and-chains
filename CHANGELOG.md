# Changelog

## V.0.0.1 – Development snapshot (2026-11-21)

- Establish `0.0.1` as the package version and `V.0.0.1` as the display label. The CLI and window title expose the same version as the package metadata. Foundation CI checks the manifest and current documentation.
- Integrate Connected System branding and the optically balanced V.02 front-view pieces with stronger shading for dark pieces. Keep the separate top-view set, editable SVG masters, offline PNG fallbacks, and the Tk 9 session preview for custom SVG boards.
- Test configured local UCI engines through `readyok`, show the advertised name and option count, and clean up the process and the Tk poll independently.
- Stabilize Tk test cleanup and enable crash diagnostics. Branch, PR and post-merge CI for PR #7 passed on Windows, macOS and Linux.
- Reconcile the current documentation with the code, archive prior planning snapshots, and record the next tasks and owner decisions. This is a development version.
- Show keyboard focus when entering the board, localize square and selection feedback, and support Enter on action buttons, including promotion choices.
- Clear the board focus message when keyboard focus leaves the board. Preserve newer action feedback and reject package acceptance records with unresolved blockers.
- End live games automatically when every legal reply is a capture leading to insufficient material. Preserve the recorded moves in older games and supplied puzzle lines.
- Recognize dead positions reached by short forced continuations into stalemate or insufficient material.
- Validate saved games on a temporary copy of an SQLite backup before replacing the active library.
- Show the preserved filename when the app creates a new library after database corruption. Verify repository asset paths and recorded hashes in the Foundation check.
- Show localized demo puzzle themes in the filter and puzzle details. Keep custom theme identifiers visible and preserve the original identifiers used for filtering.
- Add optional quality thresholds and rejection reasons to the offline puzzle builder. Record the origin of each puzzle and correct the source metadata of the bundled demo pack.
- Add an optional seed for repeatable selection from a fully validated puzzle source. Report the source checksum and the number of selected puzzles.
- Keep valid CSV records around malformed UTF-8 bytes and verify the checksums of the archived OneDrive snapshots in Foundation CI.

The dated entries below preserve the development history incorporated into this snapshot.

## Unreleased – Saved game endings and history (2026-11-20)

- Keep local resignation and draw-claim details when reopening a game. SQLite v3 migrates existing libraries after creating a backup.
- Fix saving games that ended before the first move.
- Store individual history entries for undo and redo instead of copying the entire move list and repetition table.
- Keep the play controls reachable in small windows with vertical scrolling and automatic focus visibility.

## Unreleased – PGN exchange and puzzle filters (2026-11-20)

- Import and export a single UTF-8 PGN game from the local library. Bound input size and move count and replace export files atomically.
- Filter Puzzle Lab by theme and rating and show saved solves in the current selection.
- Score resignation against a lone king as a draw, preserving the outcome through undo and redo.

## Unreleased – N02 follow-up (2026-11-20)

- Added draw claims in the Tk app for the current position and for a declared legal move.
- Reset the UCI engine once per game and skip cancelled searches before they can reach the engine.
- Reopen stored games and recorded PGN results in the local two-player interface.
- Validate and, if needed, migrate a backup before restoring it. Preserve the active database on invalid input.
- Reject normalized duplicate puzzle IDs and validate loaded packs beyond their checksum.
- Added external Perft fixtures and a Tk underpromotion regression. Run native Tk CI on Python 3.11 and 3.14.

## Unreleased – N02 Functional Core (2026-11-20, merged in PR #2)

- Evidence-based work-package status model; F0 baseline preserved.
- Chess core: structural SAN parser (PGN import ~14× faster), PGN result
  consistency checks, promotion without `=`, new golden/perft/property tests.
- Game controller with asynchronous bot worker, stale-result protection and
  engine fault handling; project-owned mock UCI engine (not a chess AI).
- Six data-driven bot presets with handshake-based option negotiation.
- Puzzle Lab: streaming Lichess CSV importer (Rating ≥ 1000), versioned
  packs, solving sessions, five project-authored demo puzzles.
- Local storage: platform data paths, SQLite migrations, backup/restore,
  corruption quarantine, atomic JSON settings.
- Tk app: bot modes, levels, engine settings dialog, puzzle tab, save game,
  copy PGN, shortcuts, DE/EN UI, exchangeable piece renderer, SVG contract.
- CI split into foundation/docs, policy, headless OS×Python matrix, GUI jobs.

## Unreleased – Foundation F0 (2026-11-19)

- Initial repository starter, product brief, licensing decision gate and prompt work orders.
- Source scaffolding and standard-library-based validation scripts.
- No chess UI, engine, puzzles or public installers implemented.
