"""Pure Glide v1.0.2 / Glide Shell 0.6.2 design system for Chess & Chains – V.0.3.0.

All color palettes, typography scales, spacing tokens, corner radii, accent
choices, background tints and Canvas widget primitives follow the portable Glide
Shell 0.6.2 design contract (src/glide_shell/DESIGN_RICHTLINIEN.md) and the
canonical Glide v1.0.2 design language — without Glide product-specific brand
assets or Glide-purple (#9E4AC8).

SPDX-License-Identifier: MPL-2.0
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

from dataclasses import dataclass, replace
import tkinter as tk
from tkinter import font as tkfont
from types import MappingProxyType
from typing import Callable, Sequence

from glide_shell import custom_controls, system_appearance, text_fit, window_lifetime

# ---------------------------------------------------------------------------
# Glide v1.0.2 / Shell 0.6.2 – canonical default tokens (Light defaults; Dark is
# resolved dynamically via ThemePalette / ThemeManager).
# Zero pre-Glide parchment/cream/yellow (#EFE8D8/#FAF6EC/#F4C400) leftovers.
# ---------------------------------------------------------------------------

WINDOW          = "#F5F5F7"   # outermost root background (Glide Light window)
PAPER           = "#FFFFFF"   # elevated panel / button / control surface
ACETATE         = "#FFFFFF"   # inner card / sheet content surface
SHADOW          = "#D8D8DE"   # subtle card border / elevation frame
INK             = "#15243C"   # primary text / foreground
MUTED_INK       = "#595960"   # secondary / caption text (WCAG >= 4.5 on paper & hover)
FOCUS_INK       = "#086FD6"   # keyboard-focus indicator
DISABLED_INK    = "#707074"   # disabled text
TAB_IDLE        = "#E5E5EA"   # inactive tab surface
INPUT_BORDER    = "#D8D8DE"   # input field border (unfocused)
LINE            = "#D8D8DE"   # subtle divider / hairline
HOVER           = "#D8E9FE"   # interactive hover tint

# Shell-neutral primary action & semantic accents (host-neutral, no #9E4AC8)
BRAND_BLUE      = "#086FD6"   # primary action accent & active highlight
CHROME_YELLOW   = "#086FD6"   # compatibility alias pointing to neutral host accent
BRAND_RED       = "#B8221A"   # destructive / delete
CONFIRM_GREEN   = "#196B2E"   # confirm / success
SELECTION_BG    = BRAND_BLUE
SELECTION_FG    = "#FFFFFF"
VIEW_TITLE      = INK

# Chess-domain board defaults aligned with Glide Cobalt Themenfarbe
SQUARE_LIGHT    = "#D1E1F2"
SQUARE_DARK     = "#315E8E"
LAST_MOVE       = "#98BFE7"
LEGAL_MARK      = "#15243C"
ATLAS_LINE      = "#34689F"

# ---------------------------------------------------------------------------
# Glide spacing scale (px)
# ---------------------------------------------------------------------------
SPACING = MappingProxyType(
    {v: v for v in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 18, 22, 24, 28, 30)}
)

# ---------------------------------------------------------------------------
# Glide corner-radius tokens & selectable radius levels
# ---------------------------------------------------------------------------
RADII = MappingProxyType({
    "card":  18,   # cards, panels, sidebar rail pills
    "field": 12,   # standard buttons, inputs, tabs
    "chip":  10,   # compact badges / tags
    "small":  6,   # subtle corners / inline elements
})

RADIUS_CHOICES: tuple[tuple[str, str, int], ...] = (
    ("large",    "theme.radius.large",    18),
    ("standard", "theme.radius.standard", 12),
    ("subtle",   "theme.radius.subtle",    6),
    ("flat",     "theme.radius.flat",      0),
)
RADIUS_MAP: dict[str, int] = {key: radius for key, _, radius in RADIUS_CHOICES}

# ---------------------------------------------------------------------------
# Glide typographic scale & customization options
# ---------------------------------------------------------------------------
FONT_SIZES: dict[str, int] = {
    "caption": 10,
    "body":    11,
    "section": 16,
    "title":   22,
}

FONT_SCALE_CHOICES: tuple[tuple[str, str, float], ...] = (
    ("compact",  "theme.font_scale.compact",  0.90),
    ("standard", "theme.font_scale.standard", 1.00),
    ("large",    "theme.font_scale.large",    1.15),
)
FONT_SCALE_MAP: dict[str, float] = {key: scale for key, _, scale in FONT_SCALE_CHOICES}

FONT_WEIGHT_CHOICES: tuple[tuple[str, str], ...] = (
    ("auto",     "theme.font_weight.auto"),
    ("standard", "theme.font_weight.standard"),
    ("bold",     "theme.font_weight.bold"),
)
FONT_WEIGHT_KEYS: frozenset[str] = frozenset(key for key, _ in FONT_WEIGHT_CHOICES)

# ---------------------------------------------------------------------------
# Glide Accent & Background Customization Choices (8 accents + 10 backgrounds)
# ---------------------------------------------------------------------------
ACCENT_CHOICES: tuple[tuple[str, str], ...] = (
    ("accent",     "theme.accent.accent"),
    ("clear",      "theme.accent.clear"),
    ("due_action", "theme.accent.due_action"),
    ("export",     "theme.accent.export"),
    ("flag",       "theme.accent.flag"),
    ("delete",     "theme.accent.delete"),
    ("import",     "theme.accent.import"),
    ("muted",      "theme.accent.muted"),
)
ACCENT_KEYS: frozenset[str] = frozenset(key for key, _ in ACCENT_CHOICES)

BACKGROUND_CHOICES: tuple[tuple[str, str], ...] = (
    ("default",    "theme.background.default"),
    ("surface",    "theme.background.surface"),
    ("accent",     "theme.background.accent"),
    ("clear",      "theme.background.clear"),
    ("due_action", "theme.background.due_action"),
    ("export",     "theme.background.export"),
    ("flag",       "theme.background.flag"),
    ("delete",     "theme.background.delete"),
    ("import",     "theme.background.import"),
    ("muted",      "theme.background.muted"),
)
BACKGROUND_KEYS: frozenset[str] = frozenset(key for key, _ in BACKGROUND_CHOICES)

# ---------------------------------------------------------------------------
# Glide layout constants & breakpoints (verbatim from Glide Shell 0.6.2)
# ---------------------------------------------------------------------------
TITLE_MAX_CHARS            = 40
BUTTON_TEXT_MAX_CHARS      = 24
NORMAL_MIN                 = (860, 700)
COMPACT_MIN                = (480, 560)
COMPACT_DEFAULT_WIDTH      = 480
COMPACT_DEFAULT_HEIGHT     = 760
SIDEBAR_WIDTH              = 328
SIDEBAR_RAIL_WIDTH         = 64
SIDEBAR_AUTO_NARROW_WIDTH  = 760
SIDEBAR_AUTO_RESTORE_WIDTH = 860
HEADER_DENSITY_FULL        = 1120
HEADER_DENSITY_COMPACT     = 900
HEADER_CAPTURE_MIN_WIDTH   = 640
HEIGHT_DENSITY_FULL        = 850
HEIGHT_DENSITY_COMPACT     = 780

# ---------------------------------------------------------------------------
# Colour-vision-deficiency palette (Okabe-Ito Glide standard set)
# ---------------------------------------------------------------------------
CVD_PALETTE = MappingProxyType({
    "orange":     "#E69F00",
    "sky":        "#56B4E9",
    "green":      "#009E73",
    "yellow":     "#F0E442",
    "blue":       "#0072B2",
    "vermillion": "#D55E00",
    "purple":     "#CC79A7",
})

BUTTON_ROLES = {
    "neutral": (TAB_IDLE, INK),
    "new":     (BRAND_BLUE, SELECTION_FG),
}

# ---------------------------------------------------------------------------
# Theme modes (10 canonical Glide themes + system selector)
# ---------------------------------------------------------------------------
THEME_MODES = ("light", "dark", "system")

EXTENDED_THEME_MODES = (
    "dark", "light",
    "glass-dark", "glass-light",
    "dopamine", "pixel",
    "contrast-dark", "contrast-light",
    "minimal-dark", "minimal-light",
    "system",
)

THEME_OPTIONS: tuple[tuple[str, str], ...] = (
    ("system",         "theme.system"),
    ("dark",           "theme.dark"),
    ("light",          "theme.light"),
    ("glass-dark",     "theme.glass_dark"),
    ("glass-light",    "theme.glass_light"),
    ("dopamine",       "theme.dopamine"),
    ("contrast-dark",  "theme.contrast_dark"),
    ("contrast-light", "theme.contrast_light"),
    ("minimal-dark",   "theme.minimal_dark"),
    ("minimal-light",  "theme.minimal_light"),
    ("pixel",          "theme.pixel"),
)

THEME_PAIRS = {
    "light":           "dark",
    "dark":            "light",
    "glass-light":     "glass-dark",
    "glass-dark":      "glass-light",
    "contrast-light":  "contrast-dark",
    "contrast-dark":   "contrast-light",
    "minimal-light":   "minimal-dark",
    "minimal-dark":    "minimal-light",
    "dopamine":        "light",
    "pixel":           "light",
    "w06-provisional": "dark",
}


def normalize_theme_name(name: str | None) -> str:
    """Normalize theme aliases (underscores, high-contrast, liquid-glass)."""
    norm = str(name or "light").strip().lower().replace("_", "-")
    if norm in ("high-contrast-dark", "cvd-dark"):
        return "contrast-dark"
    if norm in ("high-contrast-light", "cvd-light"):
        return "contrast-light"
    if norm in ("glass", "liquid-glass"):
        return "glass-dark"
    if norm in ("liquid-glass-light",):
        return "glass-light"
    return norm


def clip_button_text(text: str, limit: int = BUTTON_TEXT_MAX_CHARS) -> str:
    """Clip button labels to the Glide 24-character guideline."""
    return text_fit.clip(text, limit, ellipsis="…")


def remaining_text(length: int, limit: int = TITLE_MAX_CHARS, locale: str = "en") -> str:
    """Countdown text from the Glide length limit."""
    rest = int(limit) - max(0, int(length or 0))
    if locale.startswith("de"):
        if rest > 0:
            return "noch 1 Zeichen" if rest == 1 else f"noch {rest} Zeichen"
        if rest == 0:
            return "keine Zeichen mehr frei"
        return "1 Zeichen zu viel" if rest == -1 else f"{-rest} Zeichen zu viel"
    if rest > 0:
        return "1 char left" if rest == 1 else f"{rest} chars left"
    if rest == 0:
        return "0 chars left"
    return "1 char over" if rest == -1 else f"{-rest} chars over"


def toggle_partner_theme(theme_id: str | None) -> str:
    """Return the paired light/dark variant keeping theme family intact."""
    normalized = normalize_theme_name(theme_id)
    return THEME_PAIRS.get(normalized, "dark")


# ---------------------------------------------------------------------------
# Color math & WCAG 2.2 contrast helpers
# ---------------------------------------------------------------------------

def hex_rgb(value: str) -> tuple[int, int, int]:
    """Convert '#RRGGBB' hex string to RGB 3-tuple."""
    raw = str(value).lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        raise ValueError(f"Expected #RRGGBB hex color, got {value!r}")
    return (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))


def rgb_hex(rgb: tuple[float, float, float] | tuple[int, int, int]) -> str:
    """Format RGB 3-tuple as '#RRGGBB'."""
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def mix_rgb(
    first: tuple[int, int, int],
    second: tuple[int, int, int],
    share: float,
) -> tuple[float, float, float]:
    """Linear RGB blend between two colors."""
    return tuple(a + (b - a) * share for a, b in zip(first, second))  # type: ignore[return-value]


def _relative_luminance(hex_color: str) -> float:
    r, g, b = hex_rgb(hex_color)
    channels = []
    for channel in (r, g, b):
        srgb = channel / 255.0
        channels.append(srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(foreground: str, background: str) -> float:
    """Return WCAG 2.2 contrast ratio between two #RRGGBB colors."""
    lum_a = _relative_luminance(foreground)
    lum_b = _relative_luminance(background)
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


