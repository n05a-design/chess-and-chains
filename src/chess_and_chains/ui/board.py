"""Keyboard-operable chessboard canvas with a swappable piece renderer."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Literal, Sequence

from ..chess import GameState, Move, Piece, PieceType, square_name
from ..i18n import Translator
from .board_artwork import MAX_BOARD_PREVIEW_SIZE, BoardArtwork, Marble2DArtwork
from .pieces import OwnerSvgPieces, PieceRenderer, get_piece_set
from .theme import (
    LIGHT_THEME,
    ThemePalette,
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
    """Resizable, keyboard-operable chessboard with an exchangeable piece renderer."""

    def __init__(
        self,
        master: tk.Misc,
        on_move_requested: MoveRequest,
        on_selection_changed: SelectionCallback | None = None,
        renderer: PieceRenderer | None = None,
        *,
        artwork: BoardArtwork | None = None,
        translator: Translator | None = None,
        theme: ThemePalette = LIGHT_THEME,
    ) -> None:
        self._theme = theme
        super().__init__(
            master,
            background=theme.acetate,
            highlightthickness=0,
            takefocus=True,
            borderwidth=0,
        )
        self._on_move_requested = on_move_requested
        self._on_selection_changed = on_selection_changed
        self.t = translator if translator is not None else Translator("en")
        self.renderer: PieceRenderer = OwnerSvgPieces() if renderer is None else renderer
        self._artwork = artwork
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
        state: GameState | None,
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
        self._notify_focus()
        self.redraw()

    def set_hint(self, square: int | None) -> None:
        """Mark a square (e.g. the puzzle hint's source square)."""
        self._hint_square = square
        self.redraw()

    def set_theme(self, theme: ThemePalette) -> None:
        """Apply a Glide ThemePalette to the board canvas and redraw."""
        self._theme = theme
        self.configure(background=theme.acetate)
        self.redraw()

    @property
    def piece_set(self) -> str:
        return getattr(self.renderer, "piece_set", "original")

    @property
    def piece_view(self) -> str:
        return "top" if getattr(self.renderer, "top_view", False) else "front"

    def set_piece_set(self, piece_set: str) -> None:
        """Swap piece set without altering game or board state."""
        info = get_piece_set(piece_set)
        if hasattr(self.renderer, "set_piece_set"):
            self.renderer.set_piece_set(info.set_id)
        else:
            self.renderer = OwnerSvgPieces(piece_set=info.set_id)
        self.redraw()

    def set_piece_view(self, view: str) -> None:
        """Backward-compatible view switcher."""
        target = "top" if view == "top" else "original"
        self.set_piece_set(target)

    def set_piece_renderer(self, renderer: PieceRenderer) -> None:
        """Swap the active 2D piece renderer without altering the game or board state."""
        self.renderer = renderer
        self.redraw()

    def set_artwork(self, artwork: BoardArtwork | Marble2DArtwork | None) -> None:
        """Swap the 2D board background artwork without altering the game or board state."""
        self._artwork = artwork
        self.redraw()

    def square_bounds(self, square: int) -> tuple[float, float, float, float]:
        """Return ``(x0, y0, x1, y1)`` pixel bounds for ``square`` in the current 2D layout."""
        column, row = screen_cell(square, self._orientation)
        size = self._square_size
        x0 = self._board_x + column * size
        y0 = self._board_y + row * size
        return x0, y0, x0 + size, y0 + size

    def square_center(self, square: int) -> tuple[float, float]:
        """Return ``(center_x, center_y)`` derived strictly from ``square_bounds(square)``."""
        x0, y0, x1, y1 = self.square_bounds(square)
        return (x0 + x1) / 2.0, (y0 + y1) / 2.0

    def _marble_tint_color(self) -> str | None:
        return self._theme.brand_blue

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
        self._notify_focus()
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        width = max(self.winfo_width(), 1)
        height = max(self.winfo_height(), 1)
        usable = max(0.0, min(width - 72, height - 72))
        if self._artwork is not None:
            usable = min(usable, MAX_BOARD_PREVIEW_SIZE)
        if usable < 8:
            self._square_size = 0.0
            return
        # Snap square size to an integer (even when >= 16) and origin to integer pixels
        # so square centers and concentric move markers align without sub-pixel drift.
        tile = (int(usable) // 16) * 2 if usable >= 16 else max(1, int(usable) // 8)
        usable = float(tile * 8)
        self._square_size = float(tile)
        self._board_x = float(round((width - usable) / 2 + 12))
        self._board_y = float(round((height - usable) / 2 + 12))
        self._draw_board()
        if self._state is not None:
            self._draw_position()
        self._draw_focus()
        self._draw_coordinates()
        outline = self._theme.focus_ink if self._has_focus else self._theme.muted_ink
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
        t = self._theme
        artwork_item = None
        if self._artwork is not None:
            if isinstance(self._artwork, Marble2DArtwork):
                image = self._artwork.image(
                    self,
                    int(size),
                    flipped=self._orientation == "black",
                    tint_color=self._marble_tint_color(),
                )
                tags: tuple[str, ...] = ("board-artwork", "marble-2d-board")
            else:
                image = self._artwork.image(self, int(size), flipped=self._orientation == "black")
                tags = ("board-artwork",)
            artwork_item = self.create_image(self._board_x, self._board_y, anchor="nw", image=image, tags=tags)
        half = size / 2.0
        for row in range(8):
            for column in range(8):
                square = self._square_for_cell(column, row)
                x1, y1, x2, y2 = self.square_bounds(square)
                center_x, center_y = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                fill = t.square_light if (row + column) % 2 == 0 else t.square_dark
                base = self.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=fill,
                    outline=fill,
                )
                if artwork_item is not None:
                    self.tag_lower(base, artwork_item)
                if self._last_move is not None and square in (
                    self._last_move.from_square,
                    self._last_move.to_square,
                ):
                    self._draw_last_move(x1, y1, size)
                if square == self._selected:
                    sel_outer = max(2, round(size * 0.04))
                    sel_inner = sel_outer + max(3, round(size * 0.05))
                    self.create_rectangle(
                        center_x - half + sel_outer,
                        center_y - half + sel_outer,
                        center_x + half - sel_outer,
                        center_y + half - sel_outer,
                        outline=t.ink,
                        width=max(3, round(size * 0.04)),
                        tags=("selected-square",),
                    )
                    self.create_rectangle(
                        center_x - half + sel_inner,
                        center_y - half + sel_inner,
                        center_x + half - sel_inner,
                        center_y + half - sel_inner,
                        fill=t.action_new_bg,
                        stipple="gray25",
                        outline="",
                        tags=("selected-square",),
                    )

    def _draw_focus(self) -> None:
        if not self._has_focus or self._focused_square is None:
            return
        t = self._theme
        size = self._square_size
        half = size / 2.0
        center_x, center_y = self.square_center(self._focused_square)
        inset = min(5, max(2, round(size * 0.1)))
        bounds = (center_x - half + inset, center_y - half + inset, center_x + half - inset, center_y + half - inset)
        self.create_rectangle(*bounds, outline=t.paper, width=4, tags=("square-focus",))
        self.create_rectangle(*bounds, outline=t.focus_ink, dash=(4, 3), width=2, tags=("square-focus",))

    def _draw_position(self) -> None:
        if self._state is None:
            return
        t = self._theme
        size = self._square_size
        half = size / 2.0
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
            center_x, center_y = self.square_center(square)
            self.renderer.draw(
                self,
                center_x,
                center_y,
                size,
                piece,
            )

        for destination in {move.to_square for move in legal_from_selected}:
            center_x, center_y = self.square_center(destination)
            target_piece = self._state.board[destination]
            is_en_passant = any(
                move.to_square == destination
                and self._state.board[move.from_square] is not None
                and self._state.board[move.from_square].kind is PieceType.PAWN
                and self._state.en_passant == destination
                for move in legal_from_selected
            )
            if target_piece is not None or is_en_passant:
                radius = max(7, round(size * 0.42))
                inner = max(5, round(size * 0.35))
                self.create_oval(
                    center_x - radius,
                    center_y - radius,
                    center_x + radius,
                    center_y + radius,
                    outline=t.legal_mark,
                    width=max(3, round(size * 0.045)),
                    tags=("legal-target", "legal-capture"),
                )
                self.create_oval(
                    center_x - inner,
                    center_y - inner,
                    center_x + inner,
                    center_y + inner,
                    outline=t.paper,
                    width=max(1, round(size * 0.018)),
                    tags=("legal-target", "legal-capture"),
                )
            else:
                radius = max(4, round(size * 0.13))
                dot = max(2, round(size * 0.06))
                self.create_oval(
                    center_x - radius,
                    center_y - radius,
                    center_x + radius,
                    center_y + radius,
                    fill=t.paper,
                    outline=t.legal_mark,
                    width=max(2, round(size * 0.025)),
                    tags=("legal-target", "legal-move"),
                )
                self.create_oval(
                    center_x - dot,
                    center_y - dot,
                    center_x + dot,
                    center_y + dot,
                    fill=t.legal_mark,
                    outline="",
                    tags=("legal-target", "legal-move"),
                )

        if self._hint_square is not None:
            center_x, center_y = self.square_center(self._hint_square)
            inset = max(2, round(size * 0.08))
            self.create_rectangle(
                center_x - half + inset,
                center_y - half + inset,
                center_x + half - inset,
                center_y + half - inset,
                outline=t.focus_ink,
                dash=(2, 4),
                width=max(2, round(size * 0.04)),
                tags=("hint",),
            )

        if self._in_check:
            king_square = self._state.king_square(self._state.turn)
            center_x, center_y = self.square_center(king_square)
            outer_inset = max(2, round(size * 0.04))
            inner_inset = outer_inset + max(4, round(size * 0.06))
            self.create_rectangle(
                center_x - half + outer_inset,
                center_y - half + outer_inset,
                center_x + half - outer_inset,
                center_y + half - outer_inset,
                outline=t.brand_red,
                width=max(3, round(size * 0.04)),
                tags=("check-square",),
            )
            self.create_rectangle(
                center_x - half + inner_inset,
                center_y - half + inner_inset,
                center_x + half - inner_inset,
                center_y + half - inner_inset,
                outline=t.paper,
                dash=(5, 3),
                width=2,
                tags=("check-square",),
            )

        if self._drag_active and self._drag_pointer and self._press_square is not None:
            piece = self._state.board[self._press_square]
            if piece is not None:
                self.renderer.draw(
                    self,
                    self._drag_pointer[0],
                    self._drag_pointer[1],
                    size,
                    piece,
                    lifted=True,
                )

    def _draw_last_move(self, x: float, y: float, size: float) -> None:
        self.create_rectangle(
            x,
            y,
            x + size,
            y + size,
            fill=self._theme.last_move,
            stipple="gray25",
            outline="",
            tags=("last-move",),
        )

    def _draw_coordinates(self) -> None:
        size = self._square_size
        t = self._theme
        for row in range(8):
            rank = 8 - row if self._orientation == "white" else row + 1
            self.create_text(
                self._board_x - 12,
                self._board_y + (row + 0.5) * size,
                text=str(rank),
                fill=t.ink,
                font=("TkFixedFont", -max(8, int(size * 0.20))),
            )
        for column in range(8):
            file_index = column if self._orientation == "white" else 7 - column
            self.create_text(
                self._board_x + (column + 0.5) * size,
                self._board_y + 8 * size + 12,
                text=chr(ord("a") + file_index),
                fill=t.ink,
                font=("TkFixedFont", -max(8, int(size * 0.20))),
            )

    def _on_configure(self, _event: tk.Event) -> None:
        self.redraw()

    def _on_focus_in(self, _event: tk.Event) -> None:
        self._has_focus = True
        square = self._focused_square
        self._set_focus_square(self._initial_focus_square() if square is None else square)

    def _on_focus_out(self, _event: tk.Event) -> None:
        self._has_focus = False
        self._notify_selection("")
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
            self._set_focus_square(self._initial_focus_square())
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
            self._notify_focus()
        else:
            count = len({move.to_square for move in self._legal_moves if move.from_square == square})
            key = "board.selected_one" if count == 1 else "board.selected"
            self._notify_selection(self.t(key, square=square_name(square), count=count))
        self.redraw()

    def _initial_focus_square(self) -> int:
        return 12 if self._orientation == "white" else 52  # e2 / e7

    def _set_focus_square(self, square: int) -> None:
        self._focused_square = square
        self._notify_focus()
        self.redraw()

    def _notify_focus(self) -> None:
        square = self._focused_square
        if not self._has_focus or square is None:
            self._notify_selection("")
            return
        piece = self._state.board[square] if self._state is not None else None
        if piece is None:
            self._notify_selection(self.t("board.focus_empty", square=square_name(square)))
        else:
            color = self.t(f"side.{piece.color.name.lower()}")
            name = self.t(f"piece.{piece.kind.name.lower()}")
            self._notify_selection(self.t("board.focus_piece", square=square_name(square), color=color, piece=name))

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
