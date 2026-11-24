"""Themed Canvas-based dropdown control for Chess & Chains.

Avoids native macOS Aqua ``ttk.Combobox`` rendering issues in Dark Mode and
inherits all colors, corner radii, and font scaling from ``ThemePalette``.

SPDX-License-Identifier: MPL-2.0
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import tkinter as tk
from typing import Callable, Sequence

from glide_shell.custom_controls import rounded_rect_points

from .theme import ThemePalette, clip_button_text, font_spec


class GlideDropdown(tk.Canvas):
    """Compact, theme-aware dropdown selector with keyboard & mouse support."""

    def __init__(
        self,
        master: tk.Misc,
        variable: tk.StringVar,
        options: Sequence[tuple[str, str]],
        palette: ThemePalette,
        *,
        corner_radius: int = 8,
        scale_choice: str = "standard",
        weight_choice: str = "standard",
        width: int = 190,
        height: int = 32,
        on_change: Callable[[str], None] | None = None,
        state: str = "normal",
    ) -> None:
        super().__init__(
            master,
            width=width,
            height=height,
            highlightthickness=0,
            bd=0,
            background=palette.paper,
            takefocus=1 if state == "normal" else 0,
        )
        self._variable = variable
        self._choices: list[tuple[str, str]] = list(options)
        self._palette = palette
        self._corner_radius = corner_radius
        self._scale_choice = scale_choice
        self._weight_choice = weight_choice
        self._on_change = on_change
        self._state = state
        self._hovered = False
        self._focused = False
        self._popup: tk.Toplevel | None = None
        self._popup_canvas: tk.Canvas | None = None
        self._popup_hover_idx: int = -1

        self.bind("<Configure>", lambda _e: self._redraw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Button-1>", self._on_click)
        self.bind("<space>", self._on_key_open)
        self.bind("<Return>", self._on_key_open)
        self.bind("<Down>", self._on_key_open)
        self.bind("<Destroy>", self._on_destroy)
        self._trace_id = self._variable.trace_add("write", lambda *_: self._redraw())
        self._redraw()

    def _on_destroy(self, event: tk.Event[tk.Misc]) -> None:
        if event.widget is self:
            self._close_popup()
            try:
                self._variable.trace_remove("write", self._trace_id)
            except tk.TclError:
                pass

    def _on_enter(self, _event: tk.Event[tk.Misc]) -> None:
        if self._state == "normal":
            self._hovered = True
            self._redraw()

    def _on_leave(self, _event: tk.Event[tk.Misc]) -> None:
        self._hovered = False
        self._redraw()

    def _on_focus_in(self, _event: tk.Event[tk.Misc]) -> None:
        self._focused = True
        self._redraw()

    def _on_focus_out(self, _event: tk.Event[tk.Misc]) -> None:
        self._focused = False
        self._redraw()

    def _on_click(self, _event: tk.Event[tk.Misc]) -> None:
        if self._state != "normal":
            return
        self.focus_set()
        if self._popup is not None:
            self._close_popup()
        else:
            self._open_popup()

    def _on_key_open(self, _event: tk.Event[tk.Misc]) -> str:
        if self._state != "normal":
            return "break"
        if self._popup is None:
            self._open_popup()
        return "break"

    def set_options(self, options: Sequence[tuple[str, str]]) -> None:
        self._choices = list(options)
        self._redraw()

    def set_state(self, state: str) -> None:
        self._state = state
        self.configure(takefocus=1 if state == "normal" else 0)
        if state != "normal":
            self._hovered = False
            self._close_popup()
        self._redraw()

    def apply_theme(
        self,
        palette: ThemePalette,
        *,
        corner_radius: int | None = None,
        scale_choice: str | None = None,
        weight_choice: str | None = None,
    ) -> None:
        self._palette = palette
        if corner_radius is not None:
            self._corner_radius = corner_radius
        if scale_choice is not None:
            self._scale_choice = scale_choice
        if weight_choice is not None:
            self._weight_choice = weight_choice
        try:
            parent_bg = self.master.cget("background")
        except tk.TclError:
            parent_bg = palette.paper
        self.configure(background=parent_bg)
        self._redraw()

    def _current_label(self) -> str:
        val = self._variable.get()
        for opt_val, opt_label in self._choices:
            if opt_val == val:
                return opt_label
        return self._choices[0][1] if self._choices else val

    def _redraw(self) -> None:
        if not self.winfo_exists():
            return
        w = max(self.winfo_width(), int(self.cget("width")))
        h = max(self.winfo_height(), int(self.cget("height")))
        self.delete("all")
        p = self._palette
        disabled = self._state != "normal"
        fill = p.acetate if (disabled or self._hovered) else p.paper
        if self._popup is not None or self._focused:
            outline = p.action_new_bg
            outline_w = 2
        elif self._hovered and not disabled:
            outline = p.action_new_bg
            outline_w = 1
        else:
            outline = p.input_border
            outline_w = 1

        radius = min(self._corner_radius, max(4, h // 3))
        pts = rounded_rect_points(1, 1, w - 1, h - 1, radius)
        self.create_polygon(pts, smooth=True, fill=fill, outline=outline, width=outline_w)

        fnt = font_spec(10, scale_choice=self._scale_choice, weight_choice=self._weight_choice)
        label = clip_button_text(self._current_label())
        text_color = p.muted_ink if disabled else p.ink
        self.create_text(
            12,
            h // 2,
            text=label,
            anchor="w",
            fill=text_color,
            font=fnt,
        )
        chevron = "▴" if self._popup is not None else "▾"
        self.create_text(
            w - 12,
            h // 2,
            text=chevron,
            anchor="e",
            fill=p.muted_ink if disabled else p.ink,
            font=fnt,
        )

    def _open_popup(self) -> None:
        if not self._choices:
            return
        self._close_popup()
        p = self._palette
        w = max(self.winfo_width(), int(self.cget("width")))
        row_h = 28
        total_h = len(self._choices) * row_h + 6

        popup = tk.Toplevel(self)
        popup.withdraw()
        popup.overrideredirect(True)
        try:
            popup.transient(self.winfo_toplevel())
        except tk.TclError:
            pass
        popup.configure(background=p.input_border)

        x = self.winfo_rootx()
        y = self.winfo_rooty() + max(self.winfo_height(), int(self.cget("height"))) + 2
        screen_h = self.winfo_screenheight()
        if y + total_h > screen_h - 16:
            y = max(16, self.winfo_rooty() - total_h - 2)

        canvas = tk.Canvas(
            popup,
            width=w,
            height=total_h,
            highlightthickness=1,
            highlightbackground=p.input_border,
            bd=0,
            background=p.paper,
        )
        canvas.pack(fill="both", expand=True)

        current_val = self._variable.get()
        self._popup_hover_idx = next(
            (i for i, (v, _) in enumerate(self._choices) if v == current_val),
            0,
        )

        self._popup = popup
        self._popup_canvas = canvas
        self._draw_popup()

        canvas.bind("<Motion>", self._on_popup_motion)
        canvas.bind("<Button-1>", self._on_popup_click)
        popup.bind("<Escape>", lambda _e: self._close_popup(refocus=True))
        popup.bind("<Up>", self._on_popup_up)
        popup.bind("<Down>", self._on_popup_down)
        popup.bind("<Return>", self._on_popup_return)
        popup.bind("<space>", self._on_popup_return)
        popup.bind("<FocusOut>", lambda _e: self.after(10, self._check_focus_out))

        popup.geometry(f"{w}x{total_h}+{x}+{y}")
        popup.deiconify()
        popup.focus_set()
        self._redraw()

    def _check_focus_out(self) -> None:
        if self._popup is None:
            return
        try:
            focused = self.focus_get()
        except tk.TclError:
            focused = None
        if focused not in (self._popup, self._popup_canvas, self):
            self._close_popup()

    def _draw_popup(self) -> None:
        canvas = self._popup_canvas
        if canvas is None or not canvas.winfo_exists():
            return
        canvas.delete("all")
        p = self._palette
        w = int(canvas.cget("width"))
        row_h = 28
        fnt = font_spec(10, scale_choice=self._scale_choice, weight_choice=self._weight_choice)
        current_val = self._variable.get()

        for idx, (val, label) in enumerate(self._choices):
            y0 = 3 + idx * row_h
            y1 = y0 + row_h
            is_selected = val == current_val
            is_hovered = idx == self._popup_hover_idx
            if is_hovered:
                canvas.create_rectangle(3, y0, w - 3, y1, fill=p.hover, outline="")
            elif is_selected:
                canvas.create_rectangle(3, y0, w - 3, y1, fill=p.acetate, outline="")
            text_color = p.action_new_bg if is_selected else p.ink
            clipped = clip_button_text(label)
            canvas.create_text(
                12,
                (y0 + y1) // 2,
                text=clipped,
                anchor="w",
                fill=text_color,
                font=fnt,
            )

    def _on_popup_motion(self, event: tk.Event[tk.Misc]) -> None:
        idx = (event.y - 3) // 28
        if 0 <= idx < len(self._choices) and idx != self._popup_hover_idx:
            self._popup_hover_idx = idx
            self._draw_popup()

    def _on_popup_click(self, event: tk.Event[tk.Misc]) -> None:
        idx = (event.y - 3) // 28
        if 0 <= idx < len(self._choices):
            self._select_index(idx)

    def _on_popup_up(self, _event: tk.Event[tk.Misc]) -> str:
        if self._choices:
            self._popup_hover_idx = (self._popup_hover_idx - 1) % len(self._choices)
            self._draw_popup()
        return "break"

    def _on_popup_down(self, _event: tk.Event[tk.Misc]) -> str:
        if self._choices:
            self._popup_hover_idx = (self._popup_hover_idx + 1) % len(self._choices)
            self._draw_popup()
        return "break"

    def _on_popup_return(self, _event: tk.Event[tk.Misc]) -> str:
        if 0 <= self._popup_hover_idx < len(self._choices):
            self._select_index(self._popup_hover_idx)
        return "break"

    def _select_index(self, idx: int) -> None:
        val, _label = self._choices[idx]
        self._close_popup(refocus=True)
        if self._variable.get() != val:
            self._variable.set(val)
        if self._on_change is not None:
            self._on_change(val)

    def _close_popup(self, *, refocus: bool = False) -> None:
        popup = self._popup
        self._popup = None
        self._popup_canvas = None
        if popup is not None:
            try:
                if popup.winfo_exists():
                    popup.destroy()
            except tk.TclError:
                pass
        if refocus and self.winfo_exists():
            try:
                self.focus_set()
            except tk.TclError:
                pass
        self._redraw()
