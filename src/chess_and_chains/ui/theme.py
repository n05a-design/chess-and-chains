"""Semantic colors and Connected System Light/Dark theme resolution via Glide Shell."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import font as tkfont
from types import MappingProxyType

from glide_shell import custom_controls, system_appearance, text_fit

CHROME_YELLOW = "#F4C400"
BRAND_BLUE = "#2447D8"
BRAND_RED = "#B12729"
WINDOW = "#EFE8D8"
INK = "#171920"
PAPER = "#FAF6EC"
ACETATE = "#FFFCF4"
SHADOW = "#CFC4B0"
SQUARE_LIGHT = "#ECE2CA"
SQUARE_DARK = "#8D7862"
LAST_MOVE = "#FAF6EC"
TAB_IDLE = "#EFE8D8"
MUTED_INK = "#514B44"
FOCUS_INK = "#171920"
DISABLED_INK = "#6B645C"
LEGAL_MARK = "#171920"
ATLAS_LINE = "#8D7862"

SPACING = MappingProxyType(
    {value: value for value in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 18, 22, 24, 28, 30)}
)
RADII = MappingProxyType({"card": 18, "field": 16})
FONT_SIZES = {
    "caption": 10,
    "body": 11,
    "section": 16,
    "title": 22,
}

# Portable Glide layout constants & breakpoints (adapted to Connected System desktop shell)
TITLE_MAX_CHARS = 40
BUTTON_TEXT_MAX_CHARS = 24
NORMAL_MIN = (860, 700)
COMPACT_MIN = (480, 560)
COMPACT_DEFAULT_WIDTH = 480
COMPACT_DEFAULT_HEIGHT = 760
SIDEBAR_WIDTH = 328
SIDEBAR_RAIL_WIDTH = 64
SIDEBAR_AUTO_NARROW_WIDTH = 760
SIDEBAR_AUTO_RESTORE_WIDTH = 860
HEADER_DENSITY_FULL = 1120
HEADER_DENSITY_COMPACT = 900
HEADER_CAPTURE_MIN_WIDTH = 640
HEIGHT_DENSITY_FULL = 850
HEIGHT_DENSITY_COMPACT = 780

CVD_PALETTE = MappingProxyType({
    "orange": "#E69F00",
    "sky": "#56B4E9",
    "green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
})

BUTTON_ROLES = {
    "neutral": (PAPER, INK),
    "new": (CHROME_YELLOW, INK),
}

THEME_MODES = ("light", "dark", "system")

EXTENDED_THEME_MODES = (
    "light",
    "dark",
    "contrast-light",
    "contrast-dark",
    "minimal-light",
    "minimal-dark",
    "system",
)

THEME_PAIRS = {
    "light": "dark",
    "dark": "light",
    "contrast-light": "contrast-dark",
    "contrast-dark": "contrast-light",
    "minimal-light": "minimal-dark",
    "minimal-dark": "minimal-light",
    "w06-provisional": "dark",
}


def clip_button_text(text: str, limit: int = BUTTON_TEXT_MAX_CHARS) -> str:
    """Clip button labels to the Glide 24-character guideline without altering source strings."""
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
    """Return the paired light/dark variant keeping contrast/minimal family intact."""
    normalized = (theme_id or "light").strip().lower()
    return THEME_PAIRS.get(normalized, "dark")


@dataclass(frozen=True, slots=True)
class ThemePalette:
    """Semantic Connected System palette aligned with Glide design roles."""

    mode: str
    window: str
    paper: str
    acetate: str
    shadow: str
    ink: str
    muted_ink: str
    focus_ink: str
    disabled_ink: str
    tab_idle: str
    brand_blue: str
    chrome_yellow: str
    brand_red: str
    square_light: str
    square_dark: str
    last_move: str
    legal_mark: str
    atlas_line: str
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

    def button_colors(self, role: str) -> tuple[str, str]:
        if role == "new":
            return self.action_new_bg, self.action_new_fg
        if role == "neutral":
            return self.paper, self.ink
        raise ValueError(f"Unknown button role: {role}")


LIGHT_THEME = ThemePalette(
    mode="light",
    window=WINDOW,
    paper=PAPER,
    acetate=ACETATE,
    shadow=SHADOW,
    ink=INK,
    muted_ink=MUTED_INK,
    focus_ink=FOCUS_INK,
    disabled_ink=DISABLED_INK,
    tab_idle=TAB_IDLE,
    brand_blue=BRAND_BLUE,
    chrome_yellow=CHROME_YELLOW,
    brand_red=BRAND_RED,
    square_light=SQUARE_LIGHT,
    square_dark=SQUARE_DARK,
    last_move=LAST_MOVE,
    legal_mark=LEGAL_MARK,
    atlas_line=ATLAS_LINE,
    action_new_bg=CHROME_YELLOW,
    action_new_fg=INK,
    input_border="#C9BFA8",
    line="#DCD3BE",
    hover="#E7DEC9",
    selection=BRAND_BLUE,
    selection_text="#FFFFFF",
    view_title=INK,
    confirm="#166233",
    delete=BRAND_RED,
)

DARK_THEME = ThemePalette(
    mode="dark",
    window="#14161D",
    paper="#1D202A",
    acetate="#232733",
    shadow="#0C0D12",
    ink="#F5F2EA",
    muted_ink="#C4BEB4",
    focus_ink=CHROME_YELLOW,
    disabled_ink="#9E988E",
    tab_idle="#1D202A",
    brand_blue="#4D6FFF",
    chrome_yellow=CHROME_YELLOW,
    brand_red="#E35D5F",
    square_light="#C6B99E",
    square_dark="#6B5B4A",
    last_move="#3E4863",
    legal_mark="#F5F2EA",
    atlas_line="#8D7862",
    action_new_bg=CHROME_YELLOW,
    action_new_fg=INK,
    input_border="#363B4A",
    line="#2C3140",
    hover="#243A55",
    selection=BRAND_BLUE,
    selection_text="#FFFFFF",
    view_title="#F5F2EA",
    confirm="#30D158",
    delete="#FF8082",
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
    view_title="#101014",
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
    view_title="#FFFFFF",
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
    brand_blue="#3A3A3A",
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
    view_title="#171717",
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
    view_title="#F4F4F4",
    confirm="#E4E4E4",
    delete="#F4F4F4",
)

THEMES: dict[str, ThemePalette] = {
    "light": LIGHT_THEME,
    "dark": DARK_THEME,
    "contrast-light": CONTRAST_LIGHT_THEME,
    "contrast-dark": CONTRAST_DARK_THEME,
    "minimal-light": MINIMAL_LIGHT_THEME,
    "minimal-dark": MINIMAL_DARK_THEME,
    "w06-provisional": LIGHT_THEME,
}


def _relative_luminance(hex_color: str) -> float:
    raw = hex_color.lstrip("#")
    if len(raw) != 6:
        raise ValueError(f"Expected #RRGGBB hex color, got {hex_color!r}")
    channels = []
    for offset in (0, 2, 4):
        srgb = int(raw[offset:offset + 2], 16) / 255.0
        channels.append(srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(foreground: str, background: str) -> float:
    """Return WCAG 2.2 contrast ratio between two #RRGGBB colors."""
    lum_a = _relative_luminance(foreground)
    lum_b = _relative_luminance(background)
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


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
) -> ThemePalette:
    """Resolve explicit or system theme using ``glide_shell.system_appearance``."""
    normalized = (theme_id or "light").strip().lower()
    if normalized == "system":
        dark = detect_system_dark(root) if system_dark is None else system_dark
        return system_appearance.resolve(
            {"light": LIGHT_THEME, "dark": DARK_THEME},
            dark,
            LIGHT_THEME,
        )
    return THEMES.get(normalized, LIGHT_THEME)


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
    """Register Connected System typography providers on ``glide_shell.custom_controls``."""
    custom_controls.set_font_provider(_host_font_provider)
    custom_controls.set_ink_provider(_host_ink_provider)
