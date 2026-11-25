"""Redesigned Glide Settings & Customization Modal Dialog for Chess & Chains.

Follows the Glide 1.0.2 settings dialog pattern:
- Compact ``GlideDropdown`` selectors instead of long radio-button lists
- Binary settings represented as two-option dropdowns
- Flat, card-free two-column responsive layout (collapses to one column)
- Live theme-color preview swatch and real-time preview with Cancel rollback
- Sticky footer with Cancel (left) and Save/Apply (right)

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
from glide_shell.custom_controls import ThemedAutoScrollbar

from ..chess import Color, Piece, PieceType
from ..i18n import Translator
from .dropdown import GlideDropdown
from .pieces import OwnerSvgPieces
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
    ThemePalette,
    apply_window_geometry,
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
        piece_set: str | None = None,
        piece_view: str = "front",
        has_custom_board: bool = False,
        on_open_engine: Callable[[], None] | None = None,
        on_apply: Callable[..., None] | None = None,
        on_preview: Callable[..., None] | None = None,
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
        # on_preview: called during live preview only (must NOT persist to disk).
        # Falls back to on_apply with persist=False if not supplied separately.
        self.on_preview = on_preview
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
        chosen_set = piece_set if piece_set is not None else ("top" if piece_view == "top" else "original")
        self.piece_set_var = tk.StringVar(self, value=chosen_set)
        self.piece_view_var = tk.StringVar(self, value="top" if chosen_set == "top" else "front")

        # String proxies for binary dropdowns
        self._anim_str = tk.StringVar(self, value="on" if animations_enabled else "off")
        self._hints_str = tk.StringVar(self, value="on" if hints_visible else "off")
        self._sidebar_str = tk.StringVar(self, value="on" if sidebar_visible else "off")
        self._sidebar_w_str = tk.StringVar(self, value="narrow" if sidebar_narrow else "standard")

        self._initial_snapshot = self._snapshot()
        self._dropdowns: list[GlideDropdown] = []
        self._section_labels: list[tk.Label] = []
        self._row_labels: list[tk.Label] = []
        self._row_frames: list[tk.Frame] = []
        self._columns = 2

        self.title(self.t("appearance.dialog.title"))
        self.configure(background=palette.window)
        self.minsize(480, 520)
        apply_window_geometry(self, 740, 620, 480, 520)

        self._build_ui()
        self._sync_perspective_dependency()

        self.bind("<Escape>", lambda _e: self._cancel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.transient(parent)
        self.deiconify()
        if modal:
            self.grab_set()

    def _snapshot(self) -> dict[str, object]:
        return {
            "theme_id": self.theme_var.get(),
            "background_choice": self.bg_var.get(),
            "accent_choice": self.accent_var.get(),
            "radius_choice": self.radius_var.get(),
            "font_scale_choice": self.scale_var.get(),
            "font_weight_choice": self.weight_var.get(),
            "animations_enabled": self.animations_var.get(),
            "hints_visible": self.hints_var.get(),
            "locale": self.locale_var.get(),
            "sidebar_visible": self.sidebar_visible_var.get(),
            "sidebar_narrow": self.sidebar_narrow_var.get(),
            "board_design_choice": self.board_design_var.get(),
            "board_perspective": self.perspective_var.get(),
            "piece_set": self.piece_set_var.get(),
            "piece_view": self.piece_view_var.get(),
        }

    def _build_ui(self) -> None:
        p = self._palette
        t = self.t
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        self._header = tk.Frame(self, background=p.window, padx=20, pady=14)
        self._header.grid(row=0, column=0, sticky="ew")
        self._header.grid_columnconfigure(0, weight=1)

        self._heading_lbl = tk.Label(
            self._header,
            text=t("appearance.dialog.heading"),
            background=p.window,
            foreground=p.ink,
            font=font_spec(14, "bold", scale_choice=self._scale_choice),
            anchor="w",
        )
        self._heading_lbl.grid(row=0, column=0, sticky="w")
        self.design_note_label = self._heading_lbl

        self._swatch_canvas = tk.Canvas(
            self._header,
            width=28,
            height=20,
            highlightthickness=0,
            bd=0,
            background=p.window,
        )
        self._swatch_canvas.grid(row=0, column=1, sticky="e", padx=(12, 0))
        self._draw_swatch()

        # Scrollable body
        self._body_wrap = tk.Frame(self, background=p.window)
        self._body_wrap.grid(row=1, column=0, sticky="nsew")
        self._body_wrap.grid_rowconfigure(0, weight=1)
        self._body_wrap.grid_columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(
            self._body_wrap,
            background=p.window,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._scrollbar = ThemedAutoScrollbar(
            self._body_wrap,
            p.window,
            p.acetate,
            p.line,
            p.action_new_bg,
            orient="vertical",
        )
        self._scrollbar.grid(row=0, column=1, sticky="ns")
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._content = tk.Frame(self._canvas, background=p.window, padx=20, pady=8)
        self._canvas_win = self._canvas.create_window((0, 0), window=self._content, anchor="nw")
        self._content.bind("<Configure>", lambda _e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        self._populate_sections()

        # Sticky footer
        self._footer_sep = tk.Frame(self, background=p.line, height=1)
        self._footer_sep.grid(row=2, column=0, sticky="ew")

        self._footer = tk.Frame(self, background=p.window, padx=20, pady=12)
        self._footer.grid(row=3, column=0, sticky="ew")
        self._footer.grid_columnconfigure(0, weight=1)

        self._cancel_btn = RoundedButton(
            self._footer,
            text=t("appearance.dialog.cancel"),
            command=self._cancel,
            palette=p,
            corner_radius=self._corner_radius,
            scale_choice=self._scale_choice,
            weight_choice=self._weight_choice,
            width=120,
            height=34,
        )
        self._cancel_btn.grid(row=0, column=1, padx=(0, 10), sticky="e")

        self._apply_btn = RoundedButton(
            self._footer,
            text=t("appearance.dialog.apply"),
            command=self._save_and_close,
            palette=p,
            primary=True,
            corner_radius=self._corner_radius,
            scale_choice=self._scale_choice,
            weight_choice=self._weight_choice,
            width=130,
            height=34,
        )
        self._apply_btn.grid(row=0, column=2, sticky="e")

    def _on_canvas_configure(self, event: tk.Event[tk.Misc]) -> None:
        self._canvas.itemconfigure(self._canvas_win, width=event.width)
        new_cols = 2 if event.width >= 600 else 1
        if new_cols != self._columns:
            self._columns = new_cols
            self._relayout_rows()

    def _populate_sections(self) -> None:
        t = self.t
        is_de = self.locale_var.get() == "de"

        theme_opts = [(item[0], item[1]) for item in THEME_OPTIONS]
        accent_opts = [(item[0], item[1]) for item in ACCENT_CHOICES]
        bg_opts = [(item[0], item[1]) for item in BACKGROUND_CHOICES]
        radius_opts = [(item[0], item[1]) for item in RADIUS_CHOICES]
        scale_opts = [(item[0], item[1]) for item in FONT_SCALE_CHOICES]
        weight_opts = [(item[0], item[1]) for item in FONT_WEIGHT_CHOICES]
        locale_opts = [("de", "Deutsch"), ("en", "English")]

        board_opts = [("standard", "Standard"), ("marble", "Marmor" if is_de else "Marble")]
        if self._has_custom_board:
            board_opts.append(("custom", "Benutzerdefiniert" if is_de else "Custom"))
        persp_opts = [
            ("2d", "Vogelperspektive (2D)" if is_de else "Top-down (2D)"),
            ("3d", "Räumlich (3D)" if is_de else "Spatial (3D)"),
        ]
        piece_set_opts = [
            ("original", "Original"),
            ("top", "Draufsicht" if is_de else "Top view"),
            ("classic", "Klassisch" if is_de else "Classic"),
        ]
        on_off = [("on", "Ein" if is_de else "On"), ("off", "Aus" if is_de else "Off")]
        sb_width = [
            ("standard", "Standard" if is_de else "Standard"),
            ("narrow", "Schmal" if is_de else "Narrow"),
        ]

        self._row_items: list[tuple[str, tk.Frame]] = []

        self._add_section("Darstellung" if is_de else "Appearance", [
            ("Theme" if is_de else "Theme", self.theme_var, theme_opts, self._on_any_change),
            ("Themenfarbe" if is_de else "Theme Color", self.accent_var, accent_opts, self._on_any_change),
            ("Hintergrund" if is_de else "Background", self.bg_var, bg_opts, self._on_any_change),
            ("Eckenradius" if is_de else "Corner Radius", self.radius_var, radius_opts, self._on_any_change),
            ("Schriftgröße" if is_de else "Font Scale", self.scale_var, scale_opts, self._on_any_change),
            ("Schriftgewicht" if is_de else "Font Weight", self.weight_var, weight_opts, self._on_any_change),
            ("Sprache" if is_de else "Language", self.locale_var, locale_opts, self._on_any_change),
        ])

        self._persp_dropdown: GlideDropdown | None = None
        self._add_section("Schachbrett" if is_de else "Chessboard", [
            ("Brettdesign" if is_de else "Board Design", self.board_design_var, board_opts, self._on_board_design_change),
            ("Perspektive" if is_de else "Perspective", self.perspective_var, persp_opts, self._on_any_change),
            ("Figurenset" if is_de else "Piece Set", self.piece_set_var, piece_set_opts, self._on_piece_set_change),
        ])

        p = self._palette
        preview_frame = tk.Frame(self._content, background=p.window, pady=6)
        preview_lbl = tk.Label(
            preview_frame,
            text="Vorschau" if is_de else "Preview",
            background=p.window,
            foreground=p.muted_ink,
            font=font_spec(9, scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            anchor="w",
        )
        preview_lbl.pack(anchor="w", pady=(0, 2))
        self._row_labels.append(preview_lbl)

        self._piece_preview_canvas = tk.Canvas(
            preview_frame,
            width=194,
            height=34,
            background=p.window,
            highlightthickness=0,
            bd=0,
        )
        self._piece_preview_canvas.pack(anchor="w")
        self._row_frames.append(preview_frame)
        self._row_items.append(("row", preview_frame))
        self._update_piece_preview()

        self._add_section("Bedienung & Partie" if is_de else "Behavior & Match", [
            ("Animationen" if is_de else "Animations", self._anim_str, on_off, self._on_binary_change),
            ("Hinweise" if is_de else "Hints", self._hints_str, on_off, self._on_binary_change),
            ("Seitenleiste" if is_de else "Sidebar", self._sidebar_str, on_off, self._on_binary_change),
            ("Seitenleisten-Breite" if is_de else "Sidebar Width", self._sidebar_w_str, sb_width, self._on_binary_change),
        ])

        if self.on_open_engine is not None:
            p = self._palette
            eng_frame = tk.Frame(self._content, background=p.window, pady=6)
            self._engine_btn = RoundedButton(
                eng_frame,
                text="Engine-Einstellungen…" if is_de else "Engine Settings…",
                command=self.on_open_engine,
                palette=p,
                corner_radius=self._corner_radius,
                scale_choice=self._scale_choice,
                weight_choice=self._weight_choice,
                width=200,
                height=32,
            )
            self._engine_btn.pack(anchor="w")
            self._row_frames.append(eng_frame)
            self._row_items.append(("row", eng_frame))
        else:
            self._engine_btn = None
        self.engine_btn = self._engine_btn

        self._relayout_rows()

    def _add_section(
        self,
        title: str,
        rows: list[tuple[str, tk.StringVar, list[tuple[str, str]], Callable[[str], None]]],
    ) -> None:
        p = self._palette
        sec_frame = tk.Frame(self._content, background=p.window, pady=6)
        sec_lbl = tk.Label(
            sec_frame,
            text=title,
            background=p.window,
            foreground=p.action_new_bg,
            font=font_spec(11, "bold", scale_choice=self._scale_choice),
            anchor="w",
        )
        sec_lbl.pack(anchor="w")
        self._section_labels.append(sec_lbl)
        self._row_frames.append(sec_frame)
        self._row_items.append(("section", sec_frame))

        for label_text, var, opts, cb in rows:
            row = tk.Frame(self._content, background=p.window, pady=4, padx=4)
            row.grid_columnconfigure(0, weight=1)
            lbl = tk.Label(
                row,
                text=label_text,
                background=p.window,
                foreground=p.ink,
                font=font_spec(10, scale_choice=self._scale_choice, weight_choice=self._weight_choice),
                anchor="w",
            )
            lbl.grid(row=0, column=0, sticky="w", padx=(0, 8))
            dd_w = 215 if self._scale_choice in ("large", "extra-large") else 190
            dd = GlideDropdown(
                row,
                var,
                opts,
                p,
                corner_radius=min(self._corner_radius, 8),
                scale_choice=self._scale_choice,
                weight_choice=self._weight_choice,
                width=dd_w,
                height=32,
                on_change=cb,
            )
            dd.grid(row=0, column=1, sticky="e")
            if var is self.perspective_var:
                self._persp_dropdown = dd
            self._row_labels.append(lbl)
            self._row_frames.append(row)
            self._dropdowns.append(dd)
            self._row_items.append(("row", row))

    def _relayout_rows(self) -> None:
        for _, frame in self._row_items:
            frame.grid_forget()
        cols = self._columns
        for c in range(2):
            self._content.grid_columnconfigure(c, weight=1 if c < cols else 0)
        r = 0
        c = 0
        for kind, frame in self._row_items:
            if kind == "section":
                if c != 0:
                    r += 1
                    c = 0
                frame.grid(row=r, column=0, columnspan=cols, sticky="ew", pady=(8, 2))
                r += 1
            else:
                frame.grid(row=r, column=c, sticky="ew", padx=(0, 14) if (cols == 2 and c == 0) else 0)
                c += 1
                if c >= cols:
                    c = 0
                    r += 1

    def _draw_swatch(self) -> None:
        c = self._swatch_canvas
        c.delete("all")
        p = self._palette
        c.configure(background=p.window)
        c.create_oval(4, 2, 24, 18, fill=p.action_new_bg, outline=p.line, width=1)

    def _sync_perspective_dependency(self) -> None:
        if self._persp_dropdown is None:
            return
        design = self.board_design_var.get()
        # 3D perspective is only supported for the marble board design.
        # Standard and custom boards are always 2D (custom SVG must not silently
        # become a marble board when the user switches perspective).
        if design != "marble":
            if self.perspective_var.get() != "2d":
                self.perspective_var.set("2d")
            self._persp_dropdown.set_state("disabled")
        else:
            self._persp_dropdown.set_state("normal")

    def _on_board_design_change(self, _val: str) -> None:
        self._sync_perspective_dependency()
        self._on_any_change(_val)

    def _on_piece_set_change(self, val: str) -> None:
        self.piece_view_var.set("top" if val == "top" else "front")
        self._update_piece_preview()
        self._on_any_change(val)

    def _update_piece_preview(self) -> None:
        if not hasattr(self, "_piece_preview_canvas"):
            return
        c = self._piece_preview_canvas
        c.delete("all")
        p = self._palette
        c.configure(background=p.window)
        renderer = OwnerSvgPieces(piece_set=self.piece_set_var.get())
        sq_size = 32
        pieces = [
            (Piece(Color.WHITE, PieceType.PAWN), True),
            (Piece(Color.BLACK, PieceType.ROOK), False),
            (Piece(Color.WHITE, PieceType.KNIGHT), True),
            (Piece(Color.BLACK, PieceType.BISHOP), False),
            (Piece(Color.WHITE, PieceType.QUEEN), True),
            (Piece(Color.BLACK, PieceType.KING), False),
        ]
        light_sq = p.square_light
        dark_sq = p.square_dark
        for i, (pc, is_dark) in enumerate(pieces):
            x0 = i * sq_size + 1
            y0 = 1
            x1 = x0 + sq_size
            y1 = y0 + sq_size
            sq_fill = dark_sq if is_dark else light_sq
            c.create_rectangle(x0, y0, x1, y1, fill=sq_fill, outline=p.line, width=1)
            cx = (x0 + x1) / 2
            cy = (y0 + y1) / 2
            renderer.draw(c, cx, cy, sq_size - 4, pc)

    def _on_binary_change(self, _val: str) -> None:
        self.animations_var.set(self._anim_str.get() == "on")
        self.hints_var.set(self._hints_str.get() == "on")
        self.sidebar_visible_var.set(self._sidebar_str.get() == "on")
        self.sidebar_narrow_var.set(self._sidebar_w_str.get() == "narrow")
        self._on_any_change(_val)

    def _on_any_change(self, _val: str) -> None:
        self._apply_live_preview()

    def _update_preview(self) -> None:
        self._apply_live_preview()

    def _apply_live_preview(self) -> None:
        self._palette = resolve_theme(
            self.theme_var.get(),
            accent=self.accent_var.get(),
            background=self.bg_var.get(),
        )
        self._corner_radius = RADIUS_MAP.get(self.radius_var.get(), 12)
        self._scale_choice = self.scale_var.get()
        self._weight_choice = self.weight_var.get()
        self._retheme_dialog()
        self._emit_preview(self._snapshot())

    def _emit_preview(self, payload: dict[str, object]) -> None:
        """Call the preview callback (persist=False).

        Uses ``on_preview`` if supplied, otherwise falls back to ``on_apply``
        with ``persist=False`` appended when the callback's signature accepts it.
        """
        cb = self.on_preview if self.on_preview is not None else self.on_apply
        if cb is None:
            return
        sig = inspect.signature(cb)
        params = sig.parameters
        has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
        if has_var_kw:
            # Callback accepts **kwargs — pass persist=False so it does not write to disk
            cb(**payload, persist=False)
            return
        # Callback has explicit params only — filter and do not inject persist
        accepted = {k: v for k, v in payload.items() if k in params}
        cb(**accepted)

    def _retheme_dialog(self) -> None:
        p = self._palette
        self.configure(background=p.window)
        for frame in (self._header, self._body_wrap, self._content, self._footer, *self._row_frames):
            frame.configure(background=p.window)
        self._canvas.configure(background=p.window)
        self._footer_sep.configure(background=p.line)
        self._heading_lbl.configure(
            background=p.window,
            foreground=p.ink,
            font=font_spec(14, "bold", scale_choice=self._scale_choice),
        )
        self._draw_swatch()
        for lbl in self._section_labels:
            lbl.configure(
                background=p.window,
                foreground=p.action_new_bg,
                font=font_spec(11, "bold", scale_choice=self._scale_choice),
            )
        for lbl in self._row_labels:
            lbl.configure(
                background=p.window,
                foreground=p.ink,
                font=font_spec(10, scale_choice=self._scale_choice, weight_choice=self._weight_choice),
            )
        for dd in self._dropdowns:
            dd.apply_theme(
                p,
                corner_radius=min(self._corner_radius, 8),
                scale_choice=self._scale_choice,
                weight_choice=self._weight_choice,
            )
        for btn in (self._cancel_btn, self._apply_btn, self._engine_btn):
            if btn is not None and hasattr(btn, "update_theme"):
                btn.update_theme(
                    p,
                    corner_radius=self._corner_radius,
                    scale_choice=self._scale_choice,
                    weight_choice=self._weight_choice,
                )
        self._update_piece_preview()

    def _emit_apply(self, payload: dict[str, object]) -> None:
        if self.on_apply is None:
            return
        sig = inspect.signature(self.on_apply)
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            self.on_apply(**payload)
            return
        accepted = {k: v for k, v in payload.items() if k in sig.parameters}
        self.on_apply(**accepted)

    def _apply(self) -> None:
        self._save_and_close()

    def _save_and_close(self) -> None:
        self._emit_apply(self._snapshot())
        self._close()

    def _cancel(self) -> None:
        self._emit_preview(self._initial_snapshot)
        self._close()

    def _close(self) -> None:
        try:
            self.grab_release()
        except tk.TclError:
            pass
        modal_session.return_focus(self.master, self, self._remembered_focus)
        self.destroy()
