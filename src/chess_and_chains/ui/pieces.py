"""Bundled owner artwork, exchangeable renderers and the SVG asset contract."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import base64
import tkinter as tk
from bisect import bisect_right
from collections import OrderedDict
from dataclasses import dataclass
from importlib.resources import files
from typing import Protocol

from ..chess import Color, Piece
from .piece_contract import (
    MAX_SVG_BYTES as MAX_SVG_BYTES,
    PIECE_FILE_NAMES as PIECE_FILE_NAMES,
    SvgContractReport as SvgContractReport,
    validate_svg_piece_set as validate_svg_piece_set,
)
from .theme import INK, PAPER

PIECE_SVG_SIZE = 64
PIECE_FALLBACK_SIZES = (4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 48, 56, 64, 72, 80, 96, 112, 128, 160, 192, 256)
_PIECE_COLUMNS = len(PIECE_FILE_NAMES) // 2
_PIECE_CACHE_LIMIT = 48


@dataclass(frozen=True, slots=True)
class PieceSetInfo:
    """Descriptor and runtime contract for an available chess piece set."""

    set_id: str                   # "original", "top", "classic"
    asset_version: str            # "V.03", "V.04", "V.05"
    name_de: str                  # "Original", "Draufsicht", "Klassisch"
    name_en: str                  # "Original", "Top view", "Classic"
    subpath: str                  # subdirectory inside piece_assets
    provenance_path: str          # path to provenance documentation
    supports_svg: bool = True
    supports_png_fallback: bool = True
    perspective: str = "front"    # "front" or "top"

    def display_name(self, locale: str = "de") -> str:
        return self.name_de if (locale and locale.startswith("de")) else self.name_en


PIECE_SETS: dict[str, PieceSetInfo] = {
    "original": PieceSetInfo(
        set_id="original",
        asset_version="V.06",
        name_de="Original",
        name_en="Original",
        subpath="original",
        provenance_path="src/chess_and_chains/ui/piece_assets/original/PROVENANCE.md",
        perspective="front",
    ),
    "top": PieceSetInfo(
        set_id="top",
        asset_version="V.04.2",
        name_de="Draufsicht",
        name_en="Top view",
        subpath="top",
        provenance_path="src/chess_and_chains/ui/piece_assets/top/PROVENANCE.md",
        perspective="top",
    ),
    "classic": PieceSetInfo(
        set_id="classic",
        asset_version="V.05.1",
        name_de="Klassisch",
        name_en="Classic",
        subpath="classic",
        provenance_path="src/chess_and_chains/ui/piece_assets/classic/PROVENANCE.md",
        perspective="front",
    ),
}

DEFAULT_PIECE_SET = "original"


def get_piece_set(set_id: str | None) -> PieceSetInfo:
    """Return the registered piece set info or default fallback."""
    if set_id and set_id in PIECE_SETS:
        return PIECE_SETS[set_id]
    if set_id == "front":
        return PIECE_SETS["original"]
    return PIECE_SETS[DEFAULT_PIECE_SET]


def list_piece_sets() -> tuple[PieceSetInfo, ...]:
    """Return all registered piece sets in display order."""
    return tuple(PIECE_SETS.values())


def piece_atlas_box(name: str, band: int) -> tuple[int, int, int, int]:
    """Get the source rectangle for a piece in the two-row atlas band."""
    size = PIECE_FALLBACK_SIZES[band]
    row, column = divmod(PIECE_FILE_NAMES.index(name), _PIECE_COLUMNS)
    left = column * size
    top = 2 * sum(PIECE_FALLBACK_SIZES[:band]) + row * size
    return left, top, left + size, top + size


class PieceRenderer(Protocol):
    renderer_id: str

    def draw(self, canvas, center_x: float, center_y: float, square_size: float,
             piece: Piece, *, lifted: bool = False) -> None: ...


class OwnerSvgPieces:
    """Scale the supplied SVGs in Tk 9 or use their offline PNG atlas in Tk 8.6."""

    renderer_id = "owner-svg"

    def __init__(self, *, top_view: bool = False, piece_set: str | None = None) -> None:
        if piece_set is not None:
            chosen = piece_set
        elif top_view:
            chosen = "top"
        else:
            chosen = DEFAULT_PIECE_SET
        info = get_piece_set(chosen)
        self.piece_set: str = info.set_id
        self.asset_version: str = info.asset_version
        self.top_view: bool = (info.perspective == "top")
        self._assets = files(__package__).joinpath("piece_assets").joinpath(info.subpath)
        self._svg_sources = {name: self._assets.joinpath(name).read_bytes() for name in PIECE_FILE_NAMES}
        self._native_svg = True
        self._atlas: tk.PhotoImage | None = None
        self._images: OrderedDict[tuple[str, str, str, int], tk.PhotoImage] = OrderedDict()

    def set_piece_set(self, piece_set: str) -> None:
        """Switch active piece set and clear cached images cleanly."""
        info = get_piece_set(piece_set)
        if info.set_id == self.piece_set:
            return
        self.piece_set = info.set_id
        self.asset_version = info.asset_version
        self.top_view = (info.perspective == "top")
        self._assets = files(__package__).joinpath("piece_assets").joinpath(info.subpath)
        self._svg_sources = {name: self._assets.joinpath(name).read_bytes() for name in PIECE_FILE_NAMES}
        self.clear_cache()

    def clear_cache(self) -> None:
        """Invalidate all cached PhotoImages and offline atlas."""
        self._images.clear()
        self._atlas = None

    def draw(self, canvas, center_x: float, center_y: float, square_size: float,
             piece: Piece, *, lifted: bool = False) -> None:
        name = f"{piece.color.value}{piece.kind.value.upper()}.svg"
        size = max(1, round(square_size * (1.08 if lifted else 1)))
        image = self._load_image(canvas, name, size)
        canvas.create_image(center_x, center_y, image=image, tags=("piece",))

    def _load_image(self, canvas: tk.Canvas, name: str, size: int) -> tk.PhotoImage:
        key = (self.piece_set, self.asset_version, name, size)
        if self._native_svg:
            if key not in self._images:
                try:
                    image = tk.PhotoImage(master=canvas, data=self._svg_sources[name],
                                          format=("svg", "-scale", size / PIECE_SVG_SIZE))
                except tk.TclError:
                    self._native_svg = False
                else:
                    self._images[key] = image
            if self._native_svg:
                return self._use_cached(key)

        band = max(0, bisect_right(PIECE_FALLBACK_SIZES, size) - 1)
        tile_size = PIECE_FALLBACK_SIZES[band]
        fallback_key = (self.piece_set, self.asset_version, name, tile_size)
        if fallback_key not in self._images:
            self._images[fallback_key] = self._copy_png_piece(canvas, name, band)
        return self._use_cached(fallback_key)

    def _use_cached(self, key: tuple[str, str, str, int]) -> tk.PhotoImage:
        self._images.move_to_end(key)
        if len(self._images) > _PIECE_CACHE_LIMIT:
            self._images.popitem(last=False)
        return self._images[key]

    def _copy_png_piece(self, canvas: tk.Canvas, name: str, band: int) -> tk.PhotoImage:
        if self._atlas is None:
            data = base64.b64encode(self._assets.joinpath("fallback.png").read_bytes())
            self._atlas = tk.PhotoImage(master=canvas, data=data, format="png")
        size = PIECE_FALLBACK_SIZES[band]
        image = tk.PhotoImage(master=canvas, width=size, height=size)
        canvas.tk.call(image, "copy", self._atlas, "-from", *piece_atlas_box(name, band))
        return image


class GeometricTestPieces:
    """Temporary letter-in-disc pieces; explicitly not product artwork."""

    renderer_id = "geometric-test"

    def draw(self, canvas, center_x: float, center_y: float, square_size: float,
             piece: Piece, *, lifted: bool = False) -> None:
        radius = square_size * (0.31 if not lifted else 0.34)
        white_piece = piece.color is Color.WHITE
        canvas.create_oval(
            center_x - radius, center_y - radius, center_x + radius, center_y + radius,
            fill=PAPER if white_piece else INK,
            outline=INK if white_piece else PAPER,
            width=max(2, int(square_size * 0.035)),
            tags=("piece",),
        )
        canvas.create_text(
            center_x, center_y,
            text=piece.kind.value.upper(),
            fill=INK if white_piece else PAPER,
            font=("TkDefaultFont", -max(8, int(square_size * 0.55)), "bold"),
            tags=("piece",),
        )