# ---------------------------------------------------------------------------
# ThemePalette — Glide semantic colour dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ThemePalette:
    """Semantic palette aligned 1:1 with the Glide v1.0.2 design contract."""
    mode: str
    # --- Glide surface roles ---
    window: str
    paper: str
    acetate: str
    shadow: str
    # --- Glide ink roles ---
    ink: str
    muted_ink: str
    focus_ink: str
    disabled_ink: str
    # --- Glide UI roles ---
    tab_idle: str
    brand_blue: str
    chrome_yellow: str
    brand_red: str
    # --- Chess board (domain-specific) ---
    square_light: str
    square_dark: str
    last_move: str
    legal_mark: str
    atlas_line: str
    # --- Glide semantic actions ---
    action_new_bg: str
    action_new_fg: str
    input_border: str
    line: str
    hover: str
    selection: str
    selection_text: str
    view_title: str
    confirm: str
    delete: str

    @property
    def is_dark(self) -> bool:
        return _relative_luminance(self.window) < 0.2

    def button_colors(self, role: str) -> tuple[str, str]:
        if role == "new":
            return self.action_new_bg, self.action_new_fg
        if role == "neutral":
            return self.tab_idle, self.ink
        raise ValueError(f"Unknown button role: {role!r}")


# ---------------------------------------------------------------------------
# 10 Canonical Glide v1.0.2 Palettes (all mathematically verified WCAG >= 4.5)
# ---------------------------------------------------------------------------

LIGHT_THEME = ThemePalette(
    mode="light",
    window="#F5F5F7",
    paper="#FFFFFF",
    acetate="#FFFFFF",
    shadow="#D8D8DE",
    ink="#15243C",
    muted_ink="#595960",
    focus_ink="#086FD6",
    disabled_ink="#707074",
    tab_idle="#E5E5EA",
    brand_blue="#086FD6",
    chrome_yellow="#086FD6",
    brand_red="#B8221A",
    square_light="#D1E1F2",
    square_dark="#315E8E",
    last_move="#98BFE7",
    legal_mark="#15243C",
    atlas_line="#34689F",
    action_new_bg="#086FD6",
    action_new_fg="#FFFFFF",
    input_border="#D8D8DE",
    line="#D8D8DE",
    hover="#D8E9FE",
    selection="#086FD6",
    selection_text="#FFFFFF",
    view_title="#0767C7",
    confirm="#196B2E",
    delete="#B8221A",
)

DARK_THEME = ThemePalette(
    mode="dark",
    window="#111113",
    paper="#1C1C1E",
    acetate="#1C1C1E",
    shadow="#08080A",
    ink="#F5F5F7",
    muted_ink="#A6ABB3",
    focus_ink="#2C95FF",
    disabled_ink="#939398",
    tab_idle="#2C2C2E",
    brand_blue="#2C95FF",
    chrome_yellow="#2C95FF",
    brand_red="#FF8078",
    square_light="#A6C2E1",
    square_dark="#2B5481",
    last_move="#22558A",
    legal_mark="#F5F5F7",
    atlas_line="#4E82BA",
    action_new_bg="#2C95FF",
    action_new_fg="#111113",
    input_border="#3A3A3C",
    line="#2C2C2E",
    hover="#243A55",
    selection="#2C95FF",
    selection_text="#111113",
    view_title="#4EA6FF",
    confirm="#30D158",
    delete="#FF8078",
)

