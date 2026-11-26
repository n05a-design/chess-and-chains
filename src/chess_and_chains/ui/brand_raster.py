"""Standard-library SVG rasteriser for the Chess & Chains logo masters.

The three owner masters in ``design/01_Logo/svg`` (Affinity exports) use
nested ``matrix()`` transforms, cubic paths, ``rect`` elements, inherited
``fill-rule`` and thin round-joined strokes. This module reads exactly that
subset and rejects everything else, so a new master with unknown features
fails loudly instead of rendering wrongly.

It is shared by the runtime (theme-tinted in-app signet, Logo 01) and by
``scripts/build_brand_assets.py`` (all PNG/ICO/ICNS exports). It imports no
Tk and no third-party packages, so the output is identical on every platform
of the CI matrix (pixel comparison; zlib bytes may differ between builds).

Security: only local bytes are parsed. Documents with ``<!ENTITY``
declarations, external references (``href``), ``<image>``, ``<use>``,
``<style>`` or ``<script>`` are rejected before rendering.

The path parser is adapted from STEPS ``scripts/build_brand_assets.py``
(same owner, n05a-design/steps) and extended by transforms, rects,
even-odd filling, strokes and erase compositing.
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

from dataclasses import dataclass
from itertools import groupby
import math
import re
import struct
import xml.etree.ElementTree as ET
import zlib

Point = tuple[float, float]
Matrix = tuple[float, float, float, float, float, float]
RGB = tuple[int, int, int]

IDENTITY: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
SUBSAMPLES = 8

_TOKEN = re.compile(r"[A-Za-z]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_ARITY = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "Z": 0}
_MATRIX = re.compile(r"^\s*matrix\(([^)]*)\)\s*$")
_RGB = re.compile(r"^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$")
_HEX6 = re.compile(r"^#([0-9A-Fa-f]{6})$")
_NAMED = {"white": (255, 255, 255), "black": (0, 0, 0)}
_ALLOWED_TAGS = {"svg", "g", "rect", "path"}
_FORBIDDEN_BYTES = (b"<!ENTITY", b"<script", b"href=", b"<image", b"<use", b"<style", b"<foreignObject")


class UnsupportedSvg(ValueError):
    """The SVG uses a feature outside the supported master subset."""


@dataclass(frozen=True)
class Shape:
    """One painted SVG element in user space (viewBox units)."""

    index: int
    tag: str
    fill: RGB | None
    fill_rule: str
    stroke: RGB | None
    stroke_width: float  # already scaled into user space
    subpaths: tuple[tuple[Point, ...], ...]


@dataclass(frozen=True)
class Document:
    view_box: tuple[float, float, float, float]
    shapes: tuple[Shape, ...]


# --------------------------------------------------------------------------- parsing
def _multiply(a: Matrix, b: Matrix) -> Matrix:
    """Return ``a · b`` (apply ``b`` first, then ``a``)."""
    a0, a1, a2, a3, a4, a5 = a
    b0, b1, b2, b3, b4, b5 = b
    return (
        a0 * b0 + a2 * b1,
        a1 * b0 + a3 * b1,
        a0 * b2 + a2 * b3,
        a1 * b2 + a3 * b3,
        a0 * b4 + a2 * b5 + a4,
        a1 * b4 + a3 * b5 + a5,
    )


def _apply(m: Matrix, x: float, y: float) -> Point:
    return (m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5])


def _parse_transform(text: str | None) -> Matrix:
    if not text:
        return IDENTITY
    match = _MATRIX.match(text)
    if match is None:
        raise UnsupportedSvg(f"Unsupported transform {text!r} (only matrix()).")
    values = [float(v) for v in re.split(r"[\s,]+", match.group(1).strip()) if v]
    if len(values) != 6:
        raise UnsupportedSvg(f"matrix() needs six values: {text!r}")
    return tuple(values)  # type: ignore[return-value]


def _parse_style(text: str | None) -> dict[str, str]:
    style: dict[str, str] = {}
    for part in (text or "").split(";"):
        if ":" in part:
            key, value = part.split(":", 1)
            style[key.strip()] = value.strip()
    return style


def _parse_color(value: str | None) -> RGB | None:
    if value is None or value == "none":
        return None
    if value in _NAMED:
        return _NAMED[value]
    match = _RGB.match(value)
    if match:
        return tuple(int(v) for v in match.groups())  # type: ignore[return-value]
    match = _HEX6.match(value)
    if match:
        h = match.group(1)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    raise UnsupportedSvg(f"Unsupported colour {value!r}.")


def _curve(points: list[Point], p0: Point, p1: Point, p2: Point, p3: Point) -> None:
    """Append a cubic Bezier (in user space) as line points."""
    length = sum(math.dist(a, b) for a, b in ((p0, p1), (p1, p2), (p2, p3)))
    steps = min(256, max(8, int(length / 1.5) + 1))
    for index in range(1, steps + 1):
        t = index / steps
        u = 1 - t
        a, b, c, d = u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t
        points.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                       a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))


def parse_path(data: str, matrix: Matrix = IDENTITY) -> list[tuple[Point, ...]]:
    """Return the subpaths of an SVG path as user-space point lists."""
    tokens = _TOKEN.findall(data)
    subpaths: list[tuple[Point, ...]] = []
    points: list[Point] = []
    x = y = start_x = start_y = 0.0
    control = None
    position, command = 0, None

    def T(px: float, py: float) -> Point:
        return _apply(matrix, px, py)

    while position < len(tokens):
        if tokens[position].isalpha():
            command = tokens[position]
            position += 1
        elif command is None:
            raise UnsupportedSvg("Path data starts without a command.")
        kind = command.upper()
        if kind not in _ARITY:
            raise UnsupportedSvg(f"Unsupported path command {command!r}.")
        try:
            values = [float(token) for token in tokens[position:position + _ARITY[kind]]]
        except ValueError as exc:
            raise UnsupportedSvg(f"Incomplete arguments for path command {command!r}.") from exc
        if len(values) != _ARITY[kind]:
            raise UnsupportedSvg(f"Incomplete arguments for path command {command!r}.")
        position += _ARITY[kind]
        relative = command.islower()
        if relative and kind == "H":
            values[0] += x
        elif relative and kind == "V":
            values[0] += y
        elif relative:
            values = [value + (x if index % 2 == 0 else y) for index, value in enumerate(values)]
        reflected = None
        if kind == "M":
            if len(points) > 1:
                subpaths.append(tuple(points))
            x, y = start_x, start_y = values
            points = [T(x, y)]
            command = "l" if relative else "L"
        elif kind == "Z":
            if len(points) > 1:
                subpaths.append(tuple(points))
            x, y = start_x, start_y
            points = [T(x, y)]
            command = None
        elif kind == "L":
            x, y = values
            points.append(T(x, y))
        elif kind == "H":
            x = values[0]
            points.append(T(x, y))
        elif kind == "V":
            y = values[0]
            points.append(T(x, y))
        elif kind in "CS":
            if kind == "S":
                first = (2 * x - control[1], 2 * y - control[2]) if control and control[0] == "C" else (x, y)
                values = [*first, *values]
            _curve(points, T(x, y), T(*values[0:2]), T(*values[2:4]), T(*values[4:6]))
            reflected = ("C", values[2], values[3])
            x, y = values[4:6]
        else:
            if kind == "T":
                first = (2 * x - control[1], 2 * y - control[2]) if control and control[0] == "Q" else (x, y)
                values = [*first, *values]
            qx, qy, end_x, end_y = values
            _curve(points, T(x, y),
                   T(x + 2 / 3 * (qx - x), y + 2 / 3 * (qy - y)),
                   T(end_x + 2 / 3 * (qx - end_x), end_y + 2 / 3 * (qy - end_y)),
                   T(end_x, end_y))
            reflected = ("Q", qx, qy)
            x, y = end_x, end_y
        control = reflected
    if len(points) > 1:
        subpaths.append(tuple(points))
    return subpaths


def _check_bytes(content: bytes) -> None:
    lowered = content.lower()
    for marker in _FORBIDDEN_BYTES:
        if marker.lower() in lowered:
            raise UnsupportedSvg(f"Forbidden SVG construct {marker.decode()!r}.")


def parse_svg(content: bytes) -> Document:
    """Parse a logo master into painting-order shapes (user space)."""
    _check_bytes(content)
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise UnsupportedSvg(f"Invalid SVG/XML: {exc}") from exc
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise UnsupportedSvg("Root element is not <svg>.")
    vb = [float(v) for v in re.split(r"[\s,]+", root.attrib.get("viewBox", "").strip()) if v]
    if len(vb) != 4 or vb[2] <= 0 or vb[3] <= 0:
        raise UnsupportedSvg("Missing or invalid viewBox.")
    shapes: list[Shape] = []

    def walk(element: ET.Element, matrix: Matrix, fill_rule: str) -> None:
        tag = element.tag.rsplit("}", 1)[-1]
        if tag not in _ALLOWED_TAGS:
            raise UnsupportedSvg(f"Element <{tag}> is outside the supported subset.")
        style = _parse_style(element.attrib.get("style"))
        if any(key in element.attrib for key in ("fill", "stroke", "clip-path", "mask", "filter", "opacity")):
            raise UnsupportedSvg(f"<{tag}> uses presentation attributes; only inline style is supported.")
        for key in style:
            if key in ("opacity", "fill-opacity", "stroke-opacity", "filter", "mask", "clip-path") and style[key] not in ("1", "none"):
                raise UnsupportedSvg(f"Style {key} is outside the supported subset.")
        rule = style.get("fill-rule", fill_rule)
        if rule not in ("evenodd", "nonzero"):
            raise UnsupportedSvg(f"Unsupported fill-rule {rule!r}.")
        local = _multiply(matrix, _parse_transform(element.attrib.get("transform")))
        if tag in ("svg", "g"):
            for child in element:
                walk(child, local, rule)
            return
        fill = _parse_color(style.get("fill", "black"))
        stroke = _parse_color(style.get("stroke"))
        if tag == "rect":
            if any(k in element.attrib for k in ("rx", "ry")):
                raise UnsupportedSvg("Rounded <rect> is outside the supported subset.")
            rx, ry = float(element.attrib.get("x", 0)), float(element.attrib.get("y", 0))
            rw, rh = float(element.attrib["width"]), float(element.attrib["height"])
            subpaths = [tuple(_apply(local, px, py) for px, py in (
                (rx, ry), (rx + rw, ry), (rx + rw, ry + rh), (rx, ry + rh)))]
        else:
            subpaths = parse_path(element.attrib["d"], local)
        if fill is None and stroke is None:
            return
        width = 0.0
        if stroke is not None:
            raw = style.get("stroke-width", "1").removesuffix("px")
            width = float(raw) * math.sqrt(abs(local[0] * local[3] - local[1] * local[2]))
            if style.get("stroke-linejoin", "round") != "round" and "stroke-linejoin" in style:
                raise UnsupportedSvg("Only round stroke joins are supported.")
        shapes.append(Shape(len(shapes), tag, fill, rule, stroke, width, tuple(subpaths)))

    root_style = _parse_style(root.attrib.get("style"))
    walk(root, IDENTITY, root_style.get("fill-rule", "nonzero"))
    if not shapes:
        raise UnsupportedSvg("SVG contains no painted shapes.")
    return Document((vb[0], vb[1], vb[2], vb[3]), tuple(shapes))


# ------------------------------------------------------------------- geometry
def bounds(subpath_groups: list[tuple[tuple[Point, ...], ...]], pad: float = 0.0) -> tuple[float, float, float, float]:
    """Return ``(x, y, width, height)`` of all points (user space)."""
    xs = [p[0] for group in subpath_groups for path in group for p in path]
    ys = [p[1] for group in subpath_groups for path in group for p in path]
    if not xs:
        raise UnsupportedSvg("No geometry for bounds.")
    x0, y0, x1, y1 = min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad
    return (x0, y0, x1 - x0, y1 - y0)


def stroke_polygons(subpaths: tuple[tuple[Point, ...], ...], width: float) -> tuple[tuple[Point, ...], ...]:
    """Outline a closed polyline stroke as consistently wound quads and round joins."""
    half = width / 2
    polys: list[tuple[Point, ...]] = []
    for path in subpaths:
        pts = list(path)
        if pts[0] != pts[-1]:
            pts.append(pts[0])
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            length = math.hypot(x1 - x0, y1 - y0)
            if length <= 1e-9:
                continue
            nx, ny = -(y1 - y0) / length * half, (x1 - x0) / length * half
            polys.append(((x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)))
        for x0, y0 in pts[:-1]:
            polys.append(tuple((x0 + half * math.cos(a * math.pi / 6), y0 - half * math.sin(a * math.pi / 6))
                               for a in range(12)))
    return tuple(polys)


# ------------------------------------------------------------------ raster
@dataclass(frozen=True)
class Frame:
    """Map user space to a ``width`` x ``height`` pixel grid: px = (x - x0) * scale."""

    x0: float
    y0: float
    scale: float
    width: int
    height: int

    @classmethod
    def fit(cls, box: tuple[float, float, float, float], width: int, height: int) -> Frame:
        """Fit ``box`` centred into the pixel grid, keeping the aspect ratio."""
        bx, by, bw, bh = box
        scale = min(width / bw, height / bh)
        return cls(bx - (width / scale - bw) / 2, by - (height / scale - bh) / 2, scale, width, height)


def coverage(subpaths: tuple[tuple[Point, ...], ...], frame: Frame, rule: str = "nonzero") -> dict[int, list[float]]:
    """Return ``{row: coverage}`` of a filled shape (``nonzero`` or ``evenodd``)."""
    width, height = frame.width, frame.height
    crossings: dict[int, list[tuple[float, int]]] = {}
    limit = height * SUBSAMPLES - 1
    for path in subpaths:
        pixels = [((px - frame.x0) * frame.scale, (py - frame.y0) * frame.scale) for px, py in path]
        for (x0, y0), (x1, y1) in zip(pixels, pixels[1:] + pixels[:1]):
            if y0 == y1:
                continue
            direction = 1 if y1 > y0 else -1
            if direction < 0:
                x0, y0, x1, y1 = x1, y1, x0, y0
            slope = (x1 - x0) / (y1 - y0)
            first = max(0, math.ceil(y0 * SUBSAMPLES - 0.5))
            last = min(limit, math.ceil(y1 * SUBSAMPLES - 0.5) - 1)
            for sample in range(first, last + 1):
                sample_y = (sample + 0.5) / SUBSAMPLES
                crossings.setdefault(sample, []).append((x0 + (sample_y - y0) * slope, direction))
    weight = 1 / SUBSAMPLES
    partial: dict[int, list[float]] = {}
    steps: dict[int, list[float]] = {}
    evenodd = rule == "evenodd"
    for sample, hits in crossings.items():
        row = sample // SUBSAMPLES
        area = partial.setdefault(row, [0.0] * width)
        step = steps.setdefault(row, [0.0] * (width + 1))
        hits.sort()
        winding, span_start = 0, 0.0
        for hit_x, direction in hits:
            was_inside = (winding % 2 != 0) if evenodd else winding != 0
            winding += direction
            inside = (winding % 2 != 0) if evenodd else winding != 0
            if inside and not was_inside:
                span_start = hit_x
                continue
            if was_inside and not inside:
                left, right = max(span_start, 0.0), min(hit_x, float(width))
                if right <= left:
                    continue
                first_pixel, last_pixel = int(left), int(right)
                if first_pixel == last_pixel:
                    area[first_pixel] += (right - left) * weight
                    continue
                area[first_pixel] += (first_pixel + 1 - left) * weight
                if last_pixel < width:
                    area[last_pixel] += (right - last_pixel) * weight
                step[first_pixel + 1] += weight
                step[last_pixel] -= weight
    rows: dict[int, list[float]] = {}
    for row, area in partial.items():
        running, values = 0.0, []
        srow = steps[row]
        for column in range(width):
            running += srow[column]
            values.append(min(1.0, area[column] + running))
        rows[row] = values
    return rows


def _merge(first: dict[int, list[float]], second: dict[int, list[float]]) -> dict[int, list[float]]:
    for row, values in second.items():
        known = first.get(row)
        first[row] = values if known is None else [min(1.0, a + b) for a, b in zip(known, values)]
    return first


@dataclass(frozen=True)
class Layer:
    """A coverage layer painted with ``color`` (``over``) or removing alpha (``erase``)."""

    subpaths: tuple[tuple[Point, ...], ...]
    rule: str
    color: RGB | None
    mode: str = "over"


def layers_from_document(document: Document) -> list[Layer]:
    """Faithful painting order: each fill, then its stroke."""
    out: list[Layer] = []
    for shape in document.shapes:
        if shape.fill is not None:
            out.append(Layer(shape.subpaths, shape.fill_rule, shape.fill))
        if shape.stroke is not None and shape.stroke_width > 0:
            out.append(Layer(stroke_polygons(shape.subpaths, shape.stroke_width), "nonzero", shape.stroke))
    return out


def render(layers: list[Layer], frame: Frame) -> list[bytes]:
    """Composite layers into straight-alpha RGBA rows."""
    w, h = frame.width, frame.height
    size = w * h
    red, green, blue, alpha = [0.0] * size, [0.0] * size, [0.0] * size, [0.0] * size
    # Consecutive layers of one colour and mode are merged so that shared
    # antialiased seams (adjacent board squares) do not let the background through.
    for (color, mode), run in groupby(layers, key=lambda layer: (layer.color, layer.mode)):
        merged: dict[int, list[float]] = {}
        for layer in run:
            _merge(merged, coverage(layer.subpaths, frame, layer.rule))
        if mode == "erase":
            for row, values in merged.items():
                base = row * w
                for column, cov in enumerate(values):
                    if cov > 0.0:
                        i = base + column
                        keep = 1.0 - cov
                        red[i] *= keep
                        green[i] *= keep
                        blue[i] *= keep
                        alpha[i] *= keep
            continue
        assert color is not None
        sr, sg, sb = color[0] / 255, color[1] / 255, color[2] / 255
        for row, values in merged.items():
            base = row * w
            for column, cov in enumerate(values):
                if cov > 0.0:
                    i = base + column
                    keep = 1.0 - cov
                    red[i] = sr * cov + red[i] * keep
                    green[i] = sg * cov + green[i] * keep
                    blue[i] = sb * cov + blue[i] * keep
                    alpha[i] = cov + alpha[i] * keep
    rows: list[bytes] = []
    for y in range(h):
        row = bytearray()
        for i in range(y * w, (y + 1) * w):
            a = alpha[i]
            if a <= 0.0:
                row += b"\0\0\0\0"
                continue
            row += bytes((min(255, int(red[i] / a * 255 + 0.5)),
                          min(255, int(green[i] / a * 255 + 0.5)),
                          min(255, int(blue[i] / a * 255 + 0.5)),
                          min(255, int(a * 255 + 0.5))))
        rows.append(bytes(row))
    return rows


# --------------------------------------------------------- Logo 01 dynamic roles
LINK_COLORS: tuple[RGB, ...] = ((244, 196, 0), (36, 71, 216))
SEPARATOR_COLOR: RGB = (255, 255, 255)


def signet_roles(document: Document) -> tuple[list[Shape], list[Shape]]:
    """Split Logo 01 into ``(links, separators)``; reject unexpected structure.

    Links are the blue and yellow filled chain links. Separators are the white
    bands with thin black strokes that carve the interlocking overpass.
    """
    links = [s for s in document.shapes if s.fill in LINK_COLORS and s.stroke is None]
    separators = [s for s in document.shapes if s.fill == SEPARATOR_COLOR]
    if len(links) != 2 or len(separators) != 2 or len(links) + len(separators) != len(document.shapes):
        raise UnsupportedSvg("Logo 01 must consist of two filled links and two white separator bands.")
    return links, separators


def signet_visible_box(document: Document) -> tuple[float, float, float, float]:
    """Visible ink of the dynamic signet: both links, without transparent margins."""
    links, _ = signet_roles(document)
    return bounds([s.subpaths for s in links])


def signet_layers(document: Document, colors: tuple[RGB, RGB]) -> list[Layer]:
    """Theme-tinted Logo 01: links in ``colors``, separator bands become transparent cut-outs.

    The thin black separator strokes are dropped (no added outline, no white tile).
    ``colors`` maps to the links in painting order (yellow link, blue link).
    """
    links, _ = signet_roles(document)
    link_color = {links[0].index: colors[0], links[1].index: colors[1]}
    out: list[Layer] = []
    for shape in document.shapes:
        if shape.index in link_color:
            out.append(Layer(shape.subpaths, shape.fill_rule, link_color[shape.index]))
        else:
            out.append(Layer(shape.subpaths, shape.fill_rule, None, "erase"))
    return out


# --------------------------------------------------------------------- codecs
def _chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))


def encode_png(rows: list[bytes]) -> bytes:
    """Encode straight-alpha RGBA rows as an 8-bit PNG without row filters."""
    height = len(rows)
    width = len(rows[0]) // 4 if rows else 0
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    pixels = zlib.compress(b"".join(b"\0" + row for row in rows), 9)
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", header) + _chunk(b"IDAT", pixels) + _chunk(b"IEND", b"")


def decode_png(content: bytes) -> list[bytes]:
    """Return the RGBA rows of a PNG written by :func:`encode_png`."""
    if content[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a PNG file.")
    position, header, pixels = 8, None, b""
    while position < len(content):
        length, kind = struct.unpack(">I4s", content[position:position + 8])
        payload = content[position + 8:position + 8 + length]
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            pixels += payload
        position += length + 12
    if header is None or header[2:] != (8, 6, 0, 0, 0):
        raise ValueError("Unexpected PNG layout.")
    width, height = header[0], header[1]
    raw = zlib.decompress(pixels)
    stride = width * 4 + 1
    if len(raw) != height * stride or any(raw[row * stride] for row in range(height)):
        raise ValueError("Unexpected PNG pixel data.")
    return [raw[row * stride + 1:(row + 1) * stride] for row in range(height)]


ICO_BITMAP_LIMIT = 48  # Larger entries are stored as PNG, as Windows expects for 256 px.


def _ico_bitmap(rows: list[bytes]) -> bytes:
    size = len(rows)
    header = struct.pack("<IiiHHIIiiII", 40, size, size * 2, 1, 32, 0, 0, 0, 0, 0, 0)
    colour = bytearray()
    mask = bytearray()
    mask_stride = (size + 31) // 32 * 4
    for row in reversed(rows):
        bits = bytearray(mask_stride)
        for column in range(size):
            r, g, b, a = row[column * 4:column * 4 + 4]
            colour += bytes((b, g, r, a))
            if a == 0:
                bits[column // 8] |= 0x80 >> column % 8
        mask += bits
    return header + bytes(colour) + bytes(mask)


def encode_ico(images: dict[int, list[bytes]]) -> bytes:
    """Pack ``{size: rgba rows}`` into one multi-resolution Windows icon."""
    entries = [(size, _ico_bitmap(images[size]) if size <= ICO_BITMAP_LIMIT else encode_png(images[size]))
               for size in sorted(images)]
    directory = struct.pack("<HHH", 0, 1, len(entries))
    offset = 6 + 16 * len(entries)
    body = b""
    for size, payload in entries:
        directory += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(payload), offset)
        offset += len(payload)
        body += payload
    return directory + body


def decode_ico(content: bytes) -> dict[int, list[bytes]]:
    """Return ``{size: rgba rows}`` of an icon written by :func:`encode_ico`."""
    _, kind, count = struct.unpack("<HHH", content[:6])
    if kind != 1:
        raise ValueError("Not an icon file.")
    images: dict[int, list[bytes]] = {}
    for index in range(count):
        width, _, _, _, _, bits, length, offset = struct.unpack("<BBBBHHII", content[6 + 16 * index:22 + 16 * index])
        size = width or 256
        payload = content[offset:offset + length]
        if payload[:8] == b"\x89PNG\r\n\x1a\n":
            images[size] = decode_png(payload)
            continue
        if bits != 32 or struct.unpack("<IiiHH", payload[:16]) != (40, size, size * 2, 1, 32):
            raise ValueError("Unexpected icon bitmap layout.")
        rows = []
        for row in range(size - 1, -1, -1):
            line = payload[40 + row * size * 4:40 + (row + 1) * size * 4]
            rows.append(bytes(v for c in range(size)
                              for v in (line[c * 4 + 2], line[c * 4 + 1], line[c * 4], line[c * 4 + 3])))
        images[size] = rows
    return images


# Apple icon types with PNG payloads (pixel edge -> OSType). 16@2x == 32 px, etc.
ICNS_TYPES: tuple[tuple[bytes, int], ...] = (
    (b"icp4", 16), (b"icp5", 32), (b"icp6", 64), (b"ic07", 128), (b"ic08", 256),
    (b"ic09", 512), (b"ic10", 1024), (b"ic11", 32), (b"ic12", 64), (b"ic13", 256), (b"ic14", 512),
)


def encode_icns(images: dict[int, list[bytes]]) -> bytes:
    """Pack ``{pixel size: rows}`` into an Apple ``.icns`` container (PNG entries)."""
    body = b""
    for kind, size in ICNS_TYPES:
        payload = encode_png(images[size])
        body += kind + struct.pack(">I", len(payload) + 8) + payload
    return b"icns" + struct.pack(">I", len(body) + 8) + body


def decode_icns(content: bytes) -> dict[bytes, list[bytes]]:
    """Return ``{OSType: rows}`` of an ``.icns`` written by :func:`encode_icns`."""
    if content[:4] != b"icns" or struct.unpack(">I", content[4:8])[0] != len(content):
        raise ValueError("Not an icns file.")
    position, out = 8, {}
    while position < len(content):
        kind = content[position:position + 4]
        length = struct.unpack(">I", content[position + 4:position + 8])[0]
        out[kind] = decode_png(content[position + 8:position + length])
        position += length
    return out
