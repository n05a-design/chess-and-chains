"""Appearance & Glide Customization Modal Dialog for Chess & Chains – V.0.3.0.

Provides the full Glide v1.0.2 customization suite:
- Theme (System + 10 canonical Glide themes)
- Accent color (8 WCAG-compliant semantic choices)
- Background tint (10 surface/tint choices)
- Corner radius (18 px / 12 px / 6 px / 0 px)
- Font scale (90% / 100% / 115%)
- Font weight (Auto / Standard / Bold)
- Animations & Hints toggles
- Real-time live preview using RoundedSurfaceCard and RoundedButton

SPDX-License-Identifier: MPL-2.0
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import tkinter as tk
from typing import Callable

from glide_shell import modal_session
from glide_shell.custom_controls import GlideCheckbutton, GlideRadiobutton, ThemedAutoScrollbar

from ..i18n import Translator
from .theme import (
    ACCENT_CHOICES,
    BACKGROUND_CHOICES,
    FONT_SCALE_CHOICES,
    FONT_SIZES,
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


class AppearanceDialog(tk.Toplevel):
    """Interactive Glide appearance and geometry customization dialog."""

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
        self.t = translator
        self.on_apply = on_apply

        self.theme_var = tk.StringVar(self, value=theme_id)
        self.bg_var = tk.StringVar(self, value=background_choice)
        self.accent_var = tk.StringVar(self, value=accent_choice)
        self.radius_var = tk.StringVar(self, value=radius_choice)
        self.scale_var = tk.StringVar(self, value=font_scale_choice)
        self.weight_var = tk.StringVar(self, value=font_weight_choice)
        self.animations_var = tk.BooleanVar(self, value=animations_enabled)
        self.hints_var = tk.BooleanVar(self, value=hints_visible)

        self.title(self.t("appearance.dialog.title"))
        self.configure(background=palette.window)
        if parent.winfo_viewable():
            self.transient(parent)
        apply_window_geometry(self, 780, 720, 620, 540)

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

    def _build_ui(self) -> None:
        p = self._palette
        t = self.t
        r = self._corner_radius

        container = tk.Frame(self, background=p.window, padx=SPACING[16], pady=SPACING[14])
        container.pack(fill="both", expand=True)

        self.heading_lbl = tk.Label(
            container,
            text=t("appearance.dialog.heading"),
            background=p.window,
            foreground=p.view_title,
            font=font_spec("section", "bold", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
        )
        self.heading_lbl.pack(fill="x", pady=(0, SPACING[10]))

        # Action bar packed at bottom so controls stay protected (B15)
        action_bar = tk.Frame(container, background=p.window)
        action_bar.pack(side="bottom", fill="x", pady=(SPACING[10], 0))

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
        self.cancel_btn.pack(side="right", padx=(SPACING[8], 0))

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

        left = tk.Frame(body, background=p.window)
        left.pack(side="left", fill="both", expand=True, padx=(0, SPACING[8]))
        right = tk.Frame(body, background=p.window)
        right.pack(side="right", fill="both", expand=True)

        self._build_radio_card(left, t("theme.menu"), THEME_OPTIONS, self.theme_var)
        self._build_radio_card(left, t("theme.background.label"), BACKGROUND_CHOICES, self.bg_var)

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

        # Behavior checkboxes inside a RoundedSurfaceCard
        behavior_card = RoundedSurfaceCard(
            right,
            bg_color=p.window,
            fill_color=p.paper,
            outline_color=p.line,
            radius=r,
            padding=SPACING[8],
            auto_height=True,
        )
        behavior_card.pack(fill="x", pady=(0, SPACING[8]))
        tk.Label(
            behavior_card.inner,
            text=t("settings.behavior"),
            background=p.paper,
            foreground=p.muted_ink,
            font=font_spec("caption", "bold", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
        ).pack(fill="x", pady=(0, SPACING[4]))
        for var, key in ((self.animations_var, "settings.animations"), (self.hints_var, "settings.hints")):
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

        # Live Preview Card
        preview_heading = tk.Label(
            right,
            text=t("appearance.dialog.preview_title"),
            background=p.window,
            foreground=p.muted_ink,
            font=font_spec("caption", "bold", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
        )
        preview_heading.pack(fill="x", pady=(SPACING[6], SPACING[4]))

        self.preview_window_frame = tk.Frame(right, background=p.window, padx=SPACING[8], pady=SPACING[8])
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

        self.preview_btn = RoundedButton(
            self.preview_card.inner,
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
        self.preview_btn.pack(anchor="w")

    def _build_radio_card(
        self,
        parent: tk.Misc,
        title: str,
        options: list[tuple[str, str]] | tuple[tuple[str, str], ...],
        variable: tk.StringVar,
    ) -> None:
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
        card.pack(fill="x", pady=(0, SPACING[8]))
        tk.Label(
            card.inner,
            text=title,
            background=p.paper,
            foreground=p.muted_ink,
            font=font_spec("caption", "bold", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
        ).pack(fill="x", pady=(0, SPACING[4]))
        for key, text_key in options:
            radio = GlideRadiobutton(
                card.inner,
                text=t(text_key),
                value=key,
                variable=variable,
                command=self._update_preview,
                bg=p.paper,
                fg=p.ink,
                selectcolor=p.acetate,
                activeforeground=p.ink,
                highlightthickness=0,
                font=font_spec("body", scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            )
            radio.pack(fill="x", pady=1)

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
        except tk.TclError:
            pass

    def _apply(self) -> None:
        if callable(self.on_apply):
            self.on_apply(
                theme_id=self.theme_var.get(),
                background_choice=self.bg_var.get(),
                accent_choice=self.accent_var.get(),
                radius_choice=self.radius_var.get(),
                font_scale_choice=self.scale_var.get(),
                font_weight_choice=self.weight_var.get(),
                animations_enabled=bool(self.animations_var.get()),
                hints_visible=bool(self.hints_var.get()),
            )
        self._cancel()

    def _cancel(self, _event: tk.Event | None = None) -> str:
        if not getattr(self, modal_session.ACTIVE_ATTRIBUTE, False):
            modal_session.return_focus(self.master, self, self._remembered_focus)
        try:
            self.destroy()
        except tk.TclError:
            pass
        return "break"