GLASS_LIGHT_THEME = ThemePalette(
    mode="glass-light",
    window="#EDF3FA",
    paper="#FFFFFF",
    acetate="#F7FAFE",
    shadow="#AABBD1",
    ink="#15243C",
    muted_ink="#52627A",
    focus_ink="#086FD6",
    disabled_ink="#707074",
    tab_idle="#DCE8F7",
    brand_blue="#086FD6",
    chrome_yellow="#086FD6",
    brand_red="#B8221A",
    square_light="#D1E1F2",
    square_dark="#315E8E",
    last_move="#98BFE7",
    legal_mark="#15243C",
    atlas_line="#34689F",
    action_new_bg="#086FD6",
    action_new_fg="#FFFFFF",
    input_border="#AABBD1",
    line="#C7D5E8",
    hover="#DCE8F7",
    selection="#086FD6",
    selection_text="#FFFFFF",
    view_title="#0766C5",
    confirm="#196B2E",
    delete="#B8221A",
)

GLASS_DARK_THEME = ThemePalette(
    mode="glass-dark",
    window="#151B27",
    paper="#222E42",
    acetate="#1E2738",
    shadow="#0B1018",
    ink="#F5F5F7",
    muted_ink="#B2C0D8",
    focus_ink="#4DA6FF",
    disabled_ink="#939FB5",
    tab_idle="#2C374B",
    brand_blue="#4DA6FF",
    chrome_yellow="#4DA6FF",
    brand_red="#FF8C85",
    square_light="#AEC6E1",
    square_dark="#375A81",
    last_move="#315D8A",
    legal_mark="#F5F5F7",
    atlas_line="#5C8ABA",
    action_new_bg="#4DA6FF",
    action_new_fg="#111113",
    input_border="#5C6F8E",
    line="#3A4A63",
    hover="#2E3E59",
    selection="#4DA6FF",
    selection_text="#111113",
    view_title="#5BADFF",
    confirm="#3BE068",
    delete="#FF8C85",
)

DOPAMINE_THEME = ThemePalette(
    mode="dopamine",
    window="#050310",
    paper="#150F2E",
    acetate="#120D28",
    shadow="#020108",
    ink="#FFFBFF",
    muted_ink="#C7B4FF",
    focus_ink="#00D9FF",
    disabled_ink="#8574C6",
    tab_idle="#221742",
    brand_blue="#00D9FF",
    chrome_yellow="#00D9FF",
    brand_red="#FF6E94",
    square_light="#C7BAEE",
    square_dark="#45337A",
    last_move="#2A1A5A",
    legal_mark="#00F0FF",
    atlas_line="#6B3FFF",
    action_new_bg="#00D9FF",
    action_new_fg="#050310",
    input_border="#6B3FFF",
    line="#3B2575",
    hover="#2A1A5A",
    selection="#00D9FF",
    selection_text="#050310",
    view_title="#00D9FF",
    confirm="#00FF9C",
    delete="#FF6E94",
)

PIXEL_THEME = ThemePalette(
    mode="pixel",
    window="#000000",
    paper="#0D0D12",
    acetate="#111118",
    shadow="#000000",
    ink="#FFFFFF",
    muted_ink="#C8C8DC",
    focus_ink="#38D5FF",
    disabled_ink="#8C8CA6",
    tab_idle="#17171F",
    brand_blue="#3D7BFF",
    chrome_yellow="#3D7BFF",
    brand_red="#FF6E88",
    square_light="#B8BDD4",
    square_dark="#2F3B6E",
    last_move="#1B2150",
    legal_mark="#38D5FF",
    atlas_line="#3D5AFE",
    action_new_bg="#3D7BFF",
    action_new_fg="#000000",
    input_border="#3D5AFE",
    line="#283593",
    hover="#1B2150",
    selection="#3D7BFF",
    selection_text="#000000",
    view_title="#4E87FF",
    confirm="#35E0A1",
    delete="#FF6E88",
)

CONTRAST_LIGHT_THEME = ThemePalette(
    mode="contrast-light",
    window="#FFFFFF",
    paper="#FFFFFF",
    acetate="#F5F8FA",
    shadow="#8D939E",
    ink="#101014",
    muted_ink="#3A3A42",
    focus_ink="#0072B2",
    disabled_ink="#5A5A64",
    tab_idle="#EDF3F7",
    brand_blue="#0072B2",
    chrome_yellow="#E69F00",
    brand_red="#B03A00",
    square_light="#F2EFE4",
    square_dark="#5A6E82",
    last_move="#D4E8F6",
    legal_mark="#0072B2",
    atlas_line="#4A4A52",
    action_new_bg="#0072B2",
    action_new_fg="#FFFFFF",
    input_border="#4A4A52",
    line="#6E6E76",
    hover="#D4E8F6",
    selection="#0072B2",
    selection_text="#FFFFFF",
    view_title="#006BA7",
    confirm="#00664C",
    delete="#B03A00",
)

CONTRAST_DARK_THEME = ThemePalette(
    mode="contrast-dark",
    window="#000000",
    paper="#141418",
    acetate="#1E1E24",
    shadow="#000000",
    ink="#FFFFFF",
    muted_ink="#D0D0DA",
    focus_ink="#F0E442",
    disabled_ink="#9A9AA6",
    tab_idle="#1E1E24",
    brand_blue="#56B4E9",
    chrome_yellow="#F0E442",
    brand_red="#FF8F4D",
    square_light="#B8C2CC",
    square_dark="#3E5063",
    last_move="#13354A",
    legal_mark="#56B4E9",
    atlas_line="#8E8E9A",
    action_new_bg="#56B4E9",
    action_new_fg="#000000",
    input_border="#8E8E9A",
    line="#6E6E7A",
    hover="#13354A",
    selection="#56B4E9",
    selection_text="#000000",
    view_title="#56B4E9",
    confirm="#33D6A6",
    delete="#FF8F4D",
)

MINIMAL_LIGHT_THEME = ThemePalette(
    mode="minimal-light",
    window="#F4F4F4",
    paper="#FFFFFF",
    acetate="#FAFAFA",
    shadow="#D4D4D4",
    ink="#171717",
    muted_ink="#4F4F4F",
    focus_ink="#171717",
    disabled_ink="#626262",
    tab_idle="#EDEDED",
    brand_blue="#2B2B2B",
    chrome_yellow="#2B2B2B",
    brand_red="#171717",
    square_light="#EFEFEF",
    square_dark="#787878",
    last_move="#D9D9D9",
    legal_mark="#171717",
    atlas_line="#8E8E8E",
    action_new_bg="#2B2B2B",
    action_new_fg="#FFFFFF",
    input_border="#B4B4B4",
    line="#D4D4D4",
    hover="#E4E4E4",
    selection="#2B2B2B",
    selection_text="#FFFFFF",
    view_title="#2B2B2B",
    confirm="#2B2B2B",
    delete="#171717",
)

MINIMAL_DARK_THEME = ThemePalette(
    mode="minimal-dark",
    window="#111111",
    paper="#1A1A1A",
    acetate="#232323",
    shadow="#080808",
    ink="#F4F4F4",
    muted_ink="#A6A6A6",
    focus_ink="#F4F4F4",
    disabled_ink="#989898",
    tab_idle="#232323",
    brand_blue="#D6D6D6",
    chrome_yellow="#E4E4E4",
    brand_red="#F4F4F4",
    square_light="#A8A8A8",
    square_dark="#4E4E4E",
    last_move="#2B2B2B",
    legal_mark="#F4F4F4",
    atlas_line="#6A6A6A",
    action_new_bg="#E4E4E4",
    action_new_fg="#111111",
    input_border="#4E4E4E",
    line="#333333",
    hover="#2B2B2B",
    selection="#D6D6D6",
    selection_text="#111111",
    view_title="#D6D6D6",
    confirm="#E4E4E4",
    delete="#F4F4F4",
)

