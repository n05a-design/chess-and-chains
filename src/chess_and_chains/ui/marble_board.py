"""Native Tk projection of the local marble board and its engraved plates."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

from collections import OrderedDict
from importlib.resources import files
from math import atan2, ceil, cos, floor, pi, sin
import tkinter as tk

from typing import Literal

from ..chess import Color, Piece, PieceType
from .board import BoardCanvas, screen_cell
from .board_artwork import Marble2DArtwork
from .piece_contract import PIECE_FILE_NAMES
from .pieces import OwnerSvgPieces, PieceRenderer, get_piece_set
from .theme import ThemePalette

BoardDesignChoice = Literal["standard", "marble", "custom"]
BoardPerspective = Literal["2d", "3d"]
PieceView = Literal["front", "top"]

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
        self._custom_artwork = self._artwork
        self._marble_2d_artwork: Marble2DArtwork | None = None
        self._board_design: BoardDesignChoice = "custom" if self._custom_artwork is not None else "standard"
        self._perspective: BoardPerspective = "2d"
        self._piece_view: PieceView = "top" if getattr(self.renderer, "top_view", False) else "front"
        self._piece_renderers: dict[str, PieceRenderer] = {getattr(self.renderer, "piece_set", "original"): self.renderer}
        self._masters: dict[str, tk.PhotoImage] = {}
        self._images: OrderedDict[tuple[int, str], tk.PhotoImage] = OrderedDict()
        self._factor = 1
        self._board_size = board_frame()
        self._plate_size = plate_frame()

    @property
    def board_design(self) -> BoardDesignChoice:
        return self._board_design

    @property
    def perspective(self) -> BoardPerspective:
        return self._perspective

    @property
    def piece_view(self) -> PieceView:
        return "top" if self.piece_set == "top" else "front"

    @property
    def piece_set(self) -> str:
        return getattr(self.renderer, "piece_set", "original")

    def supports_3d(self, design: BoardDesignChoice | None = None) -> bool:
        target = self._board_design if design is None else design
        return target == "marble"

    def _ensure_marble_3d_assets(self) -> None:
        if not self._masters:
            assets = files(__package__).joinpath("marble_assets")
            # Assign only once both parts have loaded, so a read failure leaves the normal board usable.
            self._masters = {
                name: tk.PhotoImage(master=self, data=assets.joinpath(f"{name}.png").read_bytes(), format="png")
                for name in ("white", "black", "plates")
            }

    def _ensure_marble_2d_artwork(self) -> Marble2DArtwork:
        if self._marble_2d_artwork is None:
            self._marble_2d_artwork = Marble2DArtwork()
        return self._marble_2d_artwork

    def _sync_render_mode(self) -> None:
        self.marble = bool(self._board_design == "marble" and self._perspective == "3d")
        if self._board_design == "custom":
            self._artwork = self._custom_artwork
        elif self._board_design == "marble" and self._perspective == "2d":
            self._artwork = self._ensure_marble_2d_artwork()
        else:
            self._artwork = None
        self._press_square = None
        self._press_point = None
        self._drag_active = False
        self._drag_pointer = None
        self.configure(background=self._theme.window if self.marble else self._theme.acetate)
        self.redraw()

    def set_board_design(self, design: BoardDesignChoice) -> None:
        """Select board material independently without altering game or board state."""
        if design not in ("standard", "marble", "custom"):
            raise ValueError(f"Unknown board design: {design}")
        if design == "custom" and self._custom_artwork is None:
            raise ValueError("No custom SVG board design is loaded.")
        if design != "marble":
            self._perspective = "2d"
        elif self._perspective == "3d":
            self._ensure_marble_3d_assets()
        self._board_design = design
        self._sync_render_mode()

    def set_perspective(self, perspective: BoardPerspective) -> None:
        """Select 2D bird's-eye or 3D spatial view independently without altering game state."""
        if perspective not in ("2d", "3d"):
            raise ValueError(f"Unknown board perspective: {perspective}")
        if perspective == "3d":
            self._ensure_marble_3d_assets()
            self._board_design = "marble"
        self._perspective = perspective
        self._sync_render_mode()

    def set_piece_set(self, piece_set: str) -> None:
        """Switch active piece set across boards cleanly without altering game state."""
        info = get_piece_set(piece_set)
        renderer = self._piece_renderers.get(info.set_id)
        if renderer is None:
            if hasattr(self.renderer, "set_piece_set"):
                self.renderer.set_piece_set(info.set_id)
                renderer = self.renderer
            else:
                renderer = OwnerSvgPieces(piece_set=info.set_id)
            self._piece_renderers[info.set_id] = renderer
        else:
            self.renderer = renderer
        self._piece_view = "top" if info.perspective == "top" else "front"
        self.redraw()

    def set_piece_view(self, view: PieceView) -> None:
        """Switch piece depiction between front and top views without altering game state."""
        if view not in ("front", "top"):
            raise ValueError(f"Unknown piece view: {view}")
        target = "top" if view == "top" else "original"
        self.set_piece_set(target)

    def set_marble(self, enabled: bool) -> None:
        """Toggle 3D spatial marble mode cleanly while keeping backwards API compatibility."""
        if enabled:
            self._ensure_marble_3d_assets()
            self._board_design = "marble"
            self._perspective = "3d"
        else:
            self._perspective = "2d"
            self._board_design = "custom" if self._custom_artwork is not None else "standard"
        self._sync_render_mode()

    def set_theme(self, theme: ThemePalette) -> None:
        self._theme = theme
        self.configure(background=theme.window if self.marble else theme.acetate)
        self.redraw()

    def projected_square_center(self, square: int) -> tuple[float, float]:
        """Return the exact projected center ``(center_x, center_y)`` of ``square`` in 3D view."""
        c, r = screen_cell(square, self.orientation)
        return self._point(c + 0.5, r + 0.5)

    def _projected_circle_points(
        self,
        column: float,
        row: float,
        radius_cells: float,
        *,
        steps: int = 32,
    ) -> list[float]:
        points: list[float] = []
        cx_cell = column + 0.5
        cy_cell = row + 0.5
        for idx in range(steps):
            theta = (2.0 * pi * idx) / steps
            px, py = self._point(
                cx_cell + radius_cells * cos(theta),
                cy_cell + radius_cells * sin(theta),
            )
            points.extend((px, py))
        return points

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
        accent_border = [self._point(x, y) for x, y in ((-0.26, -0.26), (8.26, -0.26), (8.26, 8.26), (-0.26, 8.26), (-0.26, -0.26))]
        self.create_line(*accent_border, fill=t.brand_blue, width=2, joinstyle="round", tags=("marble-accent-frame",))
        if self._last_move is not None:
            for square in (self._last_move.from_square, self._last_move.to_square):
                self._outline(square, t.last_move, 0.045, width=2, tags=("last-move",))
        if self.selected_square is not None:
            self._outline(self.selected_square, t.action_new_bg, 0.095, width=3, tags=("selected-square",))
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
        legal_from_selected = (
            tuple(move for move in self._legal_moves if move.from_square == self.selected_square)
            if self.selected_square is not None
            else ()
        )
        centers = [(self._point(c + 0.5, r + 0.5), square, piece)
                   for square, piece in enumerate(self._state.board) if piece is not None
                   for c, r in (screen_cell(square, self.orientation),)]
        for (x, y), square, piece in sorted(centers, key=lambda entry: entry[0][1]):
            if not self._drag_active or square != self._press_square:
                self._disk(x, y, piece)
        for target in {move.to_square for move in legal_from_selected}:
            c, r = screen_cell(target, self.orientation)
            target_piece = self._state.board[target]
            is_en_passant = any(
                move.to_square == target
                and self._state.board[move.from_square] is not None
                and self._state.board[move.from_square].kind is PieceType.PAWN
                and self._state.en_passant == target
                for move in legal_from_selected
            )
            if target_piece is not None or is_en_passant:
                outer = self._projected_circle_points(c, r, 0.40)
                inner = self._projected_circle_points(c, r, 0.32)
                self.create_polygon(
                    *outer, fill="", outline=t.brand_red,
                    width=max(3, round(self._square_size * 0.04)),
                    tags=("legal-target", "legal-capture"),
                )
                self.create_polygon(
                    *inner, fill="", outline=t.paper,
                    width=max(1, round(self._square_size * 0.018)),
                    tags=("legal-target", "legal-capture"),
                )
            else:
                outer = self._projected_circle_points(c, r, 0.16)
                inner = self._projected_circle_points(c, r, 0.075)
                self.create_polygon(
                    *outer, fill=t.paper, outline=t.ink,
                    width=max(2, round(self._square_size * 0.025)),
                    tags=("legal-target", "legal-move"),
                )
                self.create_polygon(
                    *inner, fill=t.ink, outline="",
                    tags=("legal-target", "legal-move"),
                )
        if self._hint_square is not None:
            self._outline(self._hint_square, t.paper, 0.09, width=4, tags=("hint",))
            self._outline(self._hint_square, t.focus_ink, 0.09, width=2, dash=(3, 3), tags=("hint",))
        if self._in_check:
            self._outline(self._state.king_square(self._state.turn), t.brand_red, 0.07, width=3, tags=("check-square",))
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
