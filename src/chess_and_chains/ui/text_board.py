"""A text-based way to inspect a position and play the same legal moves."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from glide_shell import modal_session

from ..chess import GameState, Move, square_name
from ..i18n import Translator
from .dialogs import bind_button_enter


class TextBoardDialog(tk.Toplevel):
    """Keep a textual move picker synchronized with the visible board."""

    def __init__(self, parent: tk.Tk, translator: Translator, on_move: Callable[[Move], None]) -> None:
        super().__init__(parent)
        self.withdraw()
        self._remembered_focus = modal_session.remember_focus(parent, self, parent)
        previous_focus = self._remembered_focus[1]
        self.title(translator("text_board.title"))
        self.t = translator
        self._on_move = on_move
        self._previous_focus = previous_focus
        self._state: GameState | None = None
        self._legal: tuple[Move, ...] = ()
        self._sources: tuple[int, ...] = ()
        self._targets: tuple[Move, ...] = ()
        self._selected_square: int | None = None

        content = ttk.Frame(self, padding=16)
        content.pack(fill="both", expand=True)
        content.columnconfigure((0, 1), weight=1, uniform="board")
        content.rowconfigure(3, weight=1)
        self._status = ttk.Label(content)
        self._status.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 3))
        self._feedback = ttk.Label(content)
        self._feedback.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.pieces = self._add_list(content, self.t("text_board.pieces"), 0)
        self.targets = self._add_list(content, self.t("text_board.targets"), 1)
        self._availability = ttk.Label(content)
        self._availability.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(5, 7))
        self._availability.configure(text=self.t("text_board.no_targets"))

        close = ttk.Button(content, text=self.t("text_board.close"), command=self._close)
        close.grid(row=5, column=0, sticky="ew", padx=(0, 5))
        self.play_button = ttk.Button(content, text=self.t("text_board.play"), command=self._play, state="disabled")
        self.play_button.grid(row=5, column=1, sticky="ew", padx=(5, 0))
        for button in (close, self.play_button):
            bind_button_enter(button)
        self.pieces.bind("<<ListboxSelect>>", self._select_piece)
        for key in ("<Return>", "<KP_Enter>"):
            self.pieces.bind(key, self._focus_targets)
            self.targets.bind(key, self._play)
        self.bind("<Escape>", self._close)
        self.protocol("WM_DELETE_WINDOW", self._close)
        content.bind("<Configure>", lambda event: self._wrap_feedback(event.width))
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        if parent.winfo_viewable():
            self.transient(parent)
            self.tk.call("tk::PlaceWindow", self._w, "widget", parent._w)
        self.deiconify()
        self.pieces.focus_set()
        self.grab_set()

    @staticmethod
    def _add_list(content: ttk.Frame, title: str, column: int) -> tk.Listbox:
        padding = (0, 5) if column == 0 else (5, 0)
        ttk.Label(content, text=title).grid(row=2, column=column, sticky="w", padx=padding, pady=(0, 4))
        frame = ttk.Frame(content)
        frame.grid(row=3, column=column, sticky="nsew", padx=padding)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        items = tk.Listbox(frame, width=20, height=8, exportselection=False, selectmode=tk.BROWSE)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=items.yview, takefocus=False)
        items.configure(yscrollcommand=scrollbar.set)
        items.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        return items

    def _wrap_feedback(self, width: int) -> None:
        for label in (self._status, self._feedback, self._availability):
            label.configure(wraplength=max(1, width - 32))

    def show_position(
        self, state: GameState | None, legal_moves: tuple[Move, ...], status: str, feedback: str = "",
    ) -> None:
        self._status.configure(text=status)
        self._feedback.configure(text=feedback)
        if state == self._state and legal_moves == self._legal:
            return
        self._state = state
        self._legal = legal_moves
        self.pieces.delete(0, tk.END)
        entries = [] if state is None else [
            (square, piece) for square, piece in enumerate(state.board) if piece is not None
        ]
        if state is not None:
            entries.sort(key=lambda entry: (entry[1].color != state.turn, entry[0]))
        self._sources = tuple(square for square, _piece in entries)
        for square, piece in entries:
            self.pieces.insert(tk.END, self.t(
                "text_board.piece",
                square=square_name(square), color=self.t(f"side.{piece.color.name.lower()}"),
                piece=self.t(f"piece.{piece.kind.name.lower()}"),
            ))
        if self._sources:
            playable = {move.from_square for move in self._legal}
            preferred = self._selected_square
            if preferred not in playable:
                preferred = next((square for square in self._sources if square in playable), self._sources[0])
            index = self._sources.index(preferred)
            self.pieces.selection_set(index)
            self.pieces.selection_anchor(index)
            self.pieces.activate(index)
            self.pieces.see(index)
        self._select_piece()

    def _select_piece(self, _event: tk.Event | None = None) -> None:
        selected = self.pieces.curselection()
        self._selected_square = self._sources[selected[0]] if selected else None
        self._targets = tuple(move for move in self._legal if move.from_square == self._selected_square)
        self.targets.delete(0, tk.END)
        for move in self._targets:
            square = square_name(move.to_square)
            label = square if move.promotion is None else self.t(
                "text_board.promotion", square=square, piece=self.t(f"piece.{move.promotion.name.lower()}"),
            )
            self.targets.insert(tk.END, label)
        if self._targets:
            self.targets.selection_set(0)
            self.targets.selection_anchor(0)
            self.targets.activate(0)
        self.targets.configure(takefocus=bool(self._targets))
        self.play_button.state(("!disabled",) if self._targets else ("disabled",))
        self._availability.configure(text=self.t("text_board.no_targets") if not self._targets else "")

    def _focus_targets(self, _event: tk.Event) -> str:
        if self._targets:
            self.targets.focus_set()
        return "break"

    def _play(self, _event: tk.Event | None = None) -> str:
        selected = self.targets.curselection()
        if selected:
            before = self._state
            self._on_move(self._targets[selected[0]])
            if self._state != before:
                self.pieces.focus_set()
        return "break"

    def _close(self, _event: tk.Event | None = None) -> str:
        if not getattr(self, modal_session.ACTIVE_ATTRIBUTE, False):
            modal_session.return_focus(self.master, self, self._remembered_focus)
        self.destroy()
        return "break"
