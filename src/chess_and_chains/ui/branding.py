"""Chess & Chains logo roles for the Tk desktop app.

Three owner masters (``design/01_Logo/svg``), three roles:

``in_app`` – Logo 01, ``brand_assets/signet.svg``
    The header signet. Tinted at runtime in the active, contrast-checked theme
    role (``ThemePalette.view_title``). The white separator bands of the master
    become transparent cut-outs and their hairline strokes are dropped, so the
    overpass of the two links stays legible without an outline or a tile.
``internal_brand`` – Logo 02, ``brand_assets/brand-emblem.svg``
    Full-colour emblem for the About dialog. Never tinted.
``app_icon`` – Logo 03, ``brand_assets/app-icon.svg``
    Window, taskbar and Dock icon. Never tinted.

All derived rasters come from ``scripts/build_brand_assets.py``. The in-app
signet is rasterised at its exact pixel height by the standard-library
renderer in :mod:`.brand_raster`, so the transparent cut-outs and the tint
work identically on Tk 8.6 (no SVG) and Tk 9 (nanosvg cannot erase).
"""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import base64
import functools
from importlib.resources import files
from pathlib import Path
import re
import sys
import tkinter as tk

from . import brand_raster

_HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")

LOGO_ROLES: dict[str, str] = {
    "in_app": "signet",
    "internal_brand": "brand-emblem",
    "app_icon": "app-icon",
}
WINDOW_ICON_SIZES = (16, 32, 48, 64, 128, 256)


def _assets():
    return files(__package__).joinpath("brand_assets")


def asset_bytes(name: str) -> bytes:
    """Return the bytes of one packaged brand resource, e.g. ``"app-icon-32.png"``."""
    return _assets().joinpath(name).read_bytes()


def _png_photo(master: tk.Misc, data: bytes) -> tk.PhotoImage:
    return tk.PhotoImage(master=master, data=base64.b64encode(data), format="png")


def has_svg_support(master: tk.Misc) -> bool:
    """Probe whether this Tk build reads SVG ``PhotoImage`` data (Tk 9+ / tksvg)."""
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


def brand_image(master: tk.Misc, name: str, *, scale: float = 1) -> tk.PhotoImage:
    """Load an untouched full-colour brand asset, with its PNG fallback on Tk 8.6."""
    try:
        return tk.PhotoImage(master=master, data=asset_bytes(f"{name}.svg"), format=("svg", "-scale", scale))
    except tk.TclError:
        return _png_photo(master, asset_bytes(f"{name}.png"))


def emblem_image(master: tk.Misc, height: int = 96) -> tk.PhotoImage:
    """Logo 02 (full colour, never tinted) at ``height`` px for the About dialog."""
    target = max(16, int(height))
    if has_svg_support(master):
        try:
            return tk.PhotoImage(
                master=master, data=asset_bytes("brand-emblem.svg"), format=("svg", "-scaletoheight", target),
            )
        except tk.TclError:
            pass
    name = "brand-emblem-192.png" if target > 120 else "brand-emblem.png"
    return _png_photo(master, asset_bytes(name))


def _ico_path() -> Path | None:
    resource = _assets().joinpath("app-icon.ico")
    path = Path(str(resource))
    return path if path.is_file() else None


def macos_dock_icon(master: tk.Misc, name: str = "app-icon") -> tk.PhotoImage:
    """Logo 03 for the macOS Dock: inside the transparent Apple icon grid (824/1024)."""
    if sys.platform == "darwin" and name == "app-icon":
        return _png_photo(master, asset_bytes("app-icon-macos.png"))
    return brand_image(master, name)


def window_icon_photos(master: tk.Misc) -> list[tk.PhotoImage]:
    """Logo 03 in every window-icon size, largest first (Tk picks per context)."""
    if sys.platform == "darwin":
        return [macos_dock_icon(master)]
    names = {256: "app-icon.png"}
    return [
        _png_photo(master, asset_bytes(names.get(size, f"app-icon-{size}.png")))
        for size in sorted(WINDOW_ICON_SIZES, reverse=True)
    ]


def apply_window_icon(root: tk.Tk) -> list[tk.PhotoImage]:
    """Set Logo 03 as default icon for ``root`` and all later dialogs.

    Windows additionally receives the multi-resolution ICO for taskbar and
    Alt-Tab. Keep the returned images referenced for the window's lifetime.
    """
    photos = window_icon_photos(root)
    root.iconphoto(True, *photos)
    if sys.platform == "win32":
        ico = _ico_path()
        if ico is not None:
            try:
                root.iconbitmap(default=str(ico))
            except tk.TclError:
                pass
    return photos


