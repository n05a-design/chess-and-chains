"""An opt-in preview of local SVG board designs in Tk."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

from collections import OrderedDict
from importlib.resources import files
import math
import re
import tkinter as tk
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from .theme import hex_rgb, mix_rgb, rgb_hex

# ---------------------------------------------------------------------------
# SVG-support probe (Tk 9 / Tk 8.6+NanoSVG support SVG PhotoImage natively;
# vanilla Tk 8.6 on Linux does not).  Tested once per interpreter instance.
# ---------------------------------------------------------------------------
_SVG_SUPPORTED: bool | None = None  # None = not yet probed


def _probe_svg_support(master: tk.Misc) -> bool:
    """Return True if Tk's PhotoImage accepts format="svg" in this interpreter."""
    global _SVG_SUPPORTED
    if _SVG_SUPPORTED is not None:
        return _SVG_SUPPORTED
    _PROBE_SVG = (
        b'<?xml version="1.0"?>'
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">'
        b'<rect width="1" height="1" fill="#FF0000"/></svg>'
    )
    try:
        img = tk.PhotoImage(master=master, data=_PROBE_SVG, format="svg")
        img.blank()  # exercise it briefly
        _SVG_SUPPORTED = True
    except tk.TclError:
        _SVG_SUPPORTED = False
    return _SVG_SUPPORTED

MAX_BOARD_PREVIEW_SIZE = 2048
_MAX_SVG_BYTES = 2 * 1024 * 1024
_MAX_DESIGN_BYTES = 4 * 1024 * 1024
_SVG_NAMESPACE = "{http://www.w3.org/2000/svg}"
_BOARD_SQUARES = tuple(f"{file}{rank}" for rank in range(8, 0, -1) for file in "abcdefgh")
_SVG_ELEMENTS = {
    "svg", "g", "path", "rect", "circle", "ellipse", "polygon", "polyline", "line", "defs",
    "title", "desc", "linearGradient", "radialGradient", "stop",
}
_LOCAL_ID = re.compile(r"#[A-Za-z_][\w.:-]*", re.ASCII)
_CSS_URL = re.compile(r"url\s*\(\s*(['\"]?)([^)'\"]+)\1\s*\)", re.IGNORECASE)
_CSS_URL_START = re.compile(r"url\s*\(", re.IGNORECASE)


class BoardArtworkError(ValueError):
    """A supplied board design could not be loaded or rendered."""


@dataclass(frozen=True, slots=True)
class BoardDesign:
    """SVG bytes for the complete board or tiles in white's screen order."""

    full: bytes | None = None
    tiles: tuple[bytes, ...] = ()


