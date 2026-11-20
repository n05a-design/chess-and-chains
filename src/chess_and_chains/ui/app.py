"""Offline local two-player Tk desktop prototype."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Sequence

from ..chess import (
    ChessError,
    ChessGame,
    Color,
    GameStatus,
    Move,
    PieceType,
    to_san,
)
from .board import BoardCanvas, Orientation
from .theme import (
    ACETATE,
    BUTTON_ROLES,
    CHROME_YELLOW,
    DISABLED_INK,
    FONT_SIZES,
    INK,
    MUTED_INK,
    PAPER,
    SHADOW,
    TAB_IDLE,
    WINDOW,
)


class TabRail(tk.Canvas):
    """Two stepped, keyboard-operable tabs on the side leaf's fore edge."""

    def __init__(
        self,
        master: tk.Misc,
        on_change,
    ) -> None:
        super().__init__(
            master,
            width=54,
            background=ACETATE,
            highlightthickness=1,
            highlightbackground=ACETATE,
            highlightcolor=INK,
            takefocus=True,
            borderwidth=0,
        )
        self._on_change = on_change
        self._active = "play"
        self._tabs = ("play", "moves")
        self.bind("<Configure>", lambda _event: self.redraw())
        self.bind("<Button-1>", self._on_click)
        self.bind("<KeyPress>", self._on_key)
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        height = max(self.winfo_height(), 160)
        split = int(height * 0.47)
        bounds = {"play": (0, split), "moves": (split, height)}
        for tab in self._tabs:
            top, bottom = bounds[tab]
            left = 0 if self._active == tab else 7
            right = 49
            fill = CHROME_YELLOW if self._active == tab else TAB_IDLE
            self.create_polygon(
                left,
                top + 8,
                left + 7,
                top,
                right,
                top,
                right,
                bottom,
                left + 7,
                bottom,
                left,
                bottom - 8,
                fill=fill,
                outline=INK,
                width=1,
            )
            self.create_text(
                (left + right) / 2,
                (top + bottom) / 2,
                text=tab.upper(),
                angle=90,
                fill=INK,
                font=("TkDefaultFont", FONT_SIZES["caption"], "bold"),
            )

    def set_active(self, tab: str) -> None:
        if tab not in self._tabs:
            raise ValueError(f"Unknown game panel: {tab}")
        self._active = tab
        self.redraw()
        self._on_change(tab)

    def _on_click(self, event: tk.Event) -> None:
        self.focus_set()
        split = int(max(self.winfo_height(), 160) * 0.47)
        self.set_active("play" if event.y < split else "moves")

    def _on_key(self, event: tk.Event) -> str | None:
        if event.keysym in ("Up", "Down"):
            self.set_active("moves" if self._active == "play" else "play")
            return "break"
        if event.keysym in ("Return", "KP_Enter", "space"):
            self._on_change(self._active)
            return "break"
        return None


class ChessApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.game = ChessGame()
        self.orientation: Orientation = "white"
        self.redo_count = 0
        self.interaction_text = tk.StringVar(value="")
        self.panel_text = tk.StringVar(value="")
        self.action_state_text = tk.StringVar(value="")
        self._wrap_labels: list[tk.Label] = []
        self._build()
        self._refresh()

    def _build(self) -> None:
        self.root.title("Chess & Chains — Local Game")
        self.root.configure(background=WINDOW)
        self.root.geometry("1180x820")
        self.root.minsize(860, 700)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self.root, background=WINDOW, padx=22, pady=14)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        tk.Label(
            header,
            text="Chess & Chains",
            background=WINDOW,
            foreground=INK,
            font=("TkDefaultFont", FONT_SIZES["title"], "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            header,
            text="LOCAL GAME  ·  TWO PLAYERS",
            background=WINDOW,
            foreground=INK,
            font=("TkDefaultFont", FONT_SIZES["caption"], "bold"),
        ).grid(row=0, column=1, sticky="e", padx=(12, 0))

        body = tk.Frame(self.root, background=WINDOW, padx=18)
        body.grid(row=1, column=0, sticky="nsew", pady=(4, 12))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=7, minsize=490)
        body.grid_columnconfigure(1, weight=3, minsize=290)

        board_slot = tk.Frame(body, background=CHROME_YELLOW)
        board_slot.grid(row=0, column=0, sticky="nsew", padx=(0, 14), pady=(4, 10))
        board_slot.grid_rowconfigure(0, weight=1)
        board_slot.grid_columnconfigure(0, weight=1)
        board_shadow = tk.Frame(board_slot, background=SHADOW)
        board_shadow.place(x=6, y=6, relwidth=1, relheight=1, width=-6, height=-6)
        board_sheet = tk.Frame(
            board_slot,
            background=ACETATE,
            highlightbackground=INK,
            highlightthickness=1,
        )
        board_sheet.place(x=0, y=0, relwidth=1, relheight=1, width=-6, height=-6)
        board_sheet.grid_rowconfigure(1, weight=1)
        board_sheet.grid_columnconfigure(0, weight=1)

        tk.Label(
            board_sheet,
            text="TEST PIECES  ·  TEMPORARY GEOMETRIC PLACEHOLDERS",
            background=ACETATE,
            foreground=INK,
            font=("TkDefaultFont", FONT_SIZES["caption"], "bold"),
            anchor="w",
            padx=14,
            pady=9,
        ).grid(row=0, column=0, sticky="ew")
        self.board = BoardCanvas(
            board_sheet,
            self._on_move_requested,
            self._on_selection_changed,
        )
        self.board.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 10))
        tk.Label(
            board_sheet,
            textvariable=self.interaction_text,
            background=ACETATE,
            foreground=MUTED_INK,
            font=("TkDefaultFont", FONT_SIZES["caption"]),
            anchor="w",
            padx=14,
            pady=8,
        ).grid(row=2, column=0, sticky="ew")

        side_slot = tk.Frame(body, background=CHROME_YELLOW)
        side_slot.grid(row=0, column=1, sticky="nsew", pady=(4, 10))
        side_slot.grid_rowconfigure(0, weight=1)
        side_slot.grid_columnconfigure(0, weight=1)
        side_shadow = tk.Frame(side_slot, background=SHADOW)
        side_shadow.place(x=6, y=6, relwidth=1, relheight=1, width=-6, height=-6)
        side_sheet = tk.Frame(
            side_slot,
            background=ACETATE,
            highlightbackground=INK,
            highlightthickness=1,
        )
        side_sheet.place(x=0, y=0, relwidth=1, relheight=1, width=-6, height=-6)
        side_sheet.grid_rowconfigure(1, weight=1)
        side_sheet.grid_columnconfigure(0, weight=1)

        tk.Label(
            side_sheet,
            textvariable=self.panel_text,
            background=ACETATE,
            foreground=INK,
            font=("TkDefaultFont", FONT_SIZES["section"], "bold"),
            anchor="w",
            justify="left",
            padx=16,
            pady=15,
        ).grid(row=0, column=0, columnspan=2, sticky="ew")

        self.panel = tk.Frame(side_sheet, background=ACETATE, padx=14, pady=10)
        self.panel.grid(row=1, column=0, sticky="nsew")
        self.panel.grid_columnconfigure(0, weight=1)
        self.tab_rail = TabRail(side_sheet, self._show_panel)
        self.tab_rail.grid(row=0, column=2, rowspan=2, sticky="ns")
        side_sheet.grid_columnconfigure(1, minsize=8)
        side_sheet.grid_columnconfigure(2, minsize=54)

        self._build_play_panel()
        self._build_moves_panel()
        self.panel.bind("<Configure>", self._update_panel_wraplengths)
        self._show_panel("play")
        self._update_panel_wraplengths()

    def _build_play_panel(self) -> None:
        self.play_panel = tk.Frame(self.panel, background=ACETATE)
        self.play_panel.grid(row=0, column=0, sticky="nsew")
        self.play_panel.grid_columnconfigure(0, weight=1)
        lead = tk.Label(
            self.play_panel,
            text="One game, one shared board.",
            background=ACETATE,
            foreground=INK,
            font=("TkDefaultFont", FONT_SIZES["body"], "bold"),
            wraplength=300,
            anchor="w",
        )
        lead.grid(row=0, column=0, sticky="ew", pady=(0, 7))
        self._wrap_labels.append(lead)
        description = tk.Label(
            self.play_panel,
            text="The active side is shown above. Moves are checked by the local rules domain.",
            background=ACETATE,
            foreground=MUTED_INK,
            font=("TkDefaultFont", FONT_SIZES["body"]),
            wraplength=250,
            justify="left",
            anchor="w",
        )
        description.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        self._wrap_labels.append(description)

        self.new_game_button = self._button(
            self.play_panel,
            "New local game",
            self._new_game,
            role="new",
        )
        self.new_game_button.grid(row=2, column=0, sticky="ew", pady=4)
        self.undo_button = self._button(self.play_panel, "Undo move", self._undo)
        self.undo_button.grid(row=3, column=0, sticky="ew", pady=4)
        self.redo_button = self._button(self.play_panel, "Redo move", self._redo)
        self.redo_button.grid(row=4, column=0, sticky="ew", pady=4)
        self.flip_button = self._button(self.play_panel, "Flip board", self._flip_board)
        self.flip_button.grid(row=5, column=0, sticky="ew", pady=4)

        action_state = tk.Label(
            self.play_panel,
            textvariable=self.action_state_text,
            background=ACETATE,
            foreground=MUTED_INK,
            font=("TkDefaultFont", FONT_SIZES["caption"]),
            wraplength=250,
            justify="left",
            anchor="w",
        )
        action_state.grid(row=6, column=0, sticky="ew", pady=(8, 0))
        self._wrap_labels.append(action_state)
        tk.Frame(self.play_panel, height=1, background=INK).grid(
            row=7, column=0, sticky="ew", pady=(20, 12)
        )
        engine_note = tk.Label(
            self.play_panel,
            text="NO ENGINE  ·  NO NETWORK  ·  NO CLOCK",
            background=ACETATE,
            foreground=INK,
            font=("TkDefaultFont", FONT_SIZES["caption"], "bold"),
            anchor="w",
        )
        engine_note.grid(row=8, column=0, sticky="ew")
        self._wrap_labels.append(engine_note)

    def _build_moves_panel(self) -> None:
        self.moves_panel = tk.Frame(self.panel, background=ACETATE)
        self.moves_panel.grid(row=0, column=0, sticky="nsew")
        self.moves_panel.grid_rowconfigure(1, weight=1)
        self.moves_panel.grid_columnconfigure(0, weight=1)
        tk.Label(
            self.moves_panel,
            text="Move record",
            background=ACETATE,
            foreground=INK,
            font=("TkDefaultFont", FONT_SIZES["section"], "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.empty_moves_label = tk.Label(
            self.moves_panel,
            text="No moves yet. The record begins with the first legal move.",
            background=ACETATE,
            foreground=MUTED_INK,
            font=("TkDefaultFont", FONT_SIZES["body"]),
            wraplength=250,
            justify="left",
            anchor="nw",
            padx=4,
            pady=6,
        )
        self._wrap_labels.append(self.empty_moves_label)
        self.empty_moves_label.grid(row=1, column=0, sticky="new")
        list_frame = tk.Frame(self.moves_panel, background=ACETATE)
        self.move_list_frame = list_frame
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        self.move_list = tk.Listbox(
            list_frame,
            background=PAPER,
            foreground=INK,
            selectbackground=CHROME_YELLOW,
            selectforeground=INK,
            font=("TkFixedFont", 11),
            relief="solid",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=INK,
            highlightcolor=INK,
            exportselection=False,
        )
        self.move_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = tk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.move_list.yview,
            background=CHROME_YELLOW,
            troughcolor=PAPER,
            activebackground=INK,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.move_list.configure(yscrollcommand=scrollbar.set)
        list_frame.grid_remove()

    def _update_panel_wraplengths(self, _event: tk.Event | None = None) -> None:
        wraplength = max(120, min(300, self.panel.winfo_width() - 56))
        for label in self._wrap_labels:
            label.configure(wraplength=wraplength)

    def _button(
        self,
        master: tk.Misc,
        label: str,
        command,
        *,
        role: str = "neutral",
    ) -> tk.Button:
        if role not in BUTTON_ROLES:
            raise ValueError(f"Unknown button role: {role}")
        background, foreground = BUTTON_ROLES[role]
        return tk.Button(
            master,
            text=label,
            command=command,
            background=background,
            foreground=foreground,
            activebackground=INK,
            activeforeground=ACETATE,
            disabledforeground=DISABLED_INK,
            relief="solid",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=background,
            highlightcolor=INK,
            padx=10,
            pady=8,
            anchor="w",
            font=("TkDefaultFont", FONT_SIZES["body"], "bold"),
        )

    def _show_panel(self, name: str) -> None:
        for panel in (self.play_panel, self.moves_panel):
            panel.grid_remove()
        if name == "play":
            self.play_panel.grid()
        elif name == "moves":
            self.moves_panel.grid()
        else:
            raise ValueError(f"Unknown game panel: {name}")

    def _on_selection_changed(self, message: str) -> None:
        self.interaction_text.set(message)

    def _on_move_requested(self, candidates: tuple[Move, ...]) -> None:
        if len(candidates) == 1:
            self._play_move(candidates[0])
            return
        self._choose_promotion(candidates)

    def _play_move(self, move: Move) -> None:
        try:
            self.game.play(move)
        except ChessError as error:
            self.interaction_text.set(f"Move rejected: {error}")
            self._refresh()
            return
        self.redo_count = 0
        self._refresh()

    def _choose_promotion(self, candidates: Sequence[Move]) -> None:
        promotions = tuple(move for move in candidates if move.promotion is not None)
        if not promotions:
            self.interaction_text.set("Move choice is ambiguous; select a square again.")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Choose promotion")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.configure(background=ACETATE)
        tk.Label(
            dialog,
            text="Choose the piece for promotion",
            background=ACETATE,
            foreground=INK,
            font=("TkDefaultFont", FONT_SIZES["body"], "bold"),
            padx=18,
            pady=14,
        ).grid(row=0, column=0, columnspan=len(promotions), sticky="ew")
        chosen: list[Move] = []
        for column, move in enumerate(promotions):
            label = move.promotion.name.title() if move.promotion else "Piece"
            self._button(
                dialog,
                label,
                lambda candidate=move: (chosen.append(candidate), dialog.destroy()),
                role="neutral",
            ).grid(row=1, column=column, padx=6, pady=(0, 14))
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        try:
            dialog.grab_set()
            self.root.wait_window(dialog)
        finally:
            try:
                dialog.grab_release()
            except tk.TclError:
                pass
        if chosen:
            self._play_move(chosen[0])

    def _new_game(self) -> None:
        if (self.game.moves or self.redo_count) and not messagebox.askyesno(
            "Start a new game?",
            "The current local game, including undone moves, will be replaced.",
            parent=self.root,
        ):
            return
        self.game = ChessGame()
        self.redo_count = 0
        self._refresh()

    def _undo(self) -> None:
        try:
            self.game.undo()
        except ChessError as error:
            self.interaction_text.set(str(error))
            return
        self.redo_count += 1
        self._refresh()

    def _redo(self) -> None:
        if self.redo_count <= 0:
            return
        try:
            self.game.redo()
        except ChessError as error:
            self.interaction_text.set(str(error))
            self.redo_count = 0
        else:
            self.redo_count -= 1
        self._refresh()

    def _flip_board(self) -> None:
        self.orientation = "black" if self.orientation == "white" else "white"
        self.board.set_orientation(self.orientation)
        self.interaction_text.set(
            "Black's side is at the bottom." if self.orientation == "black"
            else "White's side is at the bottom."
        )

    def _refresh(self) -> None:
        outcome = self.game.outcome()
        legal_moves = (
            self.game.rules.legal_moves(self.game.state)
            if outcome.status is GameStatus.ACTIVE
            else ()
        )
        last_move = self.game.moves[-1] if self.game.moves else None
        self.board.set_position(
            self.game.state,
            legal_moves,
            last_move,
            outcome.in_check,
        )
        self.panel_text.set(self._status_label(outcome.status, outcome.in_check, outcome.winner))
        if not self.game.moves and self.redo_count:
            action_state = "No earlier move to undo; redo is available."
        elif not self.game.moves:
            action_state = "Undo is unavailable before the first move."
        elif not self.redo_count:
            action_state = "Redo is unavailable until a move has been undone."
        else:
            action_state = ""
        self.action_state_text.set(action_state)
        self._update_move_list()
        self.undo_button.configure(
            state=tk.NORMAL if self.game.moves else tk.DISABLED
        )
        self.redo_button.configure(
            state=tk.NORMAL if self.redo_count else tk.DISABLED
        )

    def _status_label(
        self,
        status: GameStatus,
        in_check: bool,
        winner: Color | None,
    ) -> str:
        if status is GameStatus.ACTIVE:
            side = self.game.state.turn.name.title()
            return f"{'Check — ' if in_check else ''}{side} to move"
        if status is GameStatus.CHECKMATE:
            return f"{winner.name.title()} wins by checkmate" if winner else "Checkmate"
        if status is GameStatus.STALEMATE:
            return "Draw by stalemate"
        if status is GameStatus.DRAW_INSUFFICIENT_MATERIAL:
            return "Draw by insufficient material"
        if status is GameStatus.DRAW_FIVEFOLD_REPETITION:
            return "Draw by fivefold repetition"
        if status is GameStatus.DRAW_SEVENTY_FIVE_MOVE:
            return "Draw by the 75-move rule"
        if status is GameStatus.DRAW_CLAIMED:
            return "Draw claimed"
        if status is GameStatus.RESIGNED:
            return f"{winner.name.title()} wins by resignation" if winner else "Game resigned"
        return "Game finished"

    def _update_move_list(self) -> None:
        san_moves: list[str] = []
        state = self.game.initial_state
        for move in self.game.moves:
            san_moves.append(to_san(state, move, self.game.rules))
            state = self.game.rules.apply(state, move)
        rows = []
        for index in range(0, len(san_moves), 2):
            white = san_moves[index]
            black = san_moves[index + 1] if index + 1 < len(san_moves) else ""
            rows.append(f"{index // 2 + 1:>2}. {white:<8} {black}")
        self.move_list.delete(0, tk.END)
        for row in rows:
            self.move_list.insert(tk.END, row)
        if rows:
            self.empty_moves_label.grid_remove()
            self.move_list_frame.grid()
            self.move_list.selection_set(len(rows) - 1)
            self.move_list.see(len(rows) - 1)
        else:
            self.move_list_frame.grid_remove()
            self.empty_moves_label.grid()


def launch() -> None:
    root = tk.Tk()
    ChessApp(root)
    root.mainloop()
