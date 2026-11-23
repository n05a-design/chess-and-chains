---
name: chess-design-system
description: Design system for Chess & Chains combining Connected System brand identity with the portable Glide Shell design contract (P1-P6, B15, B11, Light/Dark themes, WCAG 2.2 AA contrast, SVG piece assets). Use when editing UI layouts, colors, themes, typography, SVG pieces, or board views.
---

# Chess & Chains Design System

Combines the **Connected System** brand identity with the portable **Glide Shell Design Contract**.

## References

- Portable Glide Design Contract: [DESIGN_RICHTLINIEN.md](../../../src/glide_shell/DESIGN_RICHTLINIEN.md)
- Chess & Chains Design Contract: [GLIDE_DESIGN_CONTRACT.md](../../../docs/design/GLIDE_DESIGN_CONTRACT.md)
- Connected System Brand Guide: [CONNECTED_SYSTEM.md](../../../docs/design/CONNECTED_SYSTEM.md)
- Brand Tokens: [brand-tokens.json](../../../docs/design/brand-tokens.json)
- Runtime Theme System: [theme.py](../../../src/chess_and_chains/ui/theme.py)

## Rules

- Apply P1–P6, B15 (button protection across 860×700 and 1280×800), B11 (hierarchy over metadata), B01/B16 (immediate feedback), B03 (interruptible ≤ 150 ms transitions via `motion.Transitions`), and WCAG 2.2 AA contrast (`>= 4.5:1` body text) in both Light and Dark themes.
- Preserve **Connected System** assets (orthogonal link signet, Manufacturing Consent wordmark, V.02 & top-view SVG pieces, Puzzle Atlas, 3D marble board). Never import Glide logos, mascots, or Glide purple (`#9E4AC8`).
