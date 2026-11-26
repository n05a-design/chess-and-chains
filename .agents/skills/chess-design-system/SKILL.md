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
- Preserve **Connected System** assets (Manufacturing Consent wordmark, the three registered piece sets, Puzzle Atlas, 3D marble board). Never import Glide logos, mascots, or Glide purple (`#9E4AC8`).
- **Logos (contract: [design/01_Logo/README.md](../../../design/01_Logo/README.md)).** Three owner masters in `design/01_Logo/svg/`, never edited: Logo 01 `in_app` (header signet, tinted with `ThemePalette.view_title`, white separator bands become transparent cut-outs), Logo 02 `internal_brand` (full-colour About emblem, never tinted), Logo 03 `app_icon` (window/taskbar/Dock icon, README, social preview, favicon; never tinted). Access logos only through `ui/branding.py` (`apply_window_icon`, `emblem_image`, `draw_signet_canvas`, `in_app_logo_photo`). Regenerate every derived file with `python3 -B scripts/build_brand_assets.py`, verify with `--check` and `tests.test_brand_assets`; update only the affected `BRAND-*` rows in `ASSET_REGISTER.csv`. The former orthogonal signet and dark-tile icon are historical and must not return. Do not hand-edit derived PNG/ICO/ICNS files or add logos decoratively to dialogs and cards.