THEMES: dict[str, ThemePalette] = {
    "light":           LIGHT_THEME,
    "dark":            DARK_THEME,
    "glass-light":     GLASS_LIGHT_THEME,
    "glass-dark":      GLASS_DARK_THEME,
    "dopamine":        DOPAMINE_THEME,
    "pixel":           PIXEL_THEME,
    "contrast-light":  CONTRAST_LIGHT_THEME,
    "contrast-dark":   CONTRAST_DARK_THEME,
    "minimal-light":   MINIMAL_LIGHT_THEME,
    "minimal-dark":    MINIMAL_DARK_THEME,
    "w06-provisional": LIGHT_THEME,
}

# Host-neutral accent & background semantic color maps (light / dark variants)
_ACCENT_MAP_LIGHT = {
    "clear":      "#0072B2",
    "due_action": "#0E7490",
    "export":     "#196B2E",
    "flag":       "#945400",
    "delete":     "#B8221A",
    "import":     "#7A4A00",
    "muted":      "#4A4E5A",
}

_ACCENT_MAP_DARK = {
    "clear":      "#56B4E9",
    "due_action": "#40C8E0",
    "export":     "#30D158",
    "flag":       "#FFC038",
    "delete":     "#FF8078",
    "import":     "#D0A46F",
    "muted":      "#B8BDC7",
}


def legible_accent(
    color: str,
    surfaces: Sequence[str],
    *,
    is_dark: bool,
    minimum: float = 4.5,
) -> str:
    """Return ``color`` or blend it cleanly until every surface achieves ``minimum`` contrast."""
    bg_list = tuple(s for s in surfaces if s)
    if not bg_list or all(contrast_ratio(color, bg) >= minimum for bg in bg_list):
        return color
    pole = (255, 255, 255) if is_dark else (0, 0, 0)
    base = hex_rgb(color)
    for step in range(1, 101):
        candidate = rgb_hex(mix_rgb(base, pole, step / 100.0))
        if all(contrast_ratio(candidate, bg) >= minimum for bg in bg_list):
            return candidate
    return "#FFFFFF" if is_dark else "#000000"


def derive_board_colors(
    palette: ThemePalette,
    target_hex: str,
    choice: str,
) -> tuple[str, str, str, str, str]:
    """Derive ``(square_light, square_dark, last_move, legal_mark, atlas_line)`` from Themenfarbe."""
    if choice == "muted":
        if palette.is_dark:
            return "#B8BCC4", "#484C54", "#2E323A", "#F4F5F7", "#767B85"
        return "#EAECF0", "#6A6F7A", "#D0D5DF", "#17191E", "#5A5F6A"

    target_rgb = hex_rgb(target_hex)
    is_contrast = palette.mode.startswith("contrast")
    if palette.mode == "dopamine":
        sq_light = rgb_hex(mix_rgb((200, 195, 225), target_rgb, 0.28))
        sq_dark = rgb_hex(mix_rgb((28, 20, 56), target_rgb, 0.34))
        last_mv = rgb_hex(mix_rgb((18, 13, 40), target_rgb, 0.45))
        legal = (
            legible_accent(target_hex, (sq_dark, sq_light), is_dark=True, minimum=2.5)
            if contrast_ratio(target_hex, sq_light) >= 2.5
            else palette.ink
        )
        atlas = target_hex
    elif palette.mode == "pixel":
        sq_light = rgb_hex(mix_rgb((190, 195, 215), target_rgb, 0.25))
        sq_dark = rgb_hex(mix_rgb((24, 30, 54), target_rgb, 0.36))
        last_mv = rgb_hex(mix_rgb((15, 18, 38), target_rgb, 0.48))
        legal = legible_accent(target_hex, (sq_dark,), is_dark=True, minimum=3.2)
        atlas = target_hex
    elif palette.is_dark:
        light_share = 0.20 if is_contrast else 0.24
        dark_share = 0.30 if is_contrast else 0.36
        sq_light = rgb_hex(mix_rgb((204, 208, 216), target_rgb, light_share))
        sq_dark = rgb_hex(mix_rgb((42, 48, 58), target_rgb, dark_share))
        last_mv = rgb_hex(mix_rgb((26, 30, 38), target_rgb, 0.46))
        legal = palette.ink
        atlas = rgb_hex(mix_rgb((105, 115, 130), target_rgb, 0.45))
    else:
        light_share = 0.11 if is_contrast else 0.14
        dark_share = 0.34 if is_contrast else 0.38
        sq_light = rgb_hex(mix_rgb((242, 244, 247), target_rgb, light_share))
        sq_dark = rgb_hex(mix_rgb((74, 84, 98), target_rgb, dark_share))
        last_mv = rgb_hex(mix_rgb((226, 232, 240), target_rgb, 0.34))
        legal = palette.ink
        atlas = rgb_hex(mix_rgb((88, 98, 114), target_rgb, 0.45))
    return sq_light, sq_dark, last_mv, legal, atlas


def with_accent(palette: ThemePalette, choice: str) -> ThemePalette:
    """Apply Themenfarbe to interactive UI controls and chessboard square tokens."""
    if choice not in ACCENT_KEYS or choice == "accent":
        return palette
    accent_map = _ACCENT_MAP_DARK if palette.is_dark else _ACCENT_MAP_LIGHT
    target = accent_map.get(choice)
    if not target:
        return palette
    c_dark = contrast_ratio("#111113", target)
    c_light = contrast_ratio("#FFFFFF", target)
    fg = "#111113" if c_dark >= c_light else "#FFFFFF"
    title_color = palette.ink if choice == "muted" else legible_accent(
        target,
        (palette.window, palette.paper, palette.acetate, palette.hover),
        is_dark=palette.is_dark,
        minimum=4.5,
    )
    sq_light, sq_dark, last_mv, legal, atlas = derive_board_colors(palette, target, choice)
    return replace(
        palette,
        focus_ink=target,
        brand_blue=target,
        action_new_bg=target,
        action_new_fg=fg,
        selection=target,
        selection_text=fg,
        view_title=title_color,
        square_light=sq_light,
        square_dark=sq_dark,
        last_move=last_mv,
        legal_mark=legal,
        atlas_line=atlas,
    )


def with_background(palette: ThemePalette, choice: str) -> ThemePalette:
    """Apply a Glide background tint choice while preserving cards & text contrast."""
    if choice not in BACKGROUND_KEYS or choice == "default":
        return palette
    if choice == "surface":
        return replace(palette, window=palette.paper)
    accent_map = _ACCENT_MAP_DARK if palette.is_dark else _ACCENT_MAP_LIGHT
    tint_hex = palette.action_new_bg if choice == "accent" else accent_map.get(choice)
    if not tint_hex:
        return palette
    base = hex_rgb(palette.window)
    tint = hex_rgb(tint_hex)
    share = 0.14 if palette.is_dark else 0.08
    tinted_window = rgb_hex(mix_rgb(base, tint, share))
    safe_title = legible_accent(
        palette.view_title,
        (tinted_window, palette.paper, palette.acetate, palette.hover),
        is_dark=palette.is_dark,
        minimum=4.5,
    )
    return replace(palette, window=tinted_window, view_title=safe_title)


def customize_palette(
    palette: ThemePalette,
    *,
    accent: str = "accent",
    background: str = "default",
) -> ThemePalette:
    """Apply accent and background customization while preserving identity on defaults."""
    if accent == "accent" and background == "default":
        return palette
    return with_background(with_accent(palette, accent), background)


# ---------------------------------------------------------------------------
# System-dark detection & theme resolution
# ---------------------------------------------------------------------------

def detect_system_dark(root: tk.Misc | None = None) -> bool | None:
    """Detect OS dark mode via Tk queries interpreted by ``system_appearance``."""
    if root is None:
        return None
    try:
        ws = str(root.tk.call("tk", "windowingsystem"))
    except tk.TclError:
        return None
    if ws == "aqua":
        try:
            answer = root.tk.call("tk::unsupported::MacWindowStyle", "isdark", root)
            return system_appearance.tk_is_dark(answer)
        except tk.TclError:
            pass
    try:
        answer = root.tk.call("winfo", "isdark", root)
        return system_appearance.tk_is_dark(answer)
    except tk.TclError:
        return None


