"""Local Connected System preview and monochrome in-app logo engine.

- Preserves the original master SVGs and multi-color app icons unchanged.
- Dynamically crops and tints ``signet.svg`` in the active theme color for
  in-app monochrome display (borderless, transparent, zero tile/background).
- Provides a pure-Python anti-aliased transparent RGBA PNG fallback when
  running on Tk 8.6 without native SVG support.
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import base64
import functools
from importlib.resources import files
import math
import re
import struct
import tkinter as tk
import zlib

_HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")
_PATH_TOKEN_RE = re.compile(r"[MQVH]|-?\d+(?:\.\d+)?")
_PATH_D_RE = re.compile(r'\bd="([^"]+)"')
_STROKE_W_RE = re.compile(r'stroke-width="(\d+(?:\.\d+)?)"')


def brand_image(master: tk.Misc, name: str, *, scale: float = 1) -> tk.PhotoImage:
    """Load an untouched multi-color brand asset or PNG fallback (e.g. OS app-icon)."""
    assets = files(__package__).joinpath("brand_assets")
    try:
        return tk.PhotoImage(
            master=master,
            data=assets.joinpath(f"{name}.svg").read_bytes(),
            format=("svg", "-scale", scale),
        )
    except tk.TclError:
        # Tk 8.6 has PNG support but no native SVG reader.
        png = base64.b64encode(assets.joinpath(f"{name}.png").read_bytes())
        return tk.PhotoImage(master=master, data=png, format="png")


def macos_dock_icon(master: tk.Misc, name: str = "app-icon") -> tk.PhotoImage:
    """Return *name* centered at 824/1024 scale on a transparent canvas for macOS Dock/HIG."""
    import io
    import sys

    if sys.platform != "darwin":
        return brand_image(master, name)
    try:
        from PIL import Image
    except ImportError:
        return brand_image(master, name)

    assets = files(__package__).joinpath("brand_assets")
    png_bytes = assets.joinpath(f"{name}.png").read_bytes()
    with Image.open(io.BytesIO(png_bytes)) as src_img:
        rgba = src_img.convert("RGBA")
        size = max(rgba.width, rgba.height, 256)
        body_px = max(1, round(size * (824.0 / 1024.0)))
        offset = (size - body_px) // 2
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        resized = rgba.resize((body_px, body_px), Image.Resampling.LANCZOS)
        canvas.paste(resized, (offset, offset), resized)
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
    return tk.PhotoImage(master=master, data=base64.b64encode(buf.getvalue()), format="png")


@functools.lru_cache(maxsize=4)
def read_signet_svg() -> str:
    """Read and cache the original geometric master ``brand_assets/signet.svg``."""
    return files(__package__).joinpath("brand_assets", "signet.svg").read_text(encoding="utf-8")


def _parse_signet_polylines(svg: str, curve_steps: int = 12) -> tuple[list[list[tuple[float, float]]], float]:
    """Sample all ``M/Q/V/H`` strokes in ``svg`` and return ``(polylines, stroke_width)``."""
    sw_match = _STROKE_W_RE.search(svg)
    stroke_width = float(sw_match.group(1)) if sw_match else 8.0
    polylines: list[list[tuple[float, float]]] = []
    for d in _PATH_D_RE.findall(svg):
        tokens = _PATH_TOKEN_RE.findall(d)
        pts: list[tuple[float, float]] = []
        idx = 0
        cmd = ""
        cx, cy = 0.0, 0.0
        while idx < len(tokens):
            tok = tokens[idx]
            if tok in ("M", "Q", "V", "H"):
                cmd = tok
                idx += 1
                continue
            if cmd == "M":
                cx, cy = float(tokens[idx]), float(tokens[idx + 1])
                pts.append((cx, cy))
                idx += 2
            elif cmd == "H":
                cx = float(tokens[idx])
                pts.append((cx, cy))
                idx += 1
            elif cmd == "V":
                cy = float(tokens[idx])
                pts.append((cx, cy))
                idx += 1
            elif cmd == "Q":
                qx, qy = float(tokens[idx]), float(tokens[idx + 1])
                ex, ey = float(tokens[idx + 2]), float(tokens[idx + 3])
                sx, sy = cx, cy
                for s in range(1, curve_steps + 1):
                    t = s / curve_steps
                    u = 1.0 - t
                    px = u * u * sx + 2.0 * u * t * qx + t * t * ex
                    py = u * u * sy + 2.0 * u * t * qy + t * t * ey
                    pts.append((px, py))
                cx, cy = ex, ey
                idx += 4
            else:
                idx += 1
        if len(pts) >= 2:
            polylines.append(pts)
    return polylines, stroke_width


@functools.lru_cache(maxsize=4)
def signet_bounding_box(svg: str | None = None) -> tuple[float, float, float, float]:
    """Return ``(x, y, width, height)`` of the visible inked strokes without empty SVG margins."""
    source = read_signet_svg() if svg is None else svg
    polylines, stroke_width = _parse_signet_polylines(source, curve_steps=16)
    half_stroke = stroke_width * 0.5
    xs = [x for line in polylines for x, _y in line]
    ys = [y for line in polylines for _x, y in line]
    if not xs or not ys:
        return (0.0, 0.0, 64.0, 64.0)
    x0 = min(xs) - half_stroke
    y0 = min(ys) - half_stroke
    x1 = max(xs) + half_stroke
    y1 = max(ys) + half_stroke
    return (x0, y0, max(1.0, x1 - x0), max(1.0, y1 - y0))


def signet_aspect() -> float:
    """Return optical width / height aspect ratio of the cropped signet."""
    _x, _y, width, height = signet_bounding_box()
    return width / height


def cropped_signet_svg(svg: str, box: tuple[float, float, float, float] | None = None) -> str:
    """Rewrite root ``<svg>`` width, height, and viewBox tightly around ``box``."""
    x, y, width, height = signet_bounding_box(svg) if box is None else box
    header_match = re.search(r"<svg\b[^>]*>", svg)
    if header_match is None:
        raise ValueError("Missing <svg> element")
    tag = header_match.group(0)
    tag = re.sub(r'\sviewBox="[^"]*"', "", tag)
    tag = re.sub(r'\swidth="[^"]*"', "", tag)
    tag = re.sub(r'\sheight="[^"]*"', "", tag)
    tag = tag.replace(
        "<svg",
        f'<svg width="{width:.3f}" height="{height:.3f}" '
        f'viewBox="{x:.3f} {y:.3f} {width:.3f} {height:.3f}"',
        1,
    )
    return svg[:header_match.start()] + tag + svg[header_match.end():]


def tinted_signet_svg(color: str, *, crop: bool = True) -> str:
    """Return a monochrome ``signet.svg`` tinted to ``color`` without background or outline."""
    if not _HEX_RE.fullmatch(str(color)):
        raise ValueError(f"Expected #RRGGBB theme color, got {color!r}")
    raw = read_signet_svg()
    monochrome = re.sub(r'stroke="#[0-9A-Fa-f]{3,8}"', f'stroke="{color}"', raw)
    return cropped_signet_svg(monochrome) if crop else monochrome


def has_svg_support(master: tk.Misc) -> bool:
    """Probe whether Tk supports native SVG ``PhotoImage`` rendering (Tk 9+)."""
    try:
        probe = tk.PhotoImage(
            master=master,
            format="svg",
            data='<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>',
        )
        probe.tk.call("image", "delete", probe.name)
        return True
    except tk.TclError:
        return False


def _dist_to_segment_sq(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    vx, vy = bx - ax, by - ay
    denom = vx * vx + vy * vy
    if denom <= 1e-12:
        dx, dy = px - ax, py - ay
        return dx * dx + dy * dy
    t = ((px - ax) * vx + (py - ay) * vy) / denom
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    dx = px - (ax + t * vx)
    dy = py - (ay + t * vy)
    return dx * dx + dy * dy


@functools.lru_cache(maxsize=64)
def render_signet_rgba_png(
    height: int,
    color: str,
    box: tuple[float, float, float, float] | None = None,
) -> bytes:
    """Render an anti-aliased transparent monochrome PNG of the signet strokes using stdlib only."""
    if not isinstance(height, int) or not 1 <= height <= 2048:
        raise ValueError(f"Invalid logo height: {height!r}")
    if not _HEX_RE.fullmatch(str(color)):
        raise ValueError(f"Expected #RRGGBB color: {color!r}")

    svg = read_signet_svg()
    bx, by, bw, bh = signet_bounding_box(svg) if box is None else box
    width = max(1, round(bw * height / bh))
    scale_x = bw / width
    scale_y = bh / height

    polylines, stroke_width = _parse_signet_polylines(svg, curve_steps=16)
    segments = [
        (pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
        for pts in polylines
        for i in range(len(pts) - 1)
    ]
    half_stroke = stroke_width * 0.5
    #Butt/miter corner threshold around 4px stroke radius (svg uses miter joins & butt caps;
    #dist_to_segment handles rounded corners faithfully along Q curves and butt ends via t-clamp).
    pixel_aa_half = 0.6 * max(scale_x, scale_y)
    inner_sq = max(0.0, half_stroke - pixel_aa_half) ** 2
    outer_sq = (half_stroke + pixel_aa_half) ** 2

    r_val = int(color[1:3], 16)
    g_val = int(color[3:5], 16)
    b_val = int(color[5:7], 16)
    rgb = bytes((r_val, g_val, b_val))

    sub_offsets = (0.125, 0.375, 0.625, 0.875)
    n_sub = len(sub_offsets) * len(sub_offsets)

    raw_rows = bytearray()
    for py in range(height):
        raw_rows.append(0)
        wy_center = by + (py + 0.5) * scale_y
        for px in range(width):
            wx_center = bx + (px + 0.5) * scale_x
            best_sq = min(
                _dist_to_segment_sq(wx_center, wy_center, ax, ay, ex, ey)
                for ax, ay, ex, ey in segments
            )
            if best_sq <= inner_sq:
                alpha = 255
            elif best_sq >= outer_sq:
                alpha = 0
            else:
                hits = 0
                for oy in sub_offsets:
                    sy = by + (py + oy) * scale_y
                    for ox in sub_offsets:
                        sx = bx + (px + ox) * scale_x
                        d_sq = min(
                            _dist_to_segment_sq(sx, sy, ax, ay, ex, ey)
                            for ax, ay, ex, ey in segments
                        )
                        if d_sq <= half_stroke * half_stroke:
                            hits += 1
                alpha = min(255, max(0, round(hits * 255 / n_sub)))
            raw_rows.extend(rgb)
            raw_rows.append(alpha)

    def _chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))

    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(bytes(raw_rows), 9))
        + _chunk(b"IEND", b"")
    )


def in_app_logo_photo(master: tk.Misc, height: int, color: str) -> tk.PhotoImage:
    """Create a borderless, monochrome, cropped signet ``PhotoImage`` at ``height`` px."""
    target_h = max(1, int(height))
    svg = tinted_signet_svg(color, crop=True)
    if has_svg_support(master):
        try:
            return tk.PhotoImage(
                master=master,
                data=svg.encode("utf-8"),
                format=("svg", "-scaletoheight", target_h),
            )
        except tk.TclError:
            pass
    png_bytes = render_signet_rgba_png(target_h, color)
    encoded = base64.b64encode(png_bytes)
    return tk.PhotoImage(master=master, data=encoded, format="png")


def draw_signet_canvas(canvas: tk.Canvas, height: int, color: str, *, tag: str = "logo") -> int:
    """Render the monochrome cropped signet directly onto ``canvas`` without background."""
    target_h = max(1, int(height))
    target_w = max(1, round(target_h * signet_aspect()))
    canvas.delete(tag)
    canvas.configure(width=target_w, height=target_h)
    try:
        photo = in_app_logo_photo(canvas, target_h, color)
    except (tk.TclError, ValueError, OSError):
        photo = None
    canvas._logo_image = photo  # type: ignore[attr-defined]
    canvas._logo_color = color  # type: ignore[attr-defined]
    canvas._logo_height = target_h  # type: ignore[attr-defined]
    if photo is not None:
        w = max(1, photo.width())
        h = max(1, photo.height())
        canvas.configure(width=w, height=h)
        canvas.create_image(0, 0, image=photo, anchor="nw", tags=(tag,))
        canvas.tag_raise(tag)
        return w

    # Pure vector fallback on Canvas if image decoding is unavailable.
    bx, by, _bw, bh = signet_bounding_box()
    polylines, stroke_width = _parse_signet_polylines(read_signet_svg(), curve_steps=16)
    scale = target_h / bh
    line_w = max(1, round(stroke_width * scale))
    for pts in polylines:
        coords: list[float] = []
        for px, py in pts:
            coords.extend(((px - bx) * scale, (py - by) * scale))
        canvas.create_line(*coords, fill=color, width=line_w, joinstyle=tk.MITER, tags=(tag,))
    canvas.tag_raise(tag)
    return target_w