def load_board_design(path: Path) -> BoardDesign:
    """Load a complete SVG, a light/dark pair with overrides, or all 64 tiles."""
    full = path / "board.svg" if path.is_dir() else path
    if full.is_file():
        return BoardDesign(full=_read_svg(full))
    if not path.is_dir():
        raise BoardArtworkError(f"Board design not found: {path}")

    overrides = {name: path / f"{name}.svg" for name in _BOARD_SQUARES if (path / f"{name}.svg").is_file()}
    sources = (path / "light.svg", path / "dark.svg")
    if len(overrides) != 64 and not all(source.is_file() for source in sources):
        raise BoardArtworkError(f"Supply board.svg, light.svg and dark.svg, or all 64 square SVGs in {path}")

    paths = [overrides.get(name, sources[(index // 8 + index % 8) % 2]) for index, name in enumerate(_BOARD_SQUARES)]
    loaded = {}
    total = 0
    for source in dict.fromkeys(paths):
        content = _read_svg(source)
        total += len(content)
        if total > _MAX_DESIGN_BYTES:
            raise BoardArtworkError(f"Board SVGs exceed {_MAX_DESIGN_BYTES // 1024} KiB in total: {path}")
        loaded[source] = content
    return BoardDesign(tiles=tuple(loaded[source] for source in paths))


def _read_svg(path: Path) -> bytes:
    if path.suffix.lower() != ".svg":
        raise BoardArtworkError(f"Expected an SVG file: {path}")
    try:
        with path.open("rb") as file:
            data = file.read(_MAX_SVG_BYTES + 1)
        if len(data) > _MAX_SVG_BYTES:
            raise ValueError(f"SVG exceeds {_MAX_SVG_BYTES // 1024} KiB")
        text = data.decode("utf-8-sig")
        if any(marker in text.casefold() for marker in ("<!doctype", "<!entity", "<?xml-stylesheet")):
            raise ValueError("SVG references to external definitions or stylesheets are unsupported")
        root = ET.fromstring(text)
        if root.tag != _SVG_NAMESPACE + "svg":
            raise ValueError("expected an SVG document")
        _square_viewbox(root)
        for parent in root.iter():
            for child in list(parent):
                if child.tag == _SVG_NAMESPACE + "metadata":
                    parent.remove(child)
        for element in root.iter():
            if not element.tag.startswith(_SVG_NAMESPACE) or element.tag.removeprefix(_SVG_NAMESPACE) not in _SVG_ELEMENTS:
                raise ValueError(f"unsupported SVG element: {element.tag.split('}')[-1]}")
            for name, value in element.attrib.items():
                local_name = name.split("}")[-1].lower()
                if local_name.startswith("on") or local_name in {"base", "href", "src"}:
                    raise ValueError(f"unsupported SVG attribute: {local_name}")
                if "@import" in value.casefold() or _CSS_URL_START.search(_CSS_URL.sub("", value)):
                    raise ValueError("unsupported SVG style reference")
                if any(not _LOCAL_ID.fullmatch(match[2].strip()) for match in _CSS_URL.finditer(value)):
                    raise ValueError("SVG references must be within the same document")
        return _svg_bytes(root)
    except (OSError, ValueError, ET.ParseError) as error:
        raise BoardArtworkError(f"{path}: {error}") from error


def _square_viewbox(root: ET.Element) -> tuple[float, float, float]:
    try:
        x, y, width, height = map(float, re.split(r"[\s,]+", root.get("viewBox", "").strip()))
    except ValueError as error:
        raise ValueError("expected a square viewBox with four finite numbers") from error
    if not all(math.isfinite(value) for value in (x, y, width, height)) or width <= 0 or width != height:
        raise ValueError("expected a square viewBox with four finite numbers")
    return x, y, width


def _svg_bytes(root: ET.Element) -> bytes:
    # NanoSVG expects unprefixed drawing elements.
    ET.register_namespace("", _SVG_NAMESPACE[1:-1])
    return ET.tostring(root, encoding="utf-8")


class BoardArtwork:
    """Cache both board backgrounds at the current size, independent of game state."""

    def __init__(self, design: BoardDesign) -> None:
        self._design = design
        self._images: dict[bool, tk.PhotoImage] = {}
        self._key: tuple[object, int] | None = None

    def image(self, master: tk.Misc, tile_size: int, *, flipped: bool) -> tk.PhotoImage:
        key = master.tk, tile_size
        if self._key != key:
            self._images.clear()
            self._key = key
        cached = self._images.get(flipped)
        if cached is not None:
            return cached
        size = tile_size * 8
        if self._design.full is not None:
            image = self._photo(master, self._design.full, size, flipped=flipped)
        else:
            image = tk.PhotoImage(master=master, width=size, height=size)
            other = self._images.get(not flipped)
            if other is None:
                self._render_tiles(master, image, tile_size, flipped=flipped)
            else:
                self._copy_reversed_tiles(master, image, other, tile_size)
        self._images[flipped] = image
        return image

    def _render_tiles(self, master: tk.Misc, image: tk.PhotoImage, tile_size: int, *, flipped: bool) -> None:
        tiles = reversed(self._design.tiles) if flipped else self._design.tiles
        decoded: dict[bytes, tk.PhotoImage] = {}
        for position, source in enumerate(tiles):
            if source not in decoded:
                decoded[source] = self._photo(master, source, tile_size)
            row, column = divmod(position, 8)
            master.tk.call(image, "copy", decoded[source], "-to", column * tile_size, row * tile_size)

    @staticmethod
    def _copy_reversed_tiles(master: tk.Misc, target: tk.PhotoImage, source: tk.PhotoImage, tile_size: int) -> None:
        for position in range(64):
            row, column = divmod(position, 8)
            source_x = (7 - column) * tile_size
            source_y = (7 - row) * tile_size
            master.tk.call(
                target, "copy", source, "-from", source_x, source_y, source_x + tile_size, source_y + tile_size,
                "-to", column * tile_size, row * tile_size, "-compositingrule", "set",
            )

    @staticmethod
    def _photo(master: tk.Misc, content: bytes, size: int, *, flipped: bool = False) -> tk.PhotoImage:
        root = ET.fromstring(content)
        root.set("height", str(size))
        root.set("width", str(size))
        if flipped:
            x, y, length = _square_viewbox(root)
            group = ET.Element(_SVG_NAMESPACE + "g", {"transform": f"rotate(180 {x + length / 2} {y + length / 2})"})
            group.extend(root)
            root[:] = [group]
        svg_data = _svg_bytes(root)
        if _probe_svg_support(master):
            return tk.PhotoImage(master=master, data=svg_data, format="svg")
        # Raster fallback: extract first rect fill color; paint solid tile
        return _svg_to_solid_photo(master, root, size)


_HEX_COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}\b")


def _svg_dominant_color(root: ET.Element) -> str:
    """Extract the first fill color from the SVG element tree (raster fallback helper)."""
    for element in root.iter():
        fill = element.get("fill", "")
        if _HEX_COLOR_RE.match(fill):
            return fill
        style = element.get("style", "")
        m = re.search(r"fill\s*:\s*(#[0-9a-fA-F]{6})", style)
        if m:
            return m.group(1)
    return "#808080"


def _svg_to_solid_photo(master: tk.Misc, root: ET.Element, size: int) -> tk.PhotoImage:
    """Raster fallback: paint a solid-color PhotoImage from the first fill color."""
    color = _svg_dominant_color(root)
    image = tk.PhotoImage(master=master, width=size, height=size)
    # Build a single-row PPM-like block and fill the image
    image.put(color, to=(0, 0, size, size))
    return image


def _checkerboard_photo(
    master: tk.Misc,
    board_size: int,
    tile_size: int,
    light_color: str,
    dark_color: str,
    *,
    flipped: bool = False,
) -> tk.PhotoImage:
    """Generate a tinted checkerboard as raster fallback for marble/SVG boards."""
    image = tk.PhotoImage(master=master, width=board_size, height=board_size)
    for row in range(8):
        for col in range(8):
            screen_row = 7 - row if flipped else row
            screen_col = 7 - col if flipped else col
            is_light = (screen_row + screen_col) % 2 == 0
            color = light_color if is_light else dark_color
            x0 = col * tile_size
            y0 = row * tile_size
            image.put(color, to=(x0, y0, x0 + tile_size, y0 + tile_size))
    return image


def _tint_marble_svg_text(svg_text: str, tint_color: str | None) -> str:
    """Apply a subtle, veining-preserving Themenfarbe tint to the 2D marble SVG."""
    if not tint_color:
        return svg_text
    target = hex_rgb(tint_color)
    # Neutral gray (low chroma) preserves natural cool marble stones.
    if max(target) - min(target) <= 24:
        return svg_text

    def _replace(match: re.Match[str]) -> str:
        rgb = hex_rgb(match.group(0))
        lum = (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255.0
        share = 0.14 if lum > 0.55 else 0.22
        return rgb_hex(mix_rgb(rgb, target, share))

    return _HEX_COLOR_RE.sub(_replace, svg_text)


class Marble2DArtwork:
    """Orthogonal 2D bird's-eye renderer for the existing marble board artwork."""

    def __init__(self, *, source_svg: Path | None = None) -> None:
        self._source_svg = source_svg
        self._base_svg: str | None = None
        self._images: OrderedDict[tuple[object, int, bool, str | None], tk.PhotoImage] = OrderedDict()

    def _load_cropped_svg(self) -> str:
        if self._base_svg is not None:
            return self._base_svg
        raw_bytes: bytes | None = None
        if self._source_svg is not None and self._source_svg.is_file():
            raw_bytes = self._source_svg.read_bytes()
        else:
            repo_master = Path(__file__).resolve().parents[3] / "design" / "source" / "marmor-3d" / "spielsatz" / "Brett.svg"
            if repo_master.is_file():
                raw_bytes = repo_master.read_bytes()
            else:
                bundled = files(__package__).joinpath("marble_assets").joinpath("board_2d.svg")
                raw_bytes = bundled.read_bytes()
        tree = ET.fromstring(raw_bytes.decode("utf-8"))
        for child in list(tree):
            cid = child.attrib.get("id", "")
            tag = child.tag.split("}")[-1]
            if cid in ("koordinaten", "rahmen") or (tag == "rect" and child.attrib.get("width") in ("864", "806")):
                tree.remove(child)
        tree.set("viewBox", "32 32 800 800")
        tree.set("width", "800")
        tree.set("height", "800")
        self._base_svg = _svg_bytes(tree).decode("utf-8")
        return self._base_svg

    def image(
        self,
        master: tk.Misc,
        tile_size: int,
        *,
        flipped: bool = False,
        tint_color: str | None = None,
    ) -> tk.PhotoImage:
        key = (master.tk, int(tile_size), bool(flipped), tint_color)
        cached = self._images.get(key)
        if cached is not None:
            self._images.move_to_end(key)
            return cached
        size = max(8, int(tile_size) * 8)

        try:
            if not _probe_svg_support(master):
                # Raster fallback: themed checkerboard preserving tinting via color math
                img = self._checkerboard_fallback(master, size, tile_size, tint_color=tint_color, flipped=flipped)
            else:
                img = self._render_svg(master, size, tint_color=tint_color, flipped=flipped)
        except Exception:
            # On a rendering error, preserve the previous valid board state if available
            for prev_key, prev_img in reversed(self._images.items()):
                if prev_key[0] == master.tk:
                    return prev_img
            raise

        self._images[key] = img
        while len(self._images) > 24:
            self._images.popitem(last=False)
        return img

    def _render_svg(
        self,
        master: tk.Misc,
        size: int,
        *,
        tint_color: str | None,
        flipped: bool,
    ) -> tk.PhotoImage:
        svg_text = _tint_marble_svg_text(self._load_cropped_svg(), tint_color)
        root = ET.fromstring(svg_text.encode("utf-8"))
        root.set("width", str(size))
        root.set("height", str(size))
        if flipped:
            # 800x800 grid covers x in [32, 832], y in [32, 832] -> center is (432, 432).
            group = ET.Element(_SVG_NAMESPACE + "g", {"transform": "rotate(180 432 432)"})
            for child in list(root):
                if child.tag != _SVG_NAMESPACE + "defs":
                    group.append(child)
                    root.remove(child)
            root.append(group)
        return tk.PhotoImage(master=master, data=_svg_bytes(root), format="svg")

    def _checkerboard_fallback(
        self,
        master: tk.Misc,
        board_size: int,
        tile_size: int,
        *,
        tint_color: str | None,
        flipped: bool,
    ) -> tk.PhotoImage:
        """Tinted checkerboard for environments without SVG PhotoImage support."""
        # Marble-inspired neutral colors
        base_light = "#D4CAB8"
        base_dark = "#8C7B6A"
        if tint_color and (max(hex_rgb(tint_color)) - min(hex_rgb(tint_color)) > 24):
            tint = hex_rgb(tint_color)
            light = rgb_hex(mix_rgb(hex_rgb(base_light), tint, 0.14))
            dark = rgb_hex(mix_rgb(hex_rgb(base_dark), tint, 0.22))
        else:
            light, dark = base_light, base_dark
        return _checkerboard_photo(master, board_size, tile_size, light, dark, flipped=flipped)
