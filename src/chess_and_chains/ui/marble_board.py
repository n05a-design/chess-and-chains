"""Native Tk projection of the local marble board and its engraved plates."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

from collections import OrderedDict
from importlib.resources import files
from math import atan2, ceil, cos, floor, pi, sin
import tkinter as tk

from ..chess import Color, Piece
from .board import BoardCanvas, screen_cell
from .piece_contract import PIECE_FILE_NAMES
from .theme import ThemePalette

REFERENCE_PIXELS = 160
ANGLE = -pi / 12
TILT = 0.72
PROJECTION = (cos(ANGLE), sin(ANGLE) * TILT, -sin(ANGLE), cos(ANGLE) * TILT)
BORDER = 0.32
PLATE_SIZE = 0.86
PLATE_RADIUS = PLATE_SIZE * 115.3 / 260
PLATE_DEPTH = 0.105
BOARD_DEPTH = 0.22
_LEFT_ANGLE = atan2(PROJECTION[2], PROJECTION[0]) + pi


def project(column: float, row: float) -> tuple[float, float]:
    a, b, c, d = PROJECTION
    return a * column + c * row, b * column + d * row


_PLATE_FRONT = tuple(project(PLATE_RADIUS * cos(_LEFT_ANGLE - i * pi / 16),
                             PLATE_RADIUS * sin(_LEFT_ANGLE - i * pi / 16)) for i in range(17))


def board_frame() -> tuple[int, int, int, int]:
    """Return the atlas width, height and projected a8 corner in pixels."""
    lo, hi = -BORDER, 8 + BORDER
    corners = [project(x, y) for x in (lo, hi) for y in (lo, hi)]
    left = floor(min(x for x, _ in corners) * REFERENCE_PIXELS) - 2
    top = floor(min(y for _, y in corners) * REFERENCE_PIXELS) - 2
    right = ceil(max(x for x, _ in corners) * REFERENCE_PIXELS) + 2
    bottom = ceil(max(y for _, y in corners) * REFERENCE_PIXELS) + 2
    return right - left, bottom - top, -left, -top


def plate_frame() -> tuple[int, int, int, int]:
    """Return the atlas tile width, height and face center in pixels."""
    corners = [project(x, y) for x in (-PLATE_SIZE / 2, PLATE_SIZE / 2)
               for y in (-PLATE_SIZE / 2, PLATE_SIZE / 2)]
    half_width = ceil(max(abs(x) for x, _ in corners) * REFERENCE_PIXELS) + 2
    half_height = ceil(max(abs(y) for _, y in corners) * REFERENCE_PIXELS) + 2
    return 2 * half_width, 2 * half_height, half_width, half_height


class MarbleBoardCanvas(BoardCanvas):
    """Use identical move, keyboard, and selection handling in both views."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.marble = False
        self._masters: dict[str, tk.PhotoImage] = {}
        self._images: OrderedDict[tuple[int, str], tk.PhotoImage] = OrderedDict()
        self._factor = 1
        self._board_size = board_frame()
        self._plate_size = plate_frame()

    def set_marble(self, enabled: bool) -> None:
        if enabled and not self._masters:
            assets = files(__package__).joinpath("marble_assets")
            # Assign only once both parts have loaded, so a read failure leaves the normal board usable.
            self._masters = {
                name: tk.PhotoImage(master=self, data=assets.joinpath(f"{name}.png").read_bytes(), format="png")
                for name in ("white", "black", "plates")
            }
        self.marble = enabled
        self._press_square = None
        self._press_point = None
        self._drag_active = False
        self._drag_pointer = None
        self.configure(background=self._theme.window if enabled else self._theme.acetate)
        self.redraw()

    def set_theme(self, theme: ThemePalette) -> None:
        self._theme = theme
        self.configure(background=theme.window if self.marble else theme.acetate)
        self.redraw()

    def _image(self, name: str) -> tk.PhotoImage:
        key = self._factor, name
        if key not in self._images:
            if name in ("white", "black"):
                atlas, (width, height, _, _) = name, self._board_size
                left, top = 0, 0
            else:
                atlas, (width, height, _, _) = "plates", self._plate_size
                index = PIECE_FILE_NAMES.index(name)
                left, top = (index % 6) * width, (index // 6) * height
            image = tk.PhotoImage(master=self)
            self.tk.call(image, "copy", self._masters[atlas], "-from", left, top, left + width, top + height,
                         "-subsample", self._factor, self._factor)
            self._images[key] = image
        self._images.move_to_end(key)
        return self._images[key]

    def _point(self, column: float, row: float, lift: float = 0.0) -> tuple[float, float]:
        x, y = project(column, row)
        return self._board_x + x * self._square_size, self._board_y + (y - lift) * self._square_size

    def _outline(self, square: int, color: str, inset: float, **options) -> None:
        c, r = screen_cell(square, self.orientation)
        lo, hi = inset, 1 - inset
        points = [self._point(c + x, r + y) for x, y in ((lo, lo), (hi, lo), (hi, hi), (lo, hi), (lo, lo))]
        self.create_line(*points, fill=color, joinstyle="round", **options)

    def _disk(self, x: float, y: float, piece: Piece, lift: float = 0.0) -> None:
        # Connect the lower face to the visible front edge of the projected top face.
        size = self._square_size
        depth = PLATE_DEPTH * size
        front = [(x + px * size, y + py * size - lift) for px, py in _PLATE_FRONT]
        top = [(px, py - depth) for px, py in front]
        self.create_polygon(*top, *reversed(front), fill="#a4a3a2" if piece.color is Color.WHITE else "#2a2d36",
                            outline="#4c4e55", tags=("marble-side",))
        name = f"{piece.color.value}{piece.kind.value.upper()}.svg"
        image = self._image(name)
        _, _, anchor_x, anchor_y = self._plate_size
        self.create_image(x - anchor_x / self._factor, y - lift - depth - anchor_y / self._factor,
                          image=image, anchor="nw", tags=("piece",))

    def redraw(self) -> None:
        if not self.marble:
            super().redraw()
            return
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        atlas_width, atlas_height, anchor_x, anchor_y = self._board_size
        margin = 23
        if min(width, height) <= 2 * margin:
            self._square_size = 0
            return
        self._factor = max(1, ceil(max(atlas_width / (width - 2 * margin),
                                       (atlas_height + BOARD_DEPTH * REFERENCE_PIXELS) / (height - 2 * margin))))
        self._square_size = REFERENCE_PIXELS / self._factor
        left = (width - atlas_width / self._factor) / 2
        top = (height - (atlas_height / self._factor + BOARD_DEPTH * self._square_size)) / 2
        self._board_x = left + anchor_x / self._factor
        self._board_y = top + anchor_y / self._factor

        lo, hi = -BORDER, 8 + BORDER
        for endpoints, color in ((((lo, lo), (lo, hi)), "#343743"), (((lo, hi), (hi, hi)), "#181a20")):
            start, end = endpoints
            self.create_polygon(self._point(*start), self._point(*end), self._point(*end, -BOARD_DEPTH),
                                self._point(*start, -BOARD_DEPTH), fill=color, tags=("marble-side",))
        self.create_image(left, top, image=self._image(self.orientation), anchor="nw", tags=("marble-board",))

        t = self._theme
        if self._last_move is not None:
            for square in (self._last_move.from_square, self._last_move.to_square):
                self._outline(square, t.last_move, 0.045, width=2, tags=("last-move",))
        if self.selected_square is not None:
            self._outline(self.selected_square, t.action_new_bg, 0.095, width=3)
        if self._state is not None:
            self._draw_marble_position()
        if self._has_focus and self._focused_square is not None:
            self._outline(self._focused_square, t.paper, 0.12, width=4, tags=("square-focus",))
            self._outline(self._focused_square, t.focus_ink, 0.12, width=2, dash=(4, 3), tags=("square-focus",))
        self._draw_marble_coordinates()
        while len(self._images) > 48:
            self._images.popitem(last=False)

    def _draw_marble_position(self) -> None:
        t = self._theme
        centers = [(self._point(c + 0.5, r + 0.5), square, piece)
                   for square, piece in enumerate(self._state.board) if piece is not None
                   for c, r in (screen_cell(square, self.orientation),)]
        for (x, y), square, piece in sorted(centers, key=lambda entry: entry[0][1]):
            if not self._drag_active or square != self._press_square:
                self._disk(x, y, piece)
        for target in {move.to_square for move in self._legal_moves if move.from_square == self.selected_square}:
            self._outline(target, t.paper, 0.18, width=4)
            self._outline(target, t.ink, 0.18, width=2, tags=("legal-target",))
        if self._hint_square is not None:
            self._outline(self._hint_square, t.paper, 0.09, width=4, tags=("hint",))
            self._outline(self._hint_square, t.focus_ink, 0.09, width=2, dash=(3, 3), tags=("hint",))
        if self._in_check:
            self._outline(self._state.king_square(self._state.turn), t.brand_red, 0.07, width=3)
        if self._drag_active and self._drag_pointer and self._press_square is not None:
            piece = self._state.board[self._press_square]
            if piece is not None:
                self._disk(*self._drag_pointer, piece, lift=self._square_size * 0.12)

    def _draw_marble_coordinates(self) -> None:
        font = ("TkFixedFont", -max(8, int(self._square_size * 0.21)), "bold")
        t = self._theme
        coord_color = t.paper if not t.is_dark else t.ink
        for i in range(8):
            rank = 8 - i if self.orientation == "white" else i + 1
            file = "abcdefgh"[i if self.orientation == "white" else 7 - i]
            self.create_text(*self._point(-0.16, i + 0.5), text=str(rank), fill=coord_color, font=font)
            self.create_text(*self._point(i + 0.5, 8.15), text=file, fill=coord_color, font=font)

    def _square_at(self, x: float, y: float) -> int | None:
        if not self.marble:
            return super()._square_at(x, y)
        if not self._square_size:
            return None
        a, b, c, d = PROJECTION
        x, y = (x - self._board_x) / self._square_size, (y - self._board_y) / self._square_size
        det = a * d - b * c
        column = floor((d * x - c * y) / det)
        row = floor((a * y - b * x) / det)
        return self._square_for_cell(column, row) if 0 <= column < 8 and 0 <= row < 8 else None
