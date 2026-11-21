"""Keyboard bindings and the position exchange dialog."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font, ttk
from typing import Callable

from ..chess import ChessError, GameState, to_fen
from ..i18n import Translator
from ..storage.exchange import parse_fen_text, read_fen_file, write_fen_file


def bind_button_enter(button: tk.Button | ttk.Button) -> None:
    def invoke(_event: tk.Event) -> str:
        button.invoke()
        return "break"

    button.bind("<Return>", invoke)
    button.bind("<KP_Enter>", invoke)


class PositionDialog(tk.Toplevel):
    """Edit or export one FEN. Only an accepted position reaches the game."""

    def __init__(
        self, parent: tk.Tk, translator: Translator, position: GameState,
        confirm_replacement: Callable[[tk.Misc], bool],
    ) -> None:
        previous_focus = parent.focus_lastfor()
        super().__init__(parent)
        self.withdraw()
        self.title(translator("position.title"))
        if parent.winfo_viewable():
            self.transient(parent)
        self.t = translator
        self.result: GameState | None = None
        self._previous_focus = previous_focus
        self._confirm_replacement = confirm_replacement

        content = ttk.Frame(self, padding=16)
        content.pack(fill="both", expand=True)
        content.columnconfigure((0, 1), weight=1, uniform="actions")
        ttk.Label(content, text="FEN").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.draft = tk.StringVar(self, to_fen(position))
        fixed_font = font.nametofont("TkFixedFont", root=self)
        available = parent.winfo_width() if parent.winfo_viewable() else 500
        available_pixels = min(available, self.winfo_screenwidth()) - 64
        width = max(26, min(58, available_pixels // fixed_font.measure("0")))
        self.entry = ttk.Entry(content, textvariable=self.draft, width=width, font="TkFixedFont")
        self.entry.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.entry.select_range(0, tk.END)
        self.entry.icursor(0)
        self.entry.bind("<Return>", self._play)
        self.entry.bind("<KP_Enter>", self._play)

        instruction = ttk.Label(content, text=self.t("position.help"),
                                wraplength=self.entry.winfo_reqwidth())
        instruction.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 10))
        self._feedback = ttk.Label(content, wraplength=self.entry.winfo_reqwidth())
        self._feedback.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(4, 10))
        self._draft_trace = self.draft.trace_add("write", self._clear_feedback)

        for label, command, row, column in (
            ("position.open", self._open, 3, 0),
            ("position.save", self._save, 3, 1),
            ("position.copy", self._copy, 4, 0),
            ("button.cancel", self._close, 7, 0),
            ("position.play", self._play, 7, 1),
        ):
            button = ttk.Button(content, text=self.t(label), command=command)
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
        detail = str(error)
        if len(detail) > 160:
            detail = detail[:159] + "…"
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
            self.clipboard_clear()
            self.clipboard_append(to_fen(position))
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
        focus = self._previous_focus
        if focus is not None and focus.winfo_exists() and focus.winfo_viewable():
            focus.focus_set()
        self.destroy()
        return "break"

    def destroy(self) -> None:
        self.draft.trace_remove("write", self._draft_trace)
        super().destroy()