def resolve_theme(
    theme_id: str | None,
    root: tk.Misc | None = None,
    *,
    system_dark: bool | None = None,
    accent: str = "accent",
    background: str = "default",
) -> ThemePalette:
    """Resolve explicit or system theme + optional accent/background customization."""
    normalized = normalize_theme_name(theme_id)
    if normalized == "system":
        dark = detect_system_dark(root) if system_dark is None else system_dark
        base = system_appearance.resolve(
            {"light": LIGHT_THEME, "dark": DARK_THEME},
            dark,
            LIGHT_THEME,
        )
    else:
        base = THEMES.get(normalized, LIGHT_THEME)
    return customize_palette(base, accent=accent, background=background)


# ---------------------------------------------------------------------------
# Typography scaling & weight helpers (Glide parity)
# ---------------------------------------------------------------------------

def font_spec(
    role_or_size: str | int = "body",
    *styles: str,
    scale_choice: str = "standard",
    weight_choice: str = "standard",
    mono: bool = False,
) -> tuple[object, ...]:
    """Return a Tk font tuple scaled by Glide font_scale and font_weight."""
    family = "TkFixedFont" if mono else "TkDefaultFont"
    base_size = FONT_SIZES.get(role_or_size, FONT_SIZES["body"]) if isinstance(role_or_size, str) else int(role_or_size)
    factor = FONT_SCALE_MAP.get(scale_choice, 1.0)
    scaled_size = max(7, int(round(base_size * factor)))
    style_tokens = [s for s in styles if s]
    if weight_choice == "bold" and "bold" not in style_tokens:
        style_tokens.append("bold")
    style_str = " ".join(style_tokens)
    return (family, scaled_size, style_str) if style_str else (family, scaled_size)


# ---------------------------------------------------------------------------
# Typography providers (Glide Shell interface contract)
# ---------------------------------------------------------------------------

def _host_font_provider(size: int, *styles: str) -> tuple[object, ...]:
    style_str = " ".join(s for s in styles if s)
    return ("TkDefaultFont", size, style_str) if style_str else ("TkDefaultFont", size)


def _host_ink_provider(widget: tk.Misc | None, font: object, text: str, width: int) -> tuple[int, int]:
    root = widget.winfo_toplevel() if widget is not None else None
    font_obj = font if isinstance(font, tkfont.Font) else tkfont.Font(root=root, font=font)
    measured = font_obj.measure(text)
    line_height = font_obj.metrics("linespace")
    return min(measured, width) if width else measured, line_height


def install_shell_providers() -> None:
    """Register typography providers on ``glide_shell.custom_controls``."""
    custom_controls.set_font_provider(_host_font_provider)
    custom_controls.set_ink_provider(_host_ink_provider)


def apply_window_geometry(
    window: tk.Misc,
    width: int,
    height: int,
    min_width: int,
    min_height: int,
) -> tuple[int, int]:
    """Clamp window dimensions safely via glide_shell.window_geometry."""
    from glide_shell import window_geometry as _wg
    try:
        screen_w = int(window.winfo_screenwidth())
        screen_h = int(window.winfo_screenheight())
    except Exception:
        screen_w, screen_h = 0, 0
    effective_min_w = min(min_width, max(320, screen_w)) if screen_w > 0 else min_width
    effective_min_h = min(min_height, max(240, screen_h - _wg.SCREEN_RESERVE)) if screen_h > 0 else min_height
    cw, ch, _, _ = _wg.clamp(width, height, None, None, screen_w, screen_h, (effective_min_w, effective_min_h))
    window.geometry(_wg.format_geometry(cw, ch))
    window.minsize(effective_min_w, effective_min_h)
    return cw, ch


# ---------------------------------------------------------------------------
# Glide Design Language – ttk.Style integration
# ---------------------------------------------------------------------------

def _ttk_style(root: "tk.Misc | None" = None) -> "object":
    """Return a fresh ``ttk.Style`` view for *root*'s interpreter."""
    from tkinter import ttk as _ttk
    return _ttk.Style(root)


def install_ttk_theme(
    root: "tk.Misc",
    palette: "ThemePalette",
    *,
    scale_choice: str = "standard",
    weight_choice: str = "standard",
) -> None:
    """Apply the complete Glide design language to all ttk widget styles."""
    style = _ttk_style(root)
    p = palette

    body_font    = font_spec("body",    scale_choice=scale_choice, weight_choice=weight_choice)
    body_bold    = font_spec("body",    "bold", scale_choice=scale_choice, weight_choice=weight_choice)
    caption_font = font_spec("caption", scale_choice=scale_choice, weight_choice=weight_choice)
    caption_bold = font_spec("caption", "bold", scale_choice=scale_choice, weight_choice=weight_choice)
    section_font = font_spec("section", "bold", scale_choice=scale_choice, weight_choice=weight_choice)
    title_font   = font_spec("title",   "bold", scale_choice=scale_choice, weight_choice=weight_choice)

    btn_padx   = SPACING[10]
    btn_pady   = SPACING[7]
    field_padx = SPACING[8]
    field_pady = SPACING[5]

    style.configure("TFrame",              background=p.acetate)
    style.configure("Glide.TFrame",        background=p.acetate)
    style.configure("Glide.Paper.TFrame",  background=p.paper)
    style.configure("Glide.Window.TFrame", background=p.window)
    style.configure("TLabelframe",         background=p.acetate)
    style.configure("TLabelframe.Label",   background=p.acetate, foreground=p.ink, font=caption_bold)

    style.configure("TLabel",                    background=p.acetate, foreground=p.ink,        font=body_font)
    style.configure("Glide.TLabel",              background=p.acetate, foreground=p.ink,        font=body_font)
    style.configure("Glide.Caption.TLabel",      background=p.acetate, foreground=p.ink,        font=caption_font)
    style.configure("Glide.Caption.Bold.TLabel", background=p.acetate, foreground=p.ink,        font=caption_bold)
    style.configure("Glide.Muted.TLabel",        background=p.acetate, foreground=p.muted_ink,  font=caption_font)
    style.configure("Glide.Section.TLabel",      background=p.acetate, foreground=p.ink,        font=section_font)
    style.configure("Glide.Title.TLabel",        background=p.paper,   foreground=p.view_title, font=title_font)
    style.configure("Glide.Paper.TLabel",        background=p.paper,   foreground=p.ink,        font=body_font)

    style.configure(
        "Glide.TButton",
        background=p.paper, foreground=p.ink,
        font=body_bold,
        padding=(btn_padx, btn_pady),
        relief="flat", borderwidth=0,
        anchor="w",
    )
    style.map(
        "Glide.TButton",
        background=[("disabled", p.acetate), ("pressed", p.ink), ("active", p.hover)],
        foreground=[("disabled", p.disabled_ink), ("pressed", p.acetate), ("active", p.ink)],
        relief=[("pressed", "flat")],
    )

    style.configure(
        "Glide.New.TButton",
        background=p.action_new_bg, foreground=p.action_new_fg,
        font=body_bold,
        padding=(btn_padx, btn_pady),
        relief="flat", borderwidth=0,
        anchor="w",
    )
    style.map(
        "Glide.New.TButton",
        background=[("disabled", p.acetate), ("pressed", p.ink), ("active", p.hover)],
        foreground=[("disabled", p.disabled_ink), ("pressed", p.acetate), ("active", p.ink)],
    )

    style.configure(
        "Glide.Header.TButton",
        background=p.paper, foreground=p.ink,
        font=caption_bold,
        padding=(SPACING[10], SPACING[8]),
        relief="flat", borderwidth=0,
    )
    style.map(
        "Glide.Header.TButton",
        background=[("disabled", p.acetate), ("pressed", p.ink), ("active", p.hover)],
        foreground=[("disabled", p.disabled_ink), ("pressed", p.acetate), ("active", p.ink)],
    )

    style.configure(
        "Glide.TEntry",
        fieldbackground=p.paper,
        foreground=p.ink,
        insertcolor=p.ink,
        selectbackground=p.selection,
        selectforeground=p.selection_text,
        bordercolor=p.input_border,
        lightcolor=p.input_border,
        darkcolor=p.input_border,
        relief="flat",
        borderwidth=1,
        padding=(field_padx, field_pady),
        font=body_font,
    )
    style.map(
        "Glide.TEntry",
        fieldbackground=[("readonly", p.acetate), ("disabled", p.acetate)],
        foreground=[("disabled", p.disabled_ink)],
        bordercolor=[("focus", p.brand_blue), ("invalid", p.brand_red)],
        lightcolor=[("focus", p.brand_blue)],
        darkcolor=[("focus", p.brand_blue)],
    )

    for sname in ("Glide.TCheckbutton", "TCheckbutton"):
        style.configure(
            sname,
            background=p.acetate, foreground=p.ink,
            font=body_font,
            focuscolor=p.brand_blue,
            indicatorcolor=p.paper,
            indicatorrelief="flat",
        )
        style.map(
            sname,
            background=[("active", p.acetate)],
            foreground=[("disabled", p.disabled_ink)],
            indicatorcolor=[("selected", p.action_new_bg), ("pressed", p.hover)],
        )

    for sname in ("Glide.TRadiobutton", "TRadiobutton"):
        style.configure(
            sname,
            background=p.acetate, foreground=p.ink,
            font=body_font,
            focuscolor=p.brand_blue,
            indicatorcolor=p.paper,
            indicatorrelief="flat",
        )
        style.map(
            sname,
            background=[("active", p.acetate)],
            foreground=[("disabled", p.disabled_ink)],
            indicatorcolor=[("selected", p.action_new_bg), ("pressed", p.hover)],
        )

    for orient in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        style.configure(
            orient,
            background=p.acetate,
            troughcolor=p.line,
            arrowcolor=p.muted_ink,
            bordercolor=p.acetate,
            lightcolor=p.acetate,
            darkcolor=p.acetate,
            relief="flat",
        )
        style.map(
            orient,
            background=[("active", p.muted_ink), ("pressed", p.ink)],
            arrowcolor=[("active", p.ink)],
        )

    style.configure("TSeparator",       background=p.line)
    style.configure("Glide.TSeparator", background=p.line)

    style.configure(
        "Glide.TCombobox",
        fieldbackground=p.paper,
        foreground=p.ink,
        selectbackground=p.selection,
        selectforeground=p.selection_text,
        arrowcolor=p.ink,
        bordercolor=p.input_border,
        lightcolor=p.input_border,
        darkcolor=p.input_border,
        relief="flat",
        padding=(field_padx, field_pady),
        font=body_font,
    )
    style.map(
        "Glide.TCombobox",
        fieldbackground=[("readonly", p.paper)],
        foreground=[("disabled", p.disabled_ink)],
        bordercolor=[("focus", p.brand_blue)],
    )


