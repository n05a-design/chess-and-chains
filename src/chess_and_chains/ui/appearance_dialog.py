"""Unified Glide Settings & Customization Modal Dialog for Chess & Chains – V.0.3.0.

Provides full parity with the Glide v1.0.2 customization suite:
- Theme (System + 10 canonical Glide themes) with dynamic contextual notes
- Theme color (8 WCAG-compliant semantic choices affecting controls and chessboard)
- Background tint (10 surface/tint choices) with explanatory note
- Corner radius (18 px / 12 px / 6 px / 0 px)
- Font scale (90% / 100% / 115%) & Font weight (Auto / Standard / Bold)
- Interface Language (Deutsch / English)
- Behavior & Sidebar visibility toggles + Engine Settings shortcut
- Uniform 12 px Glide card rhythm and real-time RoundedSurfaceCard preview

SPDX-License-Identifier: MPL-2.0
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import inspect
import tkinter as tk
from typing import Callable

from glide_shell import modal_session
from glide_shell.custom_controls import GlideCheckbutton, GlideRadiobutton, ThemedAutoScrollbar

from ..i18n import Translator
from .theme import (
    ACCENT_CHOICES,
    BACKGROUND_CHOICES,
    FONT_SCALE_CHOICES,
    FONT_WEIGHT_CHOICES,
    RADIUS_CHOICES,
    RADIUS_MAP,
    SPACING,
    THEME_OPTIONS,
    RoundedButton,
    RoundedSurfaceCard,
    ThemePalette,
    apply_window_geometry,
    clip_button_text,
    font_spec,
    resolve_theme,
)

CARD_GAP = SPACING[12]


class AppearanceDialog(tk.Toplevel):
    """Interactive Glide Settings & Appearance customization dialog."""

    def __init__(
        self,
        parent: tk.Misc,
        translator: Translator,
        palette: ThemePalette,
        *,
        theme_id: str = "light",
        background_choice: str = "default",
        accent_choice: str = "accent",
        radius_choice: str = "standard",
        font_scale_choice: str = "standard",
        font_weight_choice: str = "standard",
        animations_enabled: bool = True,
        hints_visible: bool = True,
        locale: str = "de",
        sidebar_visible: bool = True,
        sidebar_narrow: bool = False,
        board_design_choice: str = "standard",
        board_perspective: str = "2d",
        piece_view: str = "front",
        has_custom_board: bool = False,
        on_open_engine: Callable[[], None] | None = None,
        on_apply: Callable[..., None] | None = None,
        modal: bool = True,
    ) -> None:
        super().__init__(parent)
        self.withdraw()
        self._remembered_focus = modal_session.remember_focus(parent, self, parent)
        self._palette = palette
        self._corner_radius = RADIUS_MAP.get(radius_choice, 12)
        self._scale_choice = font_scale_choice
        self._weight_choice = font_weight_choice
        self._has_custom_board = has_custom_board
        self.t = translator
        self.on_apply = on_apply
        self.on_open_engine = on_open_engine

        self.theme_var = tk.StringVar(self, value=theme_id)
        self.bg_var = tk.StringVar(self, value=background_choice)
        self.accent_var = tk.StringVar(self, value=accent_choice)
        self.radius_var = tk.StringVar(self, value=radius_choice)
        self.scale_var = tk.StringVar(self, value=font_scale_choice)
        self.weight_var = tk.StringVar(self, value=font_weight_choice)
        self.animations_var = tk.BooleanVar(self, value=animations_enabled)
        self.hints_var = tk.BooleanVar(self, value=hints_visible)
        self.locale_var = tk.StringVar(self, value=locale)
        self.sidebar_visible_var = tk.BooleanVar(self, value=sidebar_visible)
        self.sidebar_narrow_var = tk.BooleanVar(self, value=sidebar_narrow)
        self.board_design_var = tk.StringVar(self, value=board_design_choice)
        self.perspective_var = tk.StringVar(self, value=board_perspective)
        self.piece_view_var = tk.StringVar(self, value=piece_view)

        self.title(self.t("appearance.dialog.title"))
        self.configure(background=palette.window)
        if parent.winfo_viewable():
            self.transient(parent)
        apply_window_geometry(self, 820, 740, 680, 560)

        self._build_ui()
        self._update_preview()

        self.bind("<Escape>", self._cancel)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.update_idletasks()
        if parent.winfo_viewable():
            try:
                self.tk.call("tk::PlaceWindow", self._w, "widget", parent._w)
            except tk.TclError:
                pass
        self.deiconify()
        self.apply_btn.focus_set()
        if modal:
            modal_session.run_modal(parent, self, focus=self.apply_btn)

    def _theme_note_text(self, theme_id: str) -> str:
        key = f"theme.note.{theme_id.replace('-', '_')}"
        try:
            note = self.t(key)
        except KeyError:
            note = self.t("theme.note.light")
        return f"{note} {self.t('settings.design_note')}"

    def _build_ui(self) -> None:
        p = self._palette
        t = self.t
        r = self._corner_radius

        container = tk.Frame(self, background=p.window, padx=CARD_GAP, pady=CARD_GAP)
        container.pack(fill="both", expand=True)

        self.heading_lbl = tk.Label(
            container,
            text=t("appearance.dialog.heading"),
            background=p.window,
            foreground=p.view_title,
            font=font_spec("section", "bold", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
        )
        self.heading_lbl.pack(fill="x", pady=(0, CARD_GAP))

        # Action bar packed at bottom so controls stay protected (B15)
        action_bar = tk.Frame(container, background=p.window)
        action_bar.pack(side="bottom", fill="x", pady=(CARD_GAP, 0))

        self.cancel_btn = RoundedButton(
            action_bar,
            text=clip_button_text(t("appearance.dialog.cancel")),
            command=self._cancel,
            background=p.paper,
            foreground=p.ink,
            hover_bg=p.hover,
            activebackground=p.ink,
            activeforeground=p.acetate,
            border_color=p.line,
            focus_color=p.focus_ink,
            carrier_bg=p.window,
            radius=r,
            font=font_spec("body", "bold", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
        )
        self.cancel_btn.pack(side="right", padx=(CARD_GAP, 0))

        self.apply_btn = RoundedButton(
            action_bar,
            text=clip_button_text(t("appearance.dialog.apply")),
            command=self._apply,
            background=p.action_new_bg,
            foreground=p.action_new_fg,
            hover_bg=p.hover,
            activebackground=p.ink,
            activeforeground=p.acetate,
            border_color=p.action_new_bg,
            focus_color=p.focus_ink,
            carrier_bg=p.window,
            radius=r,
            font=font_spec("body", "bold", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
        )
        self.apply_btn.pack(side="right")

        # Scrollable options canvas
        scroll_wrap = tk.Frame(container, background=p.window)
        scroll_wrap.pack(fill="both", expand=True)

        self.scroll_canvas = tk.Canvas(scroll_wrap, background=p.window, bd=0, highlightthickness=0)
        self.scrollbar = ThemedAutoScrollbar(
            scroll_wrap,
            bg_color=p.window,
            track_color=p.line,
            thumb_color=p.muted_ink,
            active_thumb_color=p.ink,
            width=12,
        )
        self.scrollbar.set_command(self.scroll_canvas.yview)
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        body = tk.Frame(self.scroll_canvas, background=p.window)
        body_win = self.scroll_canvas.create_window((0, 0), window=body, anchor="nw")
        self.scroll_canvas.bind(
            "<Configure>", lambda e: self.scroll_canvas.itemconfigure(body_win, width=max(1, e.width)),
        )
        body.bind(
            "<Configure>",
            lambda _e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")),
        )
        body.columnconfigure((0, 1), weight=1, uniform="settings_cols")

        left = tk.Frame(body, background=p.window)
        left.grid(row=0, column=0, sticky="new", padx=(0, CARD_GAP // 2))
        right = tk.Frame(body, background=p.window)
        right.grid(row=0, column=1, sticky="new", padx=(CARD_GAP // 2, 0))

        tk.Label(
            left,
            text=t("settings.column.appearance"),
            background=p.window,
            foreground=p.view_title,
            font=font_spec("body", "bold", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
        ).pack(fill="x", pady=(0, SPACING[8]))

        tk.Label(
            right,
            text=t("settings.column.preferences"),
            background=p.window,
            foreground=p.view_title,
            font=font_spec("body", "bold", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
        ).pack(fill="x", pady=(0, SPACING[8]))

        theme_card = self._build_radio_card(left, t("theme.menu"), THEME_OPTIONS, self.theme_var)
        self.design_note_label = tk.Label(
            theme_card.inner,
            text=self._theme_note_text(self.theme_var.get()),
            background=p.paper,
            foreground=p.muted_ink,
            font=font_spec("caption", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
            justify="left",
            wraplength=330,
        )
        self.design_note_label.pack(fill="x", pady=(SPACING[6], 0))

        bg_card = self._build_radio_card(left, t("theme.background.label"), BACKGROUND_CHOICES, self.bg_var)
        tk.Label(
            bg_card.inner,
            text=t("settings.background_note"),
            background=p.paper,
            foreground=p.muted_ink,
            font=font_spec("caption", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
            justify="left",
            wraplength=330,
        ).pack(fill="x", pady=(SPACING[6], 0))

        self._build_radio_card(right, t("theme.accent.label"), ACCENT_CHOICES, self.accent_var)
        self._build_radio_card(
            right, t("theme.radius.label"),
            [(k, lbl) for k, lbl, _ in RADIUS_CHOICES], self.radius_var,
        )
        self._build_radio_card(
            right, t("theme.font_scale.label"),
            [(k, lbl) for k, lbl, _ in FONT_SCALE_CHOICES], self.scale_var,
        )
        self._build_radio_card(right, t("theme.font_weight.label"), FONT_WEIGHT_CHOICES, self.weight_var)
        self._build_radio_card(
            right,
            t("settings.language.label"),
            (("de", "settings.language.de"), ("en", "settings.language.en")),
            self.locale_var,
        )

        board_designs: list[tuple[str, str]] = [
            ("standard", "board.design.standard"),
            ("marble", "board.design.marble"),
        ]
        if self._has_custom_board:
            board_designs.append(("custom", "board.design.custom"))
        self._build_radio_card(left, t("board.design.label"), board_designs, self.board_design_var, on_change=self._on_design_changed)
        self._build_radio_card(
            left,
            t("board.perspective.label"),
            (("2d", "board.perspective.2d"), ("3d", "board.perspective.3d")),
            self.perspective_var,
            on_change=self._on_perspective_changed,
        )
        self._build_radio_card(
            left,
            t("board.piece_view.label"),
            (("front", "board.piece_view.front"), ("top", "board.piece_view.top")),
            self.piece_view_var,
        )

        # Behavior & Sidebar card
        behavior_card = RoundedSurfaceCard(
            right,
            bg_color=p.window,
            fill_color=p.paper,
            outline_color=p.line,
            radius=r,
            padding=SPACING[8],
            auto_height=True,
        )
        behavior_card.pack(fill="x", pady=(0, CARD_GAP))
        tk.Label(
            behavior_card.inner,
            text=t("settings.behavior"),
            background=p.paper,
            foreground=p.muted_ink,
            font=font_spec("caption", "bold", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
        ).pack(fill="x", pady=(0, SPACING[4]))
        for var, key in (
            (self.animations_var, "settings.animations"),
            (self.hints_var, "settings.hints"),
            (self.sidebar_visible_var, "view.sidebar"),
            (self.sidebar_narrow_var, "view.sidebar_narrow"),
        ):
            cb = GlideCheckbutton(
                behavior_card.inner,
                text=t(key),
                variable=var,
                command=self._update_preview,
                bg=p.paper,
                fg=p.ink,
                selectcolor=p.acetate,
                activeforeground=p.ink,
                highlightthickness=0,
                font=font_spec("body", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            )
            cb.pack(fill="x", pady=2)

        if self.on_open_engine is not None:
            self.engine_btn = RoundedButton(
                behavior_card.inner,
                text=clip_button_text(t("settings.engine_button")),
                command=self._open_engine_settings,
                background=p.tab_idle,
                foreground=p.ink,
                hover_bg=p.hover,
                activebackground=p.ink,
                activeforeground=p.acetate,
                border_color=p.line,
                focus_color=p.focus_ink,
                carrier_bg=p.paper,
                radius=min(r, RADIUS_MAP.get("field", 12)),
                font=font_spec("caption", "bold", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            )
            self.engine_btn.pack(anchor="w", pady=(SPACING[6], 0))

        # Live Preview Card in Left Column (matches total height balance & uniform CARD_GAP)
        preview_outer = RoundedSurfaceCard(
            left,
            bg_color=p.window,
            fill_color=p.paper,
            outline_color=p.line,
            radius=r,
            padding=SPACING[8],
            auto_height=True,
        )
        preview_outer.pack(fill="x", pady=(0, CARD_GAP))

        tk.Label(
            preview_outer.inner,
            text=t("appearance.dialog.preview_title"),
            background=p.paper,
            foreground=p.muted_ink,
            font=font_spec("caption", "bold", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
        ).pack(fill="x", pady=(0, SPACING[6]))

        self.preview_window_frame = tk.Frame(preview_outer.inner, background=p.window, padx=SPACING[8], pady=SPACING[8])
        self.preview_window_frame.pack(fill="x")

        self.preview_card = RoundedSurfaceCard(
            self.preview_window_frame,
            bg_color=p.window,
            fill_color=p.acetate,
            outline_color=p.line,
            radius=r,
            padding=SPACING[12],
            auto_height=True,
        )
        self.preview_card.pack(fill="x")

        self.preview_title = tk.Label(
            self.preview_card.inner,
            text=t("appearance.dialog.preview_headline"),
            background=p.acetate,
            foreground=p.ink,
            font=font_spec("body", "bold", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
        )
        self.preview_title.pack(fill="x", pady=(0, SPACING[2]))

        self.preview_sub = tk.Label(
            self.preview_card.inner,
            text=t("appearance.dialog.preview_sub"),
            background=p.acetate,
            foreground=p.muted_ink,
            font=font_spec("caption", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
        )
        self.preview_sub.pack(fill="x", pady=(0, SPACING[8]))

        preview_row = tk.Frame(self.preview_card.inner, background=p.acetate)
        preview_row.pack(fill="x")
        self.preview_row = preview_row

        self.preview_btn = RoundedButton(
            preview_row,
            text=clip_button_text(t("appearance.dialog.preview_button")),
            background=p.action_new_bg,
            foreground=p.action_new_fg,
            hover_bg=p.hover,
            border_color=p.action_new_bg,
            focus_color=p.focus_ink,
            carrier_bg=p.acetate,
            radius=r,
            width=160,
        )
        self.preview_btn.pack(side="left")

        self.preview_board = tk.Canvas(
            preview_row,
            width=44,
            height=44,
            background=p.acetate,
            bd=0,
            highlightthickness=1,
            highlightbackground=p.line,
        )
        self.preview_board.pack(side="right")

    def _on_design_changed(self) -> None:
        if self.board_design_var.get() != "marble" and self.perspective_var.get() == "3d":
            self.perspective_var.set("2d")
        self._update_preview()

    def _on_perspective_changed(self) -> None:
        if self.perspective_var.get() == "3d" and self.board_design_var.get() != "marble":
            self.board_design_var.set("marble")
        self._update_preview()

    def _build_radio_card(
        self,
        parent: tk.Misc,
        title: str,
        options: list[tuple[str, str]] | tuple[tuple[str, str], ...],
        variable: tk.StringVar,
        *,
        on_change: Callable[[], None] | None = None,
    ) -> RoundedSurfaceCard:
        p = self._palette
        t = self.t
        card = RoundedSurfaceCard(
            parent,
            bg_color=p.window,
            fill_color=p.paper,
            outline_color=p.line,
            radius=self._corner_radius,
            padding=SPACING[8],
            auto_height=True,
        )
        card.pack(fill="x", pady=(0, CARD_GAP))
        tk.Label(
            card.inner,
            text=title,
            background=p.paper,
            foreground=p.muted_ink,
            font=font_spec("caption", "bold", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
        ).pack(fill="x", pady=(0, SPACING[4]))
        cmd = on_change or self._update_preview
        for key, text_key in options:
            radio = GlideRadiobutton(
                card.inner,
                text=t(text_key),
                value=key,
                variable=variable,
                command=cmd,
                bg=p.paper,
                fg=p.ink,
                selectcolor=p.acetate,
                activeforeground=p.ink,
                highlightthickness=0,
                font=font_spec("body", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            )
            radio.pack(fill="x", pady=1)
        return card

    def _open_engine_settings(self) -> None:
        callback = self.on_open_engine
        self._cancel()
        if callable(callback):
            callback()

    def _compute_preview(self) -> tuple[ThemePalette, int, str, str]:
        palette = resolve_theme(
            self.theme_var.get(),
            self,
            accent=self.accent_var.get(),
            background=self.bg_var.get(),
        )
        radius = RADIUS_MAP.get(self.radius_var.get(), 12)
        return palette, radius, self.scale_var.get(), self.weight_var.get()

    def _update_preview(self) -> None:
        try:
            pal, radius, scale, weight = self._compute_preview()
            if hasattr(self, "design_note_label"):
                self.design_note_label.configure(text=self._theme_note_text(self.theme_var.get()))
            self.preview_window_frame.configure(background=pal.window)
            self.preview_card.set_theme(
                bg_color=pal.window,
                fill_color=pal.acetate,
                outline_color=pal.line,
                radius=radius,
            )
            self.preview_title.configure(
                background=pal.acetate,
                foreground=pal.ink,
                font=font_spec("body", "bold", scale_choice=scale, weight_choice=weight),
            )
            self.preview_sub.configure(
                background=pal.acetate,
                foreground=pal.muted_ink,
                font=font_spec("caption", scale_choice=scale, weight_choice=weight),
            )
            btn_radius = min(radius, RADIUS_MAP.get("field", 12)) if radius < 14 else radius
            self.preview_btn.configure(
                background=pal.action_new_bg,
                foreground=pal.action_new_fg,
                hover_bg=pal.hover,
                border_color=pal.action_new_bg,
                focus_color=pal.focus_ink,
                carrier_bg=pal.acetate,
                radius=btn_radius,
                font=font_spec("body", "bold", scale_choice=scale, weight_choice=weight),
            )
            if hasattr(self, "preview_row") and hasattr(self, "preview_board"):
                self.preview_row.configure(background=pal.acetate)
                self.preview_board.configure(background=pal.acetate, highlightbackground=pal.line)
                self.preview_board.delete("all")
                for br in range(2):
                    for bc in range(2):
                        sq_col = pal.square_light if (br + bc) % 2 == 0 else pal.square_dark
                        self.preview_board.create_rectangle(
                            bc * 22, br * 22, (bc + 1) * 22, (br + 1) * 22,
                            fill=sq_col, outline=sq_col,
                        )
                self.preview_board.create_oval(
                    11 - 4, 33 - 4, 11 + 4, 33 + 4,
                    fill=pal.paper, outline=pal.legal_mark, width=1,
                )
        except tk.TclError:
            pass

    def _apply(self) -> None:
        if callable(self.on_apply):
            payload = {
                "theme_id": self.theme_var.get(),
                "background_choice": self.bg_var.get(),
                "accent_choice": self.accent_var.get(),
                "radius_choice": self.radius_var.get(),
                "font_scale_choice": self.scale_var.get(),
                "font_weight_choice": self.weight_var.get(),
                "animations_enabled": bool(self.animations_var.get()),
                "hints_visible": bool(self.hints_var.get()),
                "locale": self.locale_var.get(),
                "sidebar_visible": bool(self.sidebar_visible_var.get()),
                "sidebar_narrow": bool(self.sidebar_narrow_var.get()),
                "board_design_choice": self.board_design_var.get(),
                "board_perspective": self.perspective_var.get(),
                "piece_view": self.piece_view_var.get(),
            }
            try:
                sig = inspect.signature(self.on_apply)
                accepts_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
                if not accepts_var_kw:
                    payload = {k: v for k, v in payload.items() if k in sig.parameters}
            except (TypeError, ValueError):
                pass
            self.on_apply(**payload)
        self._cancel()

    def _cancel(self, _event: tk.Event | None = None) -> str:
        if not getattr(self, modal_session.ACTIVE_ATTRIBUTE, False):
            modal_session.return_focus(self.master, self, self._remembered_focus)
        try:
            self.destroy()
        except tk.TclError:
            pass
        return "break"
