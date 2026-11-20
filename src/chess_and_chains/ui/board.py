"""Accessible chessboard canvas and test-piece rendering."""

# W06 direction contract:
# THESIS: The board is a working position under a pale acetate-tint leaf; the
# tabbed manual separates play controls from notation without hiding the game.
# OWN-WORLD: Chrome yellow marks the current section and new-game action; calm
# neutral surfaces, stepped tabs, punched focus marks, and offset shadows.
# Colors are provisional; native fonts and original Tk code avoid unapproved
# assets and Glide-shell reuse.
# STORY: Two local players see whose turn it is, make a domain-validated move,
# and follow the resulting position and notation without an engine or network.
# FIRST VIEWPORT: A large 8x8 board fills the left sheet; an acetate side leaf
# carries turn status, controls, and a tabbed move register on the right.
# FORM: Tabbed-manual system; fixed live board workspace, with no staged
# transit, verdict, or pipeline pattern because each would obscure play.

from __future__ import annotations

import tkinter as tk
from typing import Callable, Literal, Sequence

from ..chess import GameState, Move, Piece, PieceType
from .pieces import GeometricTestPieces, PieceRenderer
from .theme import (
    CHROME_YELLOW,
    FOCUS_INK,
    INK,
    LAST_MOVE,
    LEGAL_MARK,
    MUTED_INK,
    PAPER,
    SQUARE_DARK,
    SQUARE_LIGHT,
)

Orientation = Literal["white", "black"]
MoveRequest = Callable[[tuple[Move, ...]], None]
SelectionCallback = Callable[[str], None]


