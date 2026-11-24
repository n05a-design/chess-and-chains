# W03–W06 · V.0.3.0 – Glide v1.0.2 Design Language, Rounded Canvas Cards & Appearance Customization

**Date:** 2026-11-24  
**Branch:** `feat/chess-glide-1.0.2-shell-integration`  
**Version:** V.0.3.0  
**Status:** IMPLEMENTED · TESTED

---

## Goal

Completely replace pre-Glide rectangular containers and yellow-white/parchment defaults
(`#EFE8D8`, `#FAF6EC`, `#FFFCF4`, `#F4C400`) with the full Glide v1.0.2 / Glide Shell 0.6.2
design language, rounded Canvas cards and buttons with seamless carrier-background blending,
all 10 Glide themes, and interactive Appearance customization while keeping Glide-product purple
(`#9E4AC8`) excluded.

---

## Changes

### `src/chess_and_chains/ui/theme.py`
- **All 10 Glide themes + `w06-provisional` alias + `system`:** `LIGHT_THEME`, `DARK_THEME`,
  `GLASS_LIGHT_THEME`, `GLASS_DARK_THEME`, `DOPAMINE_THEME`, `PIXEL_THEME`,
  `CONTRAST_LIGHT_THEME`, `CONTRAST_DARK_THEME`, `MINIMAL_LIGHT_THEME`, `MINIMAL_DARK_THEME`.
- **Full customization API:** `ACCENT_CHOICES` (8 roles), `BACKGROUND_CHOICES` (10 tints),
  `RADIUS_CHOICES` (`18`, `12`, `6`, `0` px), `FONT_SCALE_CHOICES` (`0.9`, `1.0`, `1.15`),
  `FONT_WEIGHT_CHOICES` (`auto`, `standard`, `bold`), `with_accent()`, `with_background()`,
  `customize_palette()`, and `font_spec()`.
- **`RoundedSurfaceCard`:** rounded Canvas surface container (`bg_color`, `fill_color`,
  `outline_color`, dynamic `radius`, `auto_height`, `set_theme`).
- **`RoundedButton`:** Canvas rounded button blending its outer corners into parent
  `carrier_bg`, with hover/press feedback, `cget("background")` compatibility, and dynamic theme updates.
- **`install_ttk_theme()` / `apply_listbox_theme()` / `apply_optionmenu_theme()`:** updated
  to Glide tokens with Cobalt blue accent (`#086FD6` light / `#2C95FF` dark).

### `src/chess_and_chains/ui/branding.py`, `appearance_dialog.py` & `app.py`
- Added borderless monochrome `HeaderLogoCanvas` (`signet_bounding_box`, `in_app_logo_photo`,
  `render_signet_rgba_png`) rendered directly in WCAG-verified `theme.view_title` via
  `legible_accent()` and optically aligned to title cap-top & subtitle baseline across font scales,
  while keeping master SVGs and multi-color OS app icons untouched.
- Added unified Glide Settings (`AppearanceDialog`, `Cmd/Ctrl+,`, header `⚙`), enforced uniform
  `PANEL_GAP = 12 px` card spacing, and added standalone startup (`start_chess_and_chains.py`,
  `Start Chess & Chains.command`, `packaging/macos/build_app.py`).
- Replaced rectangular `_sheet_pair` frames and `TabRail` `tk.Button` widgets with
  `RoundedSurfaceCard` (`header_card`, `_side_slot`, `_board_slot`, `_rail_slot`, `atlas_section`)
  and `RoundedButton`.
- Added `ChessApp.apply_appearance()` and `ChessApp.open_appearance_dialog()`.

### `src/chess_and_chains/ui/{board,marble_board,atlas,dialogs,replay,text_board}.py`
- Propagated dynamic `ThemePalette` updates to 2D board, 3D marble board, Puzzle Atlas,
  dialogs, replay viewer, and text board; adopted `ThemedAutoScrollbar` in `ReplayDialog`
  and `TextBoardDialog` (retaining styled `tk.Listbox` for `selection_anchor` compatibility).

### `src/chess_and_chains/storage/settings.py` & `i18n/catalog.py`
- Persisted and validated `background_choice`, `accent_choice`, `radius_choice`,
  `font_scale_choice`, `font_weight_choice`, `animations_enabled`, `hints_visible` with full
  DE/EN localization keys.

### `docs/design/GLIDE_DESIGN_CONTRACT.md` & `brand-tokens.json` & `CHANGELOG.md`
- Updated contract, tokens, and changelog to V.0.3.0.

---

## Test & Verification Evidence

- **Full unittest suite:** `PYTHONPATH=src python3 -m unittest discover -s tests -q` → `279` tests `OK` (exit `0`)
- **Starter & status audit:** `python3 scripts/verify_starter.py` → `PASS` (exit `0`)
- **Policy check:** `python3 scripts/check_policy.py` → `PASS` (exit `0`)
- **Document link audit:** `python3 scripts/verify_document_links.py` → `PASS` (exit `0`)

---

## Next Actions

1. Perform manual visual & scaling acceptance (100% / 150% / 200%, VoiceOver/NVDA) on macOS/Windows/Linux.
