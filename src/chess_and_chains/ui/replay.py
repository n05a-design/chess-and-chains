"""Read-only navigation through a captured game record."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import tkinter as tk
from tkinter import ttk

from ..chess import ChessGame, Color, GameStatus, to_san
from ..i18n import Translator
from .board import BoardCanvas
from .dialogs import bind_button_enter


class ReplayDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, game: ChessGame, t: Translator, artwork, renderer, orientation) -> None:
        self._previous_focus = parent.focus_lastfor()
        super().__init__(parent)
        self.withdraw()
        self.title(t("replay.title"))
        self.t = t
        self._positions = game.played_positions()
        self._moves = tuple(game.moves)
        self._rules = game.rules
        self._end = game.outcome()
        self.index = 0

        panel = ttk.Frame(self, padding=12)
        panel.pack(fill="both", expand=True)
        panel.columnconfigure(0, weight=2)
        panel.columnconfigure(1, weight=1)
        panel.rowconfigure(1, weight=1)
        self.status = ttk.Label(panel, anchor="w")
        self.status.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.board = BoardCanvas(panel, lambda _moves: None, renderer=renderer, artwork=artwork, translator=t)
        self.board.set_orientation(orientation)
        self.board.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        sidebar = ttk.Frame(panel)
        sidebar.grid(row=1, column=1, sticky="nsew")
        sidebar.columnconfigure((0, 1), weight=1, uniform="commands")
        sidebar.rowconfigure(0, weight=1)
        list_frame = ttk.Frame(sidebar)
        list_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 8))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.move_list = tk.Listbox(list_frame, exportselection=False, width=16, height=8, selectmode=tk.BROWSE)
        self.move_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, command=self.move_list.yview, takefocus=False)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.move_list.configure(yscrollcommand=scrollbar.set)
        self.move_list.insert(tk.END, t("replay.start"))
        for position, move in zip(self._positions[:-1], self._moves, strict=True):
            mark = "." if position.turn is Color.WHITE else "…"
            self.move_list.insert(tk.END, f"{position.fullmove_number}{mark} {to_san(position, move, self._rules)}")
        self.move_list.bind("<<ListboxSelect>>", self._select_ply)

        self._first = self._button(sidebar, "replay.start", lambda: self.show(0), 1, 0)
        self._last = self._button(sidebar, "replay.end", lambda: self.show(len(self._moves)), 1, 1)
        self._previous = self._button(sidebar, "replay.previous", lambda: self.show(self.index - 1), 2, 0)
        self._next = self._button(sidebar, "replay.next", lambda: self.show(self.index + 1), 2, 1)
        close = self._button(sidebar, "text_board.close", self._close, 3, 0)
        close.grid_configure(columnspan=2)
        self.move_list.bind("<Left>", lambda _event: self._step(-1))
        self.move_list.bind("<Right>", lambda _event: self._step(1))
        self.bind("<Escape>", self._close)
        self.board.bind("<Escape>", self._close)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.status.bind("<Configure>", lambda event: self.status.configure(wraplength=event.width))
        self.show(0)
        self.update_idletasks()
        panel.columnconfigure(1, minsize=sidebar.winfo_reqwidth())
        self.geometry("760x500")
        self.minsize(570, 400)
        if parent.winfo_viewable():
            self.transient(parent)
            self.tk.call("tk::PlaceWindow", self._w, "widget", parent._w)
            self.geometry("760x500")
        self.deiconify()
        self.move_list.focus_set()
        self.grab_set()

    def _button(self, parent, key, command, row, column):
        button = ttk.Button(parent, text=self.t(key), command=command)
        button.grid(row=row, column=column, sticky="ew", padx=3, pady=3)
        bind_button_enter(button)
        return button

    def _select_ply(self, _event: tk.Event) -> None:
        selected = self.move_list.curselection()
        if selected:
            self.show(selected[0])

    def _step(self, delta: int) -> str:
        self.show(self.index + delta)
        return "break"

    def show(self, index: int) -> None:
        self.index = min(max(0, index), len(self._moves))
        state = self._positions[self.index]
        move = self._moves[self.index - 1] if self.index else None
        self.board.set_position(state, (), move, self._rules.is_in_check(state))
        self.move_list.selection_clear(0, tk.END)
        self.move_list.selection_set(self.index)
        self.move_list.selection_anchor(self.index)
        self.move_list.activate(self.index)
        self.move_list.see(self.index)
        self.status.configure(text=self.t("replay.position", index=self.index, total=len(self._moves)))
        if self.index == len(self._moves) and self._end.status is not GameStatus.ACTIVE:
            final = "½–½" if self._end.winner is None else ("1–0" if self._end.winner is Color.WHITE else "0–1")
            self.status.configure(text=self.t("replay.result", position=self.status.cget("text"), result=final))
        for button in (self._first, self._previous):
            button.configure(state="normal" if self.index else "disabled")
        for button in (self._last, self._next):
            button.configure(state="normal" if self.index < len(self._moves) else "disabled")

    def _close(self, _event: tk.Event | None = None) -> str:
        focus = self._previous_focus
        if focus is not None and focus.winfo_exists() and focus.winfo_viewable():
            focus.focus_set()
        self.destroy()
        return "break"