def square_at_point(
    x: float,
    y: float,
    board_x: float,
    board_y: float,
    square_size: float,
    orientation: Orientation = "white",
) -> int | None:
    """Return the domain square under a point, or None outside the board."""
    if square_size <= 0:
        return None
    column = int((x - board_x) // square_size)
    row = int((y - board_y) // square_size)
    if not (0 <= column < 8 and 0 <= row < 8):
        return None
    file_index = column if orientation == "white" else 7 - column
    rank_index = 7 - row if orientation == "white" else row
    return rank_index * 8 + file_index


def screen_cell(square: int, orientation: Orientation = "white") -> tuple[int, int]:
    """Return the board's screen column and row for a domain square."""
    if not 0 <= square < 64:
        raise ValueError("A chess square index must be between 0 and 63.")
    file_index, rank_index = square % 8, square // 8
    if orientation == "white":
        return file_index, 7 - rank_index
    return 7 - file_index, rank_index


def moves_between(
    legal_moves: Sequence[Move], source: int, destination: int
) -> tuple[Move, ...]:
    """Return the domain-validated candidates for one board interaction."""
    return tuple(
        move
        for move in legal_moves
        if move.from_square == source and move.to_square == destination
    )


class BoardCanvas(tk.Canvas):
    """Resizable, keyboard-operable chessboard with temporary letter pieces."""

    def __init__(
        self,
        master: tk.Misc,
        on_move_requested: MoveRequest,
        on_selection_changed: SelectionCallback | None = None,
        renderer: PieceRenderer | None = None,
    ) -> None:
        super().__init__(
            master,
            background=PAPER,
            highlightthickness=0,
            takefocus=True,
            borderwidth=0,
        )
        self._on_move_requested = on_move_requested
        self._on_selection_changed = on_selection_changed
        self.renderer: PieceRenderer = renderer or GeometricTestPieces()
        self._hint_square: int | None = None
        self._state: GameState | None = None
        self._legal_moves: tuple[Move, ...] = ()
        self._last_move: Move | None = None
        self._in_check = False
        self._orientation: Orientation = "white"
        self._selected: int | None = None
        self._focused_square: int | None = None
        self._has_focus = False
        self._press_square: int | None = None
        self._press_point: tuple[int, int] | None = None
        self._drag_active = False
        self._drag_pointer: tuple[int, int] | None = None
        self._board_x = 0.0
        self._board_y = 0.0
        self._square_size = 0.0

        self.bind("<Configure>", self._on_configure)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<ButtonPress-1>", self._on_button_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_button_release)
        self.bind("<KeyPress>", self._on_key)

    @property
    def selected_square(self) -> int | None:
        return self._selected

    def set_position(
        self,
        state: GameState,
        legal_moves: Sequence[Move],
        last_move: Move | None,
        in_check: bool,
    ) -> None:
        self._state = state
        self._legal_moves = tuple(legal_moves)
        self._last_move = last_move
        self._in_check = in_check
        self._selected = None
        self._hint_square = None
        self._drag_active = False
        self._drag_pointer = None
        self._notify_selection("")
        self.redraw()

    def set_hint(self, square: int | None) -> None:
        """Mark a square (e.g. the puzzle hint's source square)."""
        self._hint_square = square
        self.redraw()

    @property
    def orientation(self) -> Orientation:
        return self._orientation

    def set_orientation(self, orientation: Orientation) -> None:
        if orientation not in ("white", "black"):
            raise ValueError(f"Unknown board orientation: {orientation}")
        self._orientation = orientation
        self.redraw()

    def clear_selection(self) -> None:
        self._selected = None
        self._drag_active = False
        self._drag_pointer = None
        self._notify_selection("")
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        width = max(self.winfo_width(), 1)
        height = max(self.winfo_height(), 1)
        usable = max(0.0, min(width - 72, height - 72))
        if usable < 8:
            return
        self._square_size = usable / 8
        self._board_x = (width - usable) / 2 + 12
        self._board_y = (height - usable) / 2 + 12
        self._draw_board()
        if self._state is not None:
            self._draw_position()
        self._draw_coordinates()
        outline = FOCUS_INK if self._has_focus else MUTED_INK
        self.create_rectangle(
            self._board_x - 2,
            self._board_y - 2,
            self._board_x + usable + 2,
            self._board_y + usable + 2,
            outline=outline,
            width=3 if self._has_focus else 1,
        )

    def _draw_board(self) -> None:
        size = self._square_size
        for row in range(8):
            for column in range(8):
                x1 = self._board_x + column * size
                y1 = self._board_y + row * size
                fill = SQUARE_LIGHT if (row + column) % 2 == 0 else SQUARE_DARK
                square = self._square_for_cell(column, row)
                self.create_rectangle(
                    x1,
                    y1,
                    x1 + size,
                    y1 + size,
                    fill=fill,
                    outline=fill,
                )
                if self._last_move is not None and square in (
                    self._last_move.from_square,
                    self._last_move.to_square,
                ):
                    self._draw_last_move(x1, y1, size)
                if square == self._selected:
                    self.create_rectangle(
                        x1 + 2,
                        y1 + 2,
                        x1 + size - 2,
                        y1 + size - 2,
                        outline=INK,
                        width=max(3, int(size * 0.04)),
                    )
                    self.create_rectangle(
                        x1 + 6,
                        y1 + 6,
                        x1 + size - 6,
                        y1 + size - 6,
                        fill=CHROME_YELLOW,
                        stipple="gray25",
                        outline="",
                    )
                if square == self._focused_square:
                    self.create_rectangle(
                        x1 + 5,
                        y1 + 5,
                        x1 + size - 5,
                        y1 + size - 5,
                        outline=FOCUS_INK,
                        dash=(3, 2),
                        width=2,
                    )

    def _draw_position(self) -> None:
        if self._state is None:
            return
        size = self._square_size
        legal_from_selected = (
            tuple(move for move in self._legal_moves if move.from_square == self._selected)
            if self._selected is not None
            else ()
        )
        for square, piece in enumerate(self._state.board):
            if piece is None:
                continue
            if self._drag_active and square == self._press_square:
                continue
            column, row = screen_cell(square, self._orientation)
            self._draw_test_piece(
                self._board_x + (column + 0.5) * size,
                self._board_y + (row + 0.5) * size,
                size,
                piece,
            )

        for destination in {move.to_square for move in legal_from_selected}:
            column, row = screen_cell(destination, self._orientation)
            center_x = self._board_x + (column + 0.5) * size
            center_y = self._board_y + (row + 0.5) * size
            target_piece = self._state.board[destination]
            is_en_passant = any(
                move.to_square == destination
                and self._state.board[move.from_square] is not None
                and self._state.board[move.from_square].kind is PieceType.PAWN
                and self._state.en_passant == destination
                for move in legal_from_selected
            )
            if target_piece is not None or is_en_passant:
                radius = size * 0.32
                self.create_oval(
                    center_x - radius,
                    center_y - radius,
                    center_x + radius,
                    center_y + radius,
                    outline=LEGAL_MARK,
                    width=max(3, int(size * 0.04)),
                )
                inner = radius * 0.78
                self.create_oval(
                    center_x - inner,
                    center_y - inner,
                    center_x + inner,
                    center_y + inner,
                    outline=PAPER,
                    width=max(1, int(size * 0.018)),
                )
            else:
                radius = size * 0.1
                self.create_oval(
                    center_x - radius,
                    center_y - radius,
                    center_x + radius,
                    center_y + radius,
                    fill=PAPER,
                    outline=LEGAL_MARK,
                    width=max(2, int(size * 0.025)),
                )
                dot = radius * 0.45
                self.create_oval(
                    center_x - dot,
                    center_y - dot,
                    center_x + dot,
                    center_y + dot,
                    fill=LEGAL_MARK,
                    outline=LEGAL_MARK,
                )

        if self._hint_square is not None:
            column, row = screen_cell(self._hint_square, self._orientation)
            inset = size * 0.08
            self.create_rectangle(
                self._board_x + column * size + inset,
                self._board_y + row * size + inset,
                self._board_x + (column + 1) * size - inset,
                self._board_y + (row + 1) * size - inset,
                outline=FOCUS_INK,
                dash=(2, 4),
                width=max(2, int(size * 0.04)),
                tags=("hint",),
            )

        if self._in_check:
            king_square = self._state.king_square(self._state.turn)
            column, row = screen_cell(king_square, self._orientation)
            self.create_rectangle(
                self._board_x + column * size + 3,
                self._board_y + row * size + 3,
                self._board_x + (column + 1) * size - 3,
                self._board_y + (row + 1) * size - 3,
                outline=INK,
                width=max(3, int(size * 0.04)),
            )
            self.create_rectangle(
                self._board_x + column * size + 8,
                self._board_y + row * size + 8,
                self._board_x + (column + 1) * size - 8,
                self._board_y + (row + 1) * size - 8,
                outline=PAPER,
                dash=(5, 3),
                width=2,
            )

        if self._drag_active and self._drag_pointer and self._press_square is not None:
            piece = self._state.board[self._press_square]
            if piece is not None:
                self._draw_test_piece(
                    self._drag_pointer[0],
                    self._drag_pointer[1],
                    size,
                    piece,
                    lifted=True,
                )

    def _draw_test_piece(
        self,
        center_x: float,
        center_y: float,
        square_size: float,
        piece: Piece,
        *,
        lifted: bool = False,
    ) -> None:
        """Delegate to the exchangeable piece renderer (name kept for compatibility)."""
        self.renderer.draw(self, center_x, center_y, square_size, piece, lifted=lifted)

    def _draw_last_move(self, x: float, y: float, size: float) -> None:
        self.create_rectangle(
            x,
            y,
            x + size,
            y + size,
            fill=LAST_MOVE,
            stipple="gray25",
            outline="",
        )

    def _draw_coordinates(self) -> None:
        size = self._square_size
        for row in range(8):
            rank = 8 - row if self._orientation == "white" else row + 1
            self.create_text(
                self._board_x - 12,
                self._board_y + (row + 0.5) * size,
                text=str(rank),
                fill=INK,
                font=("TkFixedFont", max(8, int(size * 0.15))),
            )
        for column in range(8):
            file_index = column if self._orientation == "white" else 7 - column
            self.create_text(
                self._board_x + (column + 0.5) * size,
                self._board_y + 8 * size + 12,
                text=chr(ord("a") + file_index),
                fill=INK,
                font=("TkFixedFont", max(8, int(size * 0.15))),
            )

    def _on_configure(self, _event: tk.Event) -> None:
        self.redraw()

    def _on_focus_in(self, _event: tk.Event) -> None:
        self._has_focus = True
        self.redraw()

    def _on_focus_out(self, _event: tk.Event) -> None:
        self._has_focus = False
        self.redraw()

    def _on_button_press(self, event: tk.Event) -> None:
        self.focus_set()
        square = self._square_at(event.x, event.y)
        self._press_square = square
        self._press_point = (event.x, event.y)
        self._drag_active = False
        self._drag_pointer = None
        if square is not None:
            self._set_focus_square(square)
            if self._is_current_side_piece(square):
                self._set_selection(square)

    def _on_drag(self, event: tk.Event) -> None:
        if self._press_point is None or self._press_square is None:
            return
        if self._selected != self._press_square:
            return
        moved_x = abs(event.x - self._press_point[0])
        moved_y = abs(event.y - self._press_point[1])
        if moved_x + moved_y >= 5:
            self._drag_active = True
            self._drag_pointer = (event.x, event.y)
            self.redraw()

    def _on_button_release(self, event: tk.Event) -> None:
        target = self._square_at(event.x, event.y)
        source = self._press_square
        was_drag = self._drag_active
        self._press_square = None
        self._press_point = None
        self._drag_active = False
        self._drag_pointer = None
        if target is None:
            self.redraw()
            return
        self._set_focus_square(target)
        if was_drag and source is not None and target != source:
            self._request_move(source, target)
        else:
            self._handle_square(target)
        self.redraw()

    def _on_key(self, event: tk.Event) -> str | None:
        key = event.keysym
        if key in ("Left", "Right", "Up", "Down"):
            self._move_focus(key)
            return "break"
        if key in ("Return", "KP_Enter", "space"):
            self._activate_focus()
            return "break"
        if key == "Escape":
            self.clear_selection()
            return "break"
        return None

    def _move_focus(self, direction: str) -> None:
        if self._focused_square is None:
            start = 12 if self._orientation == "white" else 52
            self._set_focus_square(start)
            return
        column, row = screen_cell(self._focused_square, self._orientation)
        if direction == "Left":
            column = max(0, column - 1)
        elif direction == "Right":
            column = min(7, column + 1)
        elif direction == "Up":
            row = max(0, row - 1)
        else:
            row = min(7, row + 1)
        self._set_focus_square(self._square_for_cell(column, row))

    def _activate_focus(self) -> None:
        if self._focused_square is None:
            self._move_focus("Right")
            return
        if self._selected is not None:
            candidates = moves_between(
                self._legal_moves, self._selected, self._focused_square
            )
            if candidates:
                self._request_move(self._selected, self._focused_square)
                return
        self._handle_square(self._focused_square)

    def _handle_square(self, square: int) -> None:
        if self._selected is not None:
            candidates = moves_between(self._legal_moves, self._selected, square)
            if candidates:
                self._request_move(self._selected, square)
                return
        if self._is_current_side_piece(square):
            self._set_selection(square)
        else:
            self._set_selection(None)

    def _request_move(self, source: int, destination: int) -> None:
        candidates = moves_between(self._legal_moves, source, destination)
        if candidates:
            self._on_move_requested(candidates)
        elif self._is_current_side_piece(destination):
            self._set_selection(destination)

    def _is_current_side_piece(self, square: int) -> bool:
        if self._state is None:
            return False
        piece = self._state.board[square]
        return piece is not None and piece.color is self._state.turn

    def _set_selection(self, square: int | None) -> None:
        self._selected = square
        if square is None:
            self._notify_selection("")
        else:
            count = sum(move.from_square == square for move in self._legal_moves)
            self._notify_selection(
                f"Selected {self._square_name(square)}; {count} legal destinations."
            )
        self.redraw()

    def _set_focus_square(self, square: int) -> None:
        self._focused_square = square
        self._notify_selection(f"Focus {self._square_name(square)}.")
        self.redraw()

    def _notify_selection(self, message: str) -> None:
        if self._on_selection_changed is not None:
            self._on_selection_changed(message)

    def _square_at(self, x: float, y: float) -> int | None:
        return square_at_point(
            x,
            y,
            self._board_x,
            self._board_y,
            self._square_size,
            self._orientation,
        )

    def _square_for_cell(self, column: int, row: int) -> int:
        file_index = column if self._orientation == "white" else 7 - column
        rank_index = 7 - row if self._orientation == "white" else row
        return rank_index * 8 + file_index

    @staticmethod
    def _square_name(square: int) -> str:
        return f"{chr(ord('a') + square % 8)}{square // 8 + 1}"
