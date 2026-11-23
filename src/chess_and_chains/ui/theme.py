"""Semantic colors and Connected System Light/Dark theme resolution via Glide Shell."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import font as tkfont

from glide_shell import custom_controls, system_appearance

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
FONT_SIZES = {
    "caption": 10,
    "body": 11,
    "section": 16,
    "title": 22,
}

BUTTON_ROLES = {
    "neutral": (PAPER, INK),
    "new": (CHROME_YELLOW, INK),
}

THEME_MODES = ("light", "dark", "system")


@dataclass(frozen=True, slots=True)
class ThemePalette:
    """Semantic Connected System palette for light and dark UI modes."""

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
)

THEMES: dict[str, ThemePalette] = {
    "light": LIGHT_THEME,
    "dark": DARK_THEME,
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
