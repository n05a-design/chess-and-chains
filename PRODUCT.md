# Product

<!-- impeccable:product-schema 1 -->

This file is a concise design-tool context projection. The project's canonical
requirements, decisions, and open questions remain in `docs/product/`,
`docs/decisions/`, and `docs/questions/`.

Development snapshot **V.0.2.0**. See the [project manifest](MANIFEST.md).

## Platform

adaptive

Standalone Python desktop application; native UI behavior may vary by target OS.
Windows/macOS are project targets, not release-tested platforms.

## Users

The first board prototype targeted two people playing a local game on one
desktop. N02 added a bot mode wired to a project-owned mock engine to prove
the asynchronous engine path; it is not a real opponent. Other user groups in
`docs/product/PRODUCT_BRIEF.md` remain product hypotheses.

## Product Purpose

Build an independent chess desktop app designed to function fully offline.
Success for this slice is a locally playable two-person game where every move
is validated by the headless rules domain.

## Positioning

Offline-first local chess without a required account, server, or telemetry.
The local desktop prototype (two players, mock-bot mode, demo Puzzle Lab) is
implemented but not released. No real engine is bundled or tested, no
Lichess puzzle data is shipped, and there is no installer.

## Operating Context

One desktop window. Two local players, or one player against a bot. The bot
defaults to the mock engine and the UI labels it as "not a chess AI"; real
bot play must not be claimed until a real engine is tested (ADR-001).

## Capabilities and Constraints

- The independent MPL-2.0 rules domain is implemented and locally tested;
  including current-position and declared-move draw claims. The local game library reopens
  games for two-player play or review, preserving the recorded result. Evidence and limits
  are in `docs/reports/2026-11-20_N02-follow-up.md`.
- A local W06 board prototype is implemented with original Tk code only; Glide
  Shell and its code remain unapproved.
- Stockfish/GPL distribution is unresolved. No automatic network access or
  engine installation.
- Connected System is the owner-selected brand direction. The board uses
  owner SVG pieces in front view V.02 and a selectable top view. The
  prototype can preview the owner's local SVG boards with Tk 9.
- Keyboard operation, focus visibility, scaling, and reduced-motion behavior
  are required W06 checks; screen-reader conformance remains unverified.

## Brand Commitments

`Chess & Chains` is the working name. Manufacturing Consent is the chosen
display face and appears as vector outlines in the app wordmark. The supplied
piece designs are cleared for the app under MPL-2.0. Final owner board designs
and individual release approvals are tracked in Q-004, Q-014 and ADR-005.

## Evidence on Hand

The rules, mock UCI, puzzle fixtures, storage and GUI have automated test
evidence. PR #7 passed the GitHub Actions matrix on Windows, macOS and Linux.
Manual accessibility, native installer and real-engine acceptance remain open.

## Product Principles

- Offline behavior is a product requirement, not a marketing claim before
  implementation and testing.
- Validate chess rules in the domain, never in UI callbacks.
- Preserve license, asset, and framework approval gates.
- Report implemented, tested, and released states separately.