# ---------------------------------------------------------------------------
# OptionMenu & Listbox theme helpers
# ---------------------------------------------------------------------------

def apply_optionmenu_theme(menu_widget: "tk.Widget", palette: "ThemePalette") -> None:
    """Apply Glide palette to a ``tk.OptionMenu`` and its dropdown menu."""
    p = palette
    menu_widget.configure(
        background=p.paper,
        foreground=p.ink,
        activebackground=p.hover,
        activeforeground=p.ink,
        highlightthickness=1,
        highlightbackground=p.input_border,
        highlightcolor=p.brand_blue,
        relief="solid",
        borderwidth=1,
        font=("TkDefaultFont", FONT_SIZES["body"]),
    )
    try:
        dropdown = menu_widget["menu"]
        dropdown.configure(
            background=p.paper,
            foreground=p.ink,
            activebackground=p.selection,
            activeforeground=p.selection_text,
            font=("TkDefaultFont", FONT_SIZES["body"]),
            borderwidth=1,
            relief="solid",
        )
    except (tk.TclError, KeyError):
        pass


def apply_listbox_theme(listbox: "tk.Widget", palette: "ThemePalette") -> None:
    """Apply Glide palette to a ``tk.Listbox`` or ``GlideListbox``."""
    p = palette
    listbox.configure(
        background=p.paper,
        foreground=p.ink,
        selectbackground=p.selection,
        selectforeground=p.selection_text,
        highlightthickness=1,
        highlightbackground=p.input_border,
        highlightcolor=p.brand_blue,
        relief="flat",
        borderwidth=0,
        font=("TkDefaultFont", FONT_SIZES["body"]),
        activestyle="none",
    )


def _resolve_carrier_bg(master: tk.Misc, explicit: str | None = None, fallback: str = WINDOW) -> str:
    if explicit:
        return explicit
    try:
        return str(master.cget("background"))
    except Exception:
        try:
            return str(master.cget("bg"))
        except Exception:
            return fallback


# ---------------------------------------------------------------------------
# RoundedSurfaceCard – Glide carrier-card surface with true rounded corners
# ---------------------------------------------------------------------------

