"""Keyboard bindings and the position exchange dialog."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font, ttk
from typing import Callable

from glide_shell import desktop_adapter, modal_session, text_fit

from ..chess import ChessError, GameState, to_fen
from ..game.clock import TimeControl
from ..i18n import Translator
from ..storage.exchange import parse_fen_text, read_fen_file, write_fen_file
from .theme import LIGHT_THEME, RoundedButton, ThemePalette


def bind_button_enter(button: tk.Button | ttk.Button | ttk.Checkbutton | RoundedButton) -> None:
    def invoke(_event: tk.Event) -> str:
        button.invoke()
        return "break"

    button.bind("<Return>", invoke)
    button.bind("<KP_Enter>", invoke)


def ask_time_control(parent: tk.Tk, t: Translator, theme: ThemePalette) -> TimeControl | None:
    """Collect a Fischer time control in whole seconds."""
    dialog = modal_session.create_dialog(
        parent, t("clock.custom"), background=theme.acetate, transient=bool(parent.winfo_viewable()),
    )
    focus = modal_session.remember_focus(parent, dialog, parent)
    content = ttk.Frame(dialog, padding=16, style="Glide.TFrame")
    content.pack(fill="both", expand=True)
    content.columnconfigure(0, weight=1)
    initial = tk.StringVar(dialog, "300")
    increment = tk.StringVar(dialog, "0")
    feedback = tk.StringVar(dialog)
    fields = []
    for row, (key, value) in enumerate((("clock.initial_seconds", initial), ("clock.increment_seconds", increment))):
        ttk.Label(content, text=t(key), style="Glide.TLabel").grid(row=row * 2, column=0, sticky="w")
        entry = ttk.Entry(content, textvariable=value, style="Glide.TEntry")
        entry.grid(row=row * 2 + 1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        fields.append(entry)
    ttk.Label(content, textvariable=feedback, style="Glide.TLabel").grid(row=4, column=0, columnspan=2, sticky="w")
    result = None

    def accept(_event: tk.Event | None = None) -> str:
        nonlocal result
        try:
            result = TimeControl(int(initial.get()) * 1000, int(increment.get()) * 1000)
        except ValueError:
            feedback.set(t("clock.invalid_input"))
            return "break"
        dialog.destroy()
        return "break"

    start = ttk.Button(content, text=t("button.new_game"), command=accept, style="Glide.New.TButton")
    start.grid(row=5, column=0, sticky="e", padx=(0, 6), pady=(8, 0))
    cancel = ttk.Button(content, text=t("button.cancel"), command=dialog.destroy, style="Glide.TButton")
    cancel.grid(row=5, column=1, sticky="e", pady=(8, 0))
    for entry in fields:
        entry.bind("<Return>", accept)
        entry.bind("<KP_Enter>", accept)
    bind_button_enter(start)
    bind_button_enter(cancel)
    dialog.bind("<Escape>", lambda _event: dialog.destroy())
    modal_session.ensure_min_width(dialog)
    fields[0].focus_set()
    fields[0].selection_range(0, "end")
    try:
        modal_session.wait_modal(parent, dialog)
    finally:
        modal_session.return_focus(parent, dialog, focus)
    return result


def ask_archive_tag(parent: tk.Tk, t: Translator, theme: ThemePalette) -> str | None:
    dialog = modal_session.create_dialog(
        parent, t("library.add_tag"), background=theme.acetate, transient=bool(parent.winfo_viewable()),
    )
    focus = modal_session.remember_focus(parent, dialog, parent)
    content = ttk.Frame(dialog, padding=16, style="Glide.TFrame")
    content.pack(fill="both", expand=True)
    value, feedback = tk.StringVar(dialog), tk.StringVar(dialog)
    ttk.Label(content, text=t("library.tag"), style="Glide.TLabel").grid(row=0, column=0, sticky="w")
    entry = ttk.Entry(content, textvariable=value, style="Glide.TEntry")
    entry.grid(row=1, column=0, columnspan=2, sticky="ew")
    ttk.Label(content, textvariable=feedback, style="Glide.TLabel").grid(row=2, column=0, columnspan=2, sticky="w")
    result = None

    def accept(_event: tk.Event | None = None) -> str:
        nonlocal result
        tag = value.get().strip()
        if not 1 <= len(tag) <= 64 or any(ord(char) < 32 for char in tag):
            feedback.set(t("library.invalid_tag"))
            return "break"
        result = tag
        dialog.destroy()
        return "break"

    save = ttk.Button(content, text=t("button.save"), command=accept, style="Glide.New.TButton")
    save.grid(row=3, column=0, sticky="e", padx=4)
    cancel = ttk.Button(content, text=t("button.cancel"), command=dialog.destroy, style="Glide.TButton")
    cancel.grid(row=3, column=1, sticky="e")
    entry.bind("<Return>", accept)
    entry.bind("<KP_Enter>", accept)
    bind_button_enter(save)
    bind_button_enter(cancel)
    dialog.bind("<Escape>", lambda _event: dialog.destroy())
    modal_session.ensure_min_width(dialog)
    entry.focus_set()
    try:
        modal_session.wait_modal(parent, dialog)
    finally:
        modal_session.return_focus(parent, dialog, focus)
    return result


class PositionDialog(tk.Toplevel):
    """Edit or export one FEN. Only an accepted position reaches the game."""

    def __init__(
        self, parent: tk.Tk, translator: Translator, position: GameState,
        confirm_replacement: Callable[[tk.Misc], bool],
        *, theme: ThemePalette | None = None,
    ) -> None:
        super().__init__(parent)
        self.withdraw()
        self._remembered_focus = modal_session.remember_focus(parent, self, parent)
        self._theme = theme or LIGHT_THEME
        self.configure(background=self._theme.acetate)
        self.title(translator("position.title"))
        if parent.winfo_viewable():
            self.transient(parent)
        self.t = translator
        self.result: GameState | None = None
        self._previous_focus = self._remembered_focus[1]
        self._confirm_replacement = confirm_replacement

        content = ttk.Frame(self, padding=16, style="Glide.TFrame")
        content.pack(fill="both", expand=True)
        content.columnconfigure((0, 1), weight=1, uniform="actions")
        ttk.Label(content, text="FEN", style="Glide.Caption.Bold.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.draft = tk.StringVar(self, to_fen(position))
        fixed_font = font.nametofont("TkFixedFont", root=self)
        available = parent.winfo_width() if parent.winfo_viewable() else 500
        available_pixels = min(available, self.winfo_screenwidth()) - 64
        width = max(26, min(58, available_pixels // fixed_font.measure("0")))
        self.entry = ttk.Entry(content, textvariable=self.draft, width=width, font="TkFixedFont", style="Glide.TEntry")
        self.entry.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.entry.select_range(0, tk.END)
        self.entry.icursor(0)
        self.entry.bind("<Return>", self._play)
        self.entry.bind("<KP_Enter>", self._play)

        instruction = ttk.Label(content, text=self.t("position.help"),
                                wraplength=self.entry.winfo_reqwidth(), style="Glide.TLabel")
        instruction.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 10))
        self._feedback = ttk.Label(content, wraplength=self.entry.winfo_reqwidth(), style="Glide.Muted.TLabel")
        self._feedback.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(4, 10))
        self._draft_trace = self.draft.trace_add("write", self._clear_feedback)

        for label, command, row, column in (
            ("position.open", self._open, 3, 0),
            ("position.save", self._save, 3, 1),
            ("position.copy", self._copy, 4, 0),
            ("button.cancel", self._close, 7, 0),
            ("position.play", self._play, 7, 1),
        ):
            is_primary = label == "position.play"
            btn_style = "Glide.New.TButton" if is_primary else "Glide.TButton"
            button = ttk.Button(content, text=self.t(label), command=command, style=btn_style)
            button.grid(row=row, column=column, sticky="ew", padx=(0, 4) if column == 0 else (4, 0), pady=3)
            bind_button_enter(button)
            if label == "position.play":
                button.configure(default="active")

        ttk.Separator(content).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 7))
        self.bind("<Escape>", self._close)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        if parent.winfo_viewable():
            # Tk's dialog placement also accounts for the virtual root on multi-display desktops.
            self.tk.call("tk::PlaceWindow", self._w, "widget", parent._w)
        self.deiconify()
        self.entry.focus_set()
        self.grab_set()

    def _clear_feedback(self, *_trace: str) -> None:
        self.entry.state(("!invalid",))
        self._feedback.configure(text="")

    def _show_error(self, key: str, error: Exception) -> None:
        detail = text_fit.clip(str(error), 160, ellipsis="…")
        self._feedback.configure(text=self.t(key, error=detail))

    def _validated_draft(self) -> GameState | None:
        try:
            return parse_fen_text(self.draft.get())
        except ChessError as error:
            self.entry.state(("invalid",))
            self.entry.focus_set()
            self._show_error("position.invalid", error)
            return None

    def _open(self) -> None:
        source = filedialog.askopenfilename(
            parent=self, title=self.t("position.open"), filetypes=[(self.t("position.files"), "*.fen")],
        )
        if not source:
            return
        try:
            position = read_fen_file(Path(source))
        except (OSError, ValueError) as error:
            self._show_error("position.open_error", error)
            return
        self.draft.set(to_fen(position))
        self.entry.focus_set()
        self._feedback.configure(text=self.t("position.opened"))

    def _save(self) -> None:
        position = self._validated_draft()
        if position is None:
            return
        destination = filedialog.asksaveasfilename(
            parent=self, title=self.t("position.save"), filetypes=[(self.t("position.files"), "*.fen")],
            defaultextension=".fen", initialfile="chess-and-chains.fen",
        )
        if not destination:
            return
        try:
            write_fen_file(position, Path(destination))
        except (ChessError, OSError) as error:
            self._show_error("position.save_error", error)
            return
        self._feedback.configure(text=self.t("position.saved"))

    def _copy(self) -> None:
        position = self._validated_draft()
        if position is None:
            return
        try:
            desktop_adapter.copy_to_clipboard(self, to_fen(position))
        except tk.TclError:
            self._feedback.configure(text=self.t("position.copy_error"))
            return
        self._feedback.configure(text=self.t("position.copied"))

    def _play(self, _event: tk.Event | None = None) -> str:
        position = self._validated_draft()
        if position is not None and self._confirm_replacement(self):
            self.result = position
            self._close()
        return "break"

    def _close(self, _event: tk.Event | None = None) -> str:
        if not getattr(self, modal_session.ACTIVE_ATTRIBUTE, False):
            modal_session.return_focus(self.master, self, self._remembered_focus)
        self.destroy()
        return "break"

    def destroy(self) -> None:
        self.draft.trace_remove("write", self._draft_trace)
        super().destroy()