# --------------------------------------------------------------------------- Logo 01
@functools.lru_cache(maxsize=1)
def read_signet_svg() -> str:
    """Read and cache Logo 01 (byte copy of the master) from ``brand_assets/signet.svg``."""
    return asset_bytes("signet.svg").decode("utf-8")


@functools.lru_cache(maxsize=1)
def signet_document() -> brand_raster.Document:
    return brand_raster.parse_svg(read_signet_svg().encode("utf-8"))


@functools.lru_cache(maxsize=4)
def signet_bounding_box(svg: str | None = None) -> tuple[float, float, float, float]:
    """Return ``(x, y, width, height)`` of the visible links (viewBox units, no empty margins).

    The square 842 × 842 viewBox has wide transparent margins; the separator
    bands are transparent in the in-app variant and do not count as ink.
    """
    document = signet_document() if svg is None else brand_raster.parse_svg(svg.encode("utf-8"))
    return brand_raster.signet_visible_box(document)


def signet_aspect() -> float:
    """Return the visible width / height ratio of the in-app signet."""
    _x, _y, width, height = signet_bounding_box()
    return width / height


def cropped_signet_svg(svg: str, box: tuple[float, float, float, float] | None = None) -> str:
    """Rewrite the root ``<svg>`` width, height and viewBox tightly around ``box``."""
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


def tinted_signet_svg(color: str, *, crop: bool = True, background: str = "#FFFFFF") -> str:
    """Return Logo 01 as SVG with both links in ``color`` and separators in ``background``.

    For SVG consumers without erase compositing (background-matched separation).
    The app itself uses :func:`render_signet_rgba_png` with true transparency.
    """
    for value in (color, background):
        if not _HEX_RE.fullmatch(str(value)):
            raise ValueError(f"Expected #RRGGBB colour, got {value!r}")
    svg = read_signet_svg()
    svg = svg.replace("fill:rgb(244,196,0);", f"fill:{color};").replace("fill:rgb(36,71,216);", f"fill:{color};")
    svg = re.sub(r"fill:white;stroke:black;stroke-width:[\d.]+px;", f"fill:{background};", svg)
    return cropped_signet_svg(svg) if crop else svg


def _rgb(color: str) -> tuple[int, int, int]:
    return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))


@functools.lru_cache(maxsize=64)
def render_signet_rgba_png(
    height: int,
    color: str,
    box: tuple[float, float, float, float] | None = None,
) -> bytes:
    """Render the theme-tinted signet as transparent PNG of ``height`` px (stdlib only)."""
    if not isinstance(height, int) or not 1 <= height <= 2048:
        raise ValueError(f"Invalid logo height: {height!r}")
    if not _HEX_RE.fullmatch(str(color)):
        raise ValueError(f"Expected #RRGGBB color: {color!r}")
    document = signet_document()
    frame_box = brand_raster.signet_visible_box(document) if box is None else box
    width = max(1, round(frame_box[2] * height / frame_box[3]))
    rgb = _rgb(color)
    layers = brand_raster.signet_layers(document, (rgb, rgb))
    rows = brand_raster.render(layers, brand_raster.Frame.fit(frame_box, width, height))
    return brand_raster.encode_png(rows)


def in_app_logo_photo(master: tk.Misc, height: int, color: str) -> tk.PhotoImage:
    """Borderless, transparent, theme-tinted Logo 01 ``PhotoImage`` at ``height`` px."""
    return _png_photo(master, render_signet_rgba_png(max(1, int(height)), color))


def draw_signet_canvas(canvas: tk.Canvas, height: int, color: str, *, tag: str = "logo") -> int:
    """Render the tinted signet onto ``canvas`` (no background) and return its width."""
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

    # Vector fallback: background-matched separators (no erase on a Canvas).
    document = signet_document()
    links, _separators = brand_raster.signet_roles(document)
    link_ids = {shape.index for shape in links}
    bx, by, _bw, bh = signet_bounding_box()
    scale = target_h / bh
    background = str(canvas.cget("background"))

    def poly(points, fill: str) -> None:
        coords = [v for px, py in points for v in ((px - bx) * scale, (py - by) * scale)]
        canvas.create_polygon(*coords, fill=fill, outline="", tags=(tag,))

    previous = None
    for shape in document.shapes:
        if shape.index in link_ids:
            for path in shape.subpaths:
                poly(path, color)
            previous = shape
        else:
            poly(shape.subpaths[0], background)  # outer edge of the separator band
            if previous is not None:
                for path in previous.subpaths:
                    poly(path, color)
    canvas.tag_raise(tag)
    return target_w