class RoundedSurfaceCard(tk.Canvas):
    """Glide carrier-card container drawing smooth rounded polygons via glide_shell."""

    def __init__(
        self,
        master: tk.Misc,
        bg_color: str | None = None,
        fill_color: str = ACETATE,
        outline_color: str | None = None,
        radius: int = RADII["card"],
        padding: int = 4,
        inner_pad_x: int | None = None,
        inner_pad_y: int | None = None,
        width: int | None = None,
        height: int | None = None,
        auto_height: bool = False,
        **kwargs,
    ) -> None:
        carrier = _resolve_carrier_bg(master, bg_color, WINDOW)
        opts: dict = {
            "bg": carrier,
            "highlightthickness": 0,
            "bd": 0,
        }
        if width is not None:
            opts["width"] = width
        if height is not None:
            opts["height"] = height
        opts.update(kwargs)
        super().__init__(master, **opts)

        self.bg_color = carrier
        self.fill_color = fill_color
        self.outline_color = outline_color or LINE
        self.radius = max(0, int(radius))
        self.inner_pad_x = int(padding if inner_pad_x is None else inner_pad_x)
        self.inner_pad_y = int(padding if inner_pad_y is None else inner_pad_y)
        self.auto_height = auto_height
        self._auto_height_value: int | None = None
        self._draw_pending: str | None = None

        self.inner = tk.Frame(self, background=self.fill_color, bd=0, highlightthickness=0)
        self._window_id = self.create_window(
            self.inner_pad_x,
            self.inner_pad_y,
            anchor="nw",
            window=self.inner,
        )

        custom_controls.bind_resize(self, self._on_configure)
        if self.auto_height:
            self.inner.bind("<Configure>", self._sync_auto_height)
        self._draw()

    def set_theme(
        self,
        bg_color: str,
        fill_color: str,
        outline_color: str | None = None,
        radius: int | None = None,
    ) -> None:
        """Update outer carrier background, inner card fill, outline and corner radius."""
        self.bg_color = bg_color
        self.fill_color = fill_color
        self.outline_color = outline_color or fill_color
        if radius is not None:
            self.radius = max(0, int(radius))
        try:
            super().configure(bg=self.bg_color)
            self.inner.configure(background=self.fill_color)
        except tk.TclError:
            pass
        self._draw()

    def _sync_auto_height(self, _event: tk.Event | None = None) -> None:
        if not self.auto_height:
            return
        try:
            needed = max(1, self.inner.winfo_reqheight() + self.inner_pad_y * 2)
        except tk.TclError:
            return
        if needed == self._auto_height_value:
            return
        self._auto_height_value = needed
        try:
            super().configure(height=needed)
        except tk.TclError:
            pass

    def _on_configure(self, _event: tk.Event | None = None) -> None:
        pad_x = self.inner_pad_x
        pad_y = self.inner_pad_y
        w = max(self.winfo_width(), pad_x * 2 + 2)
        h = max(self.winfo_height(), pad_y * 2 + 2)
        try:
            self.coords(self._window_id, pad_x, pad_y)
            if self.auto_height:
                self.itemconfigure(self._window_id, width=max(1, w - pad_x * 2), height=0)
                self._sync_auto_height()
            else:
                self.itemconfigure(
                    self._window_id,
                    width=max(1, w - pad_x * 2),
                    height=max(1, h - pad_y * 2),
                )
        except tk.TclError:
            pass
        self._schedule_draw()

    def _schedule_draw(self) -> None:
        if self._draw_pending is None:
            try:
                scope = window_lifetime.scope_for(self)
                self._draw_pending = scope.after_idle(self._draw_scheduled)
            except Exception:
                self._draw()

    def _draw_scheduled(self) -> None:
        self._draw_pending = None
        self._draw()

    def _draw(self) -> None:
        try:
            if not self.winfo_exists():
                return
            self.delete("surface")
            w = max(self.winfo_width(), 4)
            h = max(self.winfo_height(), 4)
            pad = 1
            r = min(self.radius, (w - 2) // 2, (h - 2) // 2)
            if r > 0 and w > r * 2 + 2 and h > r * 2 + 2:
                points = custom_controls.rounded_rect_points(
                    pad, pad, w - pad, h - pad, r
                )
                self.create_polygon(
                    points,
                    smooth=True,
                    splinesteps=24,
                    fill=self.fill_color,
                    outline=self.outline_color,
                    width=1,
                    tags=("surface",),
                )
            else:
                self.create_rectangle(
                    pad, pad, w - pad, h - pad,
                    fill=self.fill_color,
                    outline=self.outline_color,
                    width=1,
                    tags=("surface",),
                )
            self.tag_lower("surface")
        except tk.TclError:
            pass

    def cget(self, key: str) -> object:
        if key in ("bg", "background"):
            return self.fill_color
        if key in ("carrier_bg", "canvas_bg"):
            return self.bg_color
        if key == "radius":
            return self.radius
        return super().cget(key)

    def configure(self, cnf=None, **kwargs):
        opts = dict(cnf or {}, **kwargs)
        if not opts:
            return super().configure()
        if "bg" in opts or "background" in opts:
            new_bg = opts.pop("bg", opts.pop("background", None))
            if new_bg:
                self.fill_color = str(new_bg)
                try:
                    self.inner.configure(background=self.fill_color)
                except tk.TclError:
                    pass
                self._schedule_draw()
        if "carrier_bg" in opts:
            self.bg_color = str(opts.pop("carrier_bg"))
            try:
                super().configure(bg=self.bg_color)
            except tk.TclError:
                pass
            self._schedule_draw()
        if "outline_color" in opts:
            self.outline_color = str(opts.pop("outline_color"))
            self._schedule_draw()
        if "radius" in opts:
            self.radius = max(0, int(opts.pop("radius")))
            self._schedule_draw()
        if opts:
            super().configure(**opts)
            self._schedule_draw()
        return None

    config = configure

    def pack_propagate(self, flag: bool = True) -> None:
        if hasattr(self, "inner"):
            self.inner.pack_propagate(flag)
        super().pack_propagate(flag)

    def grid_propagate(self, flag: bool = True) -> None:
        if hasattr(self, "inner"):
            self.inner.grid_propagate(flag)
        super().grid_propagate(flag)

    def columnconfigure(self, index: int, **kwargs) -> None:
        if hasattr(self, "inner"):
            self.inner.columnconfigure(index, **kwargs)
        else:
            super().columnconfigure(index, **kwargs)

    def rowconfigure(self, index: int, **kwargs) -> None:
        if hasattr(self, "inner"):
            self.inner.rowconfigure(index, **kwargs)
        else:
            super().rowconfigure(index, **kwargs)


# ---------------------------------------------------------------------------
# RoundedButton – Canvas-based button with true Glide-radius rounding &
# seamless parent carrier background blending
# ---------------------------------------------------------------------------

def _measure_text_width(font_val: object, text: str, widget: tk.Misc) -> int:
    try:
        return int(widget.tk.call("font", "measure", font_val, text))
    except Exception:
        return max(1, len(text)) * 8


class RoundedButton(tk.Canvas):
    """Canvas button with true Glide rounded corners & carrier-background blending.

    Drop-in replacement for ``tk.Button`` supporting hover, press, focus ring,
    disabled state, dynamic corner radius and full tk.Button API compatibility.
    """

    _RADIUS = RADII["field"]

    def __init__(self, master: tk.Misc, name: str | None = None, **kwargs):
        self._text        = str(kwargs.pop("text", ""))
        self._command     = kwargs.pop("command", None)
        self._bg          = kwargs.pop("background", kwargs.pop("bg", PAPER))
        self._fg          = kwargs.pop("foreground", kwargs.pop("fg", INK))
        self._active_bg   = kwargs.pop("activebackground", INK)
        self._active_fg   = kwargs.pop("activeforeground", PAPER)
        self._disabled_fg = kwargs.pop("disabledforeground", DISABLED_INK)
        self._hover_bg    = kwargs.pop("hover_bg", HOVER)
        self._border_color = kwargs.pop("border_color", kwargs.pop("highlightbackground", LINE))
        self._focus_color  = kwargs.pop("focus_color", kwargs.pop("highlightcolor", BRAND_BLUE))
        self._carrier_bg   = _resolve_carrier_bg(master, kwargs.pop("carrier_bg", kwargs.pop("bg_color", None)), ACETATE)
        self._state       = str(kwargs.pop("state", "normal"))
        self._padx        = int(kwargs.pop("padx", SPACING[10]))
        self._pady        = int(kwargs.pop("pady", SPACING[7]))
        self._font        = kwargs.pop("font", ("TkDefaultFont", FONT_SIZES["body"], "bold"))
        self._wraplength  = int(kwargs.pop("wraplength", 0))
        self._anchor      = str(kwargs.pop("anchor", "center"))
        self._justify     = str(kwargs.pop("justify", "center"))
        self._radius      = max(0, int(kwargs.pop("radius", self._RADIUS)))
        self._hovered     = False
        self._focused     = False
        self._pressing    = False

        cursor    = kwargs.pop("cursor", "hand2")
        takefocus = kwargs.pop("takefocus", 1)
        kwargs.pop("highlightthickness", None)
        kwargs.pop("relief", None)
        kwargs.pop("borderwidth", None)
        kwargs.pop("bd", None)

        explicit_width = kwargs.pop("width", None)
        self._auto_width = explicit_width is None
        self._explicit_width = explicit_width

        explicit_height = kwargs.pop("height", None)
        self._auto_height = explicit_height is None

        # Discard unrecognised tk.Button kwargs cleanly
        for _k in list(kwargs):
            kwargs.pop(_k)

        init_w = int(explicit_width) if explicit_width is not None else 80
        init_h = int(explicit_height) if explicit_height is not None else self._compute_height()

        init_kw: dict = {
            "bg": self._carrier_bg,
            "bd": 0,
            "relief": "flat",
            "width": init_w,
            "height": init_h,
            "highlightthickness": 0,
            "cursor": cursor if self._state != "disabled" else "",
            "takefocus": takefocus,
        }
        if name is not None:
            init_kw["name"] = name

        super().__init__(master, **init_kw)
        if self._auto_width:
            self._sync_auto_width()

        self.bind("<Button-1>",        self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>",           self._on_enter)
        self.bind("<Leave>",           self._on_leave)
        self.bind("<FocusIn>",         self._on_focus_in)
        self.bind("<FocusOut>",        self._on_focus_out)
        self.bind("<Return>",          lambda _e: self.invoke())
        self.bind("<KP_Enter>",        lambda _e: self.invoke())
        self.bind("<space>",           lambda _e: self.invoke())
        self.bind("<Configure>",       lambda _e: self._render())
        self._render()

    def _font_size_px(self) -> int:
        if isinstance(self._font, (list, tuple)) and len(self._font) > 1:
            try:
                return max(8, abs(int(self._font[1])))
            except (TypeError, ValueError):
                pass
        return FONT_SIZES["body"]

    def _compute_height(self, lines: int = 1) -> int:
        line_h = self._font_size_px() * 2
        try:
            font_obj = tkfont.Font(root=self.winfo_toplevel(), font=self._font)
            line_h = max(int(font_obj.metrics("linespace")) + 4, line_h // 2 + 8)
        except Exception:
            pass
        return max(24, lines * line_h + self._pady * 2)

    def _sync_auto_width(self) -> None:
        if not self._auto_width:
            return
        tw = _measure_text_width(self._font, self._text, self)
        if self._wraplength > 0:
            tw = min(tw, self._wraplength)
        needed = max(28, tw + self._padx * 2 + 8)
        try:
            super().configure(width=needed)
        except tk.TclError:
            pass

    def configure(self, cnf=None, **kwargs):
        opts = dict(cnf or {}, **kwargs)
        if not opts:
            return super().configure()
        changed = False
        size_dirty = False
        for key, attr in (
            ("text", "_text"), ("command", "_command"),
            ("state", "_state"),
            ("padx", "_padx"), ("pady", "_pady"),
            ("anchor", "_anchor"), ("justify", "_justify"),
            ("wraplength", "_wraplength"),
        ):
            if key in opts:
                setattr(self, attr, opts.pop(key))
                changed = True
                if key in ("text", "padx", "pady", "wraplength"):
                    size_dirty = True
        for key, attr in (
            ("background", "_bg"), ("bg", "_bg"),
            ("foreground", "_fg"), ("fg", "_fg"),
            ("activebackground", "_active_bg"),
            ("activeforeground", "_active_fg"),
            ("disabledforeground", "_disabled_fg"),
            ("hover_bg", "_hover_bg"),
            ("border_color", "_border_color"),
            ("highlightbackground", "_border_color"),
            ("focus_color", "_focus_color"),
            ("highlightcolor", "_focus_color"),
            ("carrier_bg", "_carrier_bg"),
            ("bg_color", "_carrier_bg"),
        ):
            if key in opts:
                setattr(self, attr, opts.pop(key))
                changed = True
        if "radius" in opts:
            self._radius = max(0, int(opts.pop("radius")))
            changed = True
        if "font" in opts:
            self._font = opts.pop("font")
            changed = True
            size_dirty = True
        opts.pop("highlightthickness", None)
        opts.pop("relief", None)
        opts.pop("borderwidth", None)
        opts.pop("bd", None)

        if opts:
            super().configure(**opts)
            changed = True
        if size_dirty:
            self._sync_auto_width()
            if self._auto_height:
                try:
                    super().configure(height=self._compute_height())
                except tk.TclError:
                    pass
        if changed:
            self._render()
        return None

    config = configure

    def cget(self, key):
        if key in ("background", "bg"):
            if self._pressing:
                return self._active_bg
            if self._hovered:
                return self._hover_bg
            return self._bg
        if key in ("carrier_bg", "canvas_bg"):
            return self._carrier_bg
        _map = {
            "text": "_text", "command": "_command", "state": "_state",
            "foreground": "_fg", "fg": "_fg",
            "activebackground": "_active_bg", "activeforeground": "_active_fg",
            "disabledforeground": "_disabled_fg",
            "hover_bg": "_hover_bg",
            "font": "_font",
            "padx": "_padx", "pady": "_pady",
            "wraplength": "_wraplength", "anchor": "_anchor",
            "radius": "_radius",
        }
        if key in _map:
            return getattr(self, _map[key])
        return super().cget(key)

    def __getitem__(self, key):
        return self.cget(key)

    def __setitem__(self, key, value):
        self.configure(**{key: value})

    def invoke(self):
        if self._state == "disabled":
            return "break"
        if callable(self._command):
            self._command()
        return "break"

    def state(self, statespec=None):
        """ttk-compatible state accessor."""
        if statespec is None:
            return ("disabled",) if self._state == "disabled" else ()
        if "disabled" in statespec:
            self.configure(state="disabled")
        elif "!disabled" in statespec:
            self.configure(state="normal")

    def _on_press(self, _event):
        if self._state == "disabled":
            return
        self._pressing = True
        self._render()

    def _on_release(self, event):
        if self._state == "disabled":
            return
        was_pressing = self._pressing
        self._pressing = False
        self._render()
        if was_pressing:
            try:
                x, y = event.x, event.y
                w, h = self.winfo_width(), self.winfo_height()
                if 0 <= x <= w and 0 <= y <= h:
                    self.invoke()
            except tk.TclError:
                pass

    def _on_enter(self, _event):
        if self._state != "disabled":
            self._hovered = True
            self._render()
            try:
                self.event_generate("<<ButtonHover>>", data="enter")
            except tk.TclError:
                pass

    def _on_leave(self, _event):
        self._hovered = False
        self._pressing = False
        self._render()
        try:
            self.event_generate("<<ButtonHover>>", data="leave")
        except tk.TclError:
            pass

    def _on_focus_in(self, _event):
        self._focused = True
        self._render()

    def _on_focus_out(self, _event):
        self._focused = False
        self._render()

    def _render(self):
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        try:
            super().configure(bg=self._carrier_bg)
        except tk.TclError:
            return

        self.delete("all")
        req_w = int(super().cget("width")) if self._auto_width else 80
        req_h = int(super().cget("height")) if not self._auto_height else self._compute_height()
        w = self.winfo_width() if self.winfo_width() > 1 else req_w
        h = self.winfo_height() if self.winfo_height() > 1 else req_h
        w = max(4, w)
        h = max(4, h)

        disabled = self._state == "disabled"
        if disabled:
            fill = self._bg
        elif self._pressing:
            fill = self._active_bg
        elif self._hovered:
            fill = self._hover_bg
        else:
            fill = self._bg

        outline = self._focus_color if self._focused else self._border_color
        outline_w = 2 if self._focused else 1

        r = min(self._radius, (w - 2) // 2, (h - 2) // 2)
        if r > 0 and w > r * 2 + 2 and h > r * 2 + 2:
            self.create_polygon(
                custom_controls.rounded_rect_points(1, 1, w - 1, h - 1, r),
                smooth=True, splinesteps=16,
                fill=fill, outline=outline, width=outline_w,
            )
        else:
            self.create_rectangle(
                1, 1, w - 1, h - 1,
                fill=fill, outline=outline, width=outline_w,
            )

        fg = self._disabled_fg if disabled else (self._active_fg if self._pressing else self._fg)
        if self._anchor in ("w", "nw", "sw"):
            tx = self._padx + 2
        elif self._anchor in ("e", "ne", "se"):
            tx = w - self._padx - 2
        else:
            tx = w // 2

        text_id = self.create_text(
            tx, h // 2,
            text=self._text,
            fill=fg,
            font=self._font,
            anchor=self._anchor if self._anchor in ("w", "e", "n", "s", "nw", "ne", "sw", "se", "center") else "center",
            justify=self._justify,
            width=self._wraplength if self._wraplength > 0 else 0,
        )

        # Adapt vertical height if wrapped text requires more vertical space
        if self._auto_height and self._wraplength > 0:
            bbox = self.bbox(text_id)
            if bbox is not None:
                text_h = bbox[3] - bbox[1]
                needed_h = max(self._compute_height(), text_h + self._pady * 2 + 4)
                try:
                    cur_req_h = int(super().cget("height"))
                    if abs(needed_h - cur_req_h) > 1:
                        super().configure(height=needed_h)
                        self.coords(text_id, tx, needed_h // 2)
                except tk.TclError:
                    pass
