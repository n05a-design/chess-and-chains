"""Compact captured piece and material advantage bar for board workspace."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

from ..chess import Color, Piece, PlayerMaterial
from .pieces import OwnerSvgPieces, PieceRenderer
from .theme import LIGHT_THEME, ThemePalette, contrast_ratio, font_spec

MINIATURE_SIZE = 18
BAR_HEIGHT = 24


def _draw_pill(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float,
    *,
    fill: str,
    outline: str = "",
    width: float = 1.0,
    tags: tuple[str, ...] = (),
) -> None:
    """Draw a smooth rounded pill rectangle on a Canvas."""
    r = min(radius, (y2 - y1) / 2, (x2 - x1) / 2)
    if r <= 1:
        canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=width, tags=tags)
        return
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    canvas.create_polygon(points, smooth=True, fill=fill, outline=outline, width=width, tags=tags)


class CapturedMaterialBar(tk.Canvas):
    """Compact material bar displaying captured opponent pieces and +N advantage score."""

    def __init__(
        self,
        parent: tk.Widget,
        player_color: Color,
        translator: Callable[..., str],
        *,
        piece_renderer: PieceRenderer | None = None,
        theme: ThemePalette | None = None,
        font_scale_choice: str = "standard",
        font_weight_choice: str = "standard",
        weight_choice: str | None = None,
    ) -> None:
        self._theme = theme or LIGHT_THEME
        super().__init__(
            parent,
            height=BAR_HEIGHT,
            background=self._theme.acetate,
            borderwidth=0,
            highlightthickness=0,
            takefocus=False,
        )
        self._player_color = player_color
        self._t = translator
        self._piece_renderer = piece_renderer or OwnerSvgPieces()
        self._font_scale_choice = font_scale_choice
        self._font_weight_choice = weight_choice or font_weight_choice
        self._material: PlayerMaterial | None = None
        self._images: dict[tuple[str, int], tk.PhotoImage] = {}
        self._tooltip_win: tk.Toplevel | None = None
        self._tooltip_job: str | None = None

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress>", self._on_leave)
        self.bind("<Destroy>", self._on_destroy)

    @property
    def player_color(self) -> Color:
        return self._player_color

    @property
    def material(self) -> PlayerMaterial | None:
        return self._material

    def set_font_preferences(self, scale_choice: str, weight_choice: str) -> None:
        self._font_scale_choice = scale_choice
        self._font_weight_choice = weight_choice
        self._render()

    def set_material(
        self,
        player_color: Color,
        material: PlayerMaterial | None,
        theme: ThemePalette | None = None,
    ) -> None:
        self._player_color = player_color
        self._material = material
        if theme is not None:
            self._theme = theme
        self._render()

    def set_theme(self, theme: ThemePalette) -> None:
        self._theme = theme
        self._render()

    def set_piece_renderer(self, renderer: PieceRenderer) -> None:
        """Swap active piece renderer and clear cached miniature images."""
        self._piece_renderer = renderer
        self._images.clear()
        self._render()

    def set_piece_set(self, piece_set: str) -> None:
        """Switch piece set for captured material bar."""
        if hasattr(self._piece_renderer, "set_piece_set"):
            self._piece_renderer.set_piece_set(piece_set)
        else:
            self._piece_renderer = OwnerSvgPieces(piece_set=piece_set)
        self._images.clear()
        self._render()

    def _get_piece_image(self, piece: Piece, size: int) -> tk.PhotoImage:
        name = f"{piece.color.value}{piece.kind.value.upper()}.svg"
        key = (name, size)
        if key not in self._images:
            if hasattr(self._piece_renderer, "_load_image"):
                self._images[key] = self._piece_renderer._load_image(self, name, size)
            else:
                fallback_renderer = OwnerSvgPieces()
                self._images[key] = fallback_renderer._load_image(self, name, size)
        return self._images[key]

    def _render(self) -> None:
        self.delete("all")
        bg = self._theme.acetate
        self.configure(background=bg)

        center_y = BAR_HEIGHT / 2

        # 1. Player side dot indicator
        # White: white dot with subtle outline; Black: dark dot with subtle outline
        dot_r = 4.0
        dot_x = 10.0
        if self._player_color is Color.WHITE:
            dot_fill = "#FFFFFF"
            dot_stroke = self._theme.line if contrast_ratio(self._theme.line, bg) >= 1.5 else "#707074"
        else:
            dot_fill = self._theme.ink
            dot_stroke = self._theme.line if contrast_ratio(self._theme.line, bg) >= 1.5 else "#707074"

        self.create_oval(
            dot_x - dot_r,
            center_y - dot_r,
            dot_x + dot_r,
            center_y + dot_r,
            fill=dot_fill,
            outline=dot_stroke,
            width=1.0,
            tags=("indicator",),
        )

        # 2. Player side label
        label_font = font_spec("caption", "bold", scale_choice=self._font_scale_choice, weight_choice=self._font_weight_choice)
        label_text = self._t("side.white") if self._player_color is Color.WHITE else self._t("side.black")
        self.create_text(
            dot_x + dot_r + 6,
            center_y,
            text=label_text,
            anchor="w",
            fill=self._theme.muted_ink,
            font=label_font,
            tags=("label",),
        )

        tk_font = tkfont.Font(font=label_font)
        label_w = tk_font.measure(label_text)
        cur_x = dot_x + dot_r + 6 + label_w + 10.0

        if self._material is None:
            return

        # 3. Captured pieces
        size = MINIATURE_SIZE
        half_size = size / 2.0
        count_font = font_spec("caption", "bold", scale_choice=self._font_scale_choice, weight_choice=self._font_weight_choice)
        count_tk_font = tkfont.Font(font=count_font)

        for group in self._material.groups:
            try:
                img = self._get_piece_image(group.piece, size)
                self.create_image(cur_x + half_size, center_y, image=img, tags=("piece",))
                cur_x += size
            except Exception:  # noqa: BLE001
                # If image loading fails, skip piece icon
                pass

            if group.count > 1:
                mult_text = f"×{group.count}"
                mult_w = count_tk_font.measure(mult_text)
                self.create_text(
                    cur_x + 2,
                    center_y,
                    text=mult_text,
                    anchor="w",
                    fill=self._theme.muted_ink,
                    font=count_font,
                    tags=("multiplier",),
                )
                cur_x += mult_w + 4.0
            cur_x += 5.0

        # 4. Material advantage (+N)
        if self._material.advantage is not None and self._material.advantage > 0:
            adv_text = f"+{self._material.advantage}"
            adv_font = font_spec("caption", "bold", scale_choice=self._font_scale_choice, weight_choice=self._font_weight_choice)
            adv_tk_font = tkfont.Font(font=adv_font)
            text_w = adv_tk_font.measure(adv_text)
            pill_h = 16.0
            pill_w = text_w + 10.0
            pill_x1 = cur_x + 3.0
            pill_y1 = center_y - (pill_h / 2.0)
            pill_x2 = pill_x1 + pill_w
            pill_y2 = pill_y1 + pill_h

            # Resolve color with Themenfarbe — require WCAG AA (4.5:1) against actual pill background:
            accent = self._theme.brand_blue
            pill_bg = self._theme.tab_idle
            pill_border = self._theme.line
            cr_accent_on_pill = contrast_ratio(accent, pill_bg)
            if cr_accent_on_pill >= 4.5:
                text_color = accent
            elif contrast_ratio(self._theme.ink, pill_bg) >= 4.5:
                text_color = self._theme.ink
            else:
                # Last resort: pick black or white
                text_color = "#000000" if contrast_ratio("#000000", pill_bg) >= contrast_ratio("#FFFFFF", pill_bg) else "#FFFFFF"

            _draw_pill(
                self,
                pill_x1,
                pill_y1,
                pill_x2,
                pill_y2,
                pill_h / 2.0,
                fill=pill_bg,
                outline=pill_border,
                width=1.0,
                tags=("advantage_pill",),
            )
            self.create_text(
                (pill_x1 + pill_x2) / 2.0,
                center_y,
                text=adv_text,
                anchor="center",
                fill=text_color,
                font=adv_font,
                tags=("advantage_text",),
            )

    # ----- Tooltip -----------------------------------------------------
    def _tooltip_text(self) -> str:
        if self._material and self._material.advantage is not None:
            return self._t("material.advantage_tooltip", points=self._material.advantage)
        return self._t("material.no_advantage_tooltip")

    def _on_enter(self, _event: tk.Event) -> None:
        self._cancel_tooltip()
        self._tooltip_job = self.after(350, self._show_tooltip)

    def _on_leave(self, _event: tk.Event | None = None) -> None:
        self._cancel_tooltip()
        self._hide_tooltip()

    def _on_destroy(self, _event: tk.Event) -> None:
        self._cancel_tooltip()
        self._hide_tooltip()

    def _cancel_tooltip(self) -> None:
        if self._tooltip_job is not None:
            self.after_cancel(self._tooltip_job)
            self._tooltip_job = None

    def _show_tooltip(self) -> None:
        if not self.winfo_exists() or not self.winfo_viewable():
            return
        self._hide_tooltip()
        tip_text = self._tooltip_text()
        if not tip_text:
            return

        x = self.winfo_rootx() + 10
        y = self.winfo_rooty() + BAR_HEIGHT + 2

        tip = tk.Toplevel(self)
        tip.wm_overrideredirect(True)
        tip.configure(background=self._theme.line)

        body = tk.Label(
            tip,
            text=tip_text,
            background=self._theme.paper,
            foreground=self._theme.ink,
            font=font_spec("caption", scale_choice=self._font_scale_choice, weight_choice=self._font_weight_choice),
            padx=8,
            pady=4,
            relief="flat",
        )
        body.pack(padx=1, pady=1)

        tip.wm_geometry(f"+{x}+{y}")
        self._tooltip_win = tip

    def _hide_tooltip(self) -> None:
        if self._tooltip_win is not None:
            try:
                self._tooltip_win.destroy()
            except tk.TclError:
                pass
            self._tooltip_win = None
