"""Derive editable dark plates and a marble board from the local SVG masters."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import argparse
from copy import deepcopy
from math import cos, radians, sin
from pathlib import Path
from random import Random
import xml.etree.ElementTree as ET


SVG = "http://www.w3.org/2000/svg"
NS = "{" + SVG + "}"
LIGHT_INK = "#1a1d22"
DARK_INK = "#f0f2f2"
FIGURES = tuple(zip("KQRBNP", ("koenig", "dame", "turm", "laeufer", "springer", "bauer")))
ET.register_namespace("", SVG)


def dark_color(fill: str) -> str:
    if fill == LIGHT_INK:
        return DARK_INK
    lightness = int(fill[1:3], 16)
    # Compress and invert the tone ramp to keep the pale veins subtle.
    value = round(34 + (240 - lightness) * 0.78)
    return f"#{value:02x}{value + 3:02x}{value + 7:02x}"


def invert(root: ET.Element) -> ET.Element:
    result = deepcopy(root)
    for element in result.iter():
        for attribute in ("fill", "stroke"):
            value = element.get(attribute)
            if value and value.startswith("#"):
                element.set(attribute, dark_color(value))
    return result


def write(root: ET.Element, target: Path) -> None:
    ET.indent(root)
    ET.ElementTree(root).write(target, encoding="utf-8", xml_declaration=True)


def vein_path(points: list[tuple[float, float]]) -> str:
    """Round a sampled vein with tangent-continuous cubic segments."""
    def coordinates(point: tuple[float, float]) -> str:
        return f"{point[0]:.2f} {point[1]:.2f}"

    commands = ["M" + coordinates(points[0])]
    for index, (a, b) in enumerate(zip(points, points[1:])):
        before = points[max(0, index - 1)]
        after = points[min(len(points) - 1, index + 2)]
        control_a = (a[0] + (b[0] - before[0]) / 6, a[1] + (b[1] - before[1]) / 6)
        control_b = (b[0] - (after[0] - a[0]) / 6, b[1] - (after[1] - a[1]) / 6)
        commands.append(f"C{coordinates(control_a)} {coordinates(control_b)} {coordinates(b)}")
    return " ".join(commands)


def field_marble(parent: ET.Element, square: str, row: int, column: int, pale: bool) -> None:
    rng = Random(0xC01D + (row * 8 + column) * 7919)
    pigment = rng.randint(225, 238) if pale else rng.randint(34, 46)
    mineral = f"#{pigment - 2:02x}{pigment:02x}{pigment + 2:02x}"
    ET.SubElement(parent, NS + "rect", {
        "id": f"stein-{square}", "width": "100", "height": "100", "fill": mineral,
    })
    clouds = ET.SubElement(parent, NS + "g", id=f"wolken-{square}")
    for index in range(3):
        white = (index % 2) == 0
        ET.SubElement(clouds, NS + "ellipse", {
            "cx": f"{rng.uniform(7, 93):.1f}", "cy": f"{rng.uniform(7, 93):.1f}",
            "rx": f"{rng.uniform(32, 66):.1f}", "ry": f"{rng.uniform(24, 52):.1f}",
            "fill": f"url(#mineralwolke-{'hell' if white else 'dunkel'})",
            "opacity": f"{rng.uniform(.22, .63) * (1 if pale else .53):.2f}",
        })
    veins = ET.SubElement(parent, NS + "g", {
        "id": f"adern-{square}", "fill": "none", "stroke-linecap": "round", "stroke-linejoin": "round",
        "stroke": "#68727b" if pale else "#b3bdca",
    })
    pattern = rng.randrange(3)
    low_count, high_count, flow_low, flow_high, ripple, spread = (
        (2, 3, .028, .064, 1.1, .19),
        (3, 5, .045, .085, 1.8, .27),
        (3, 5, .036, .094, 2.0, .43),
    )[pattern]
    heading = radians(rng.uniform(0, 180))
    root_offset = rng.uniform(-25, 24)
    for index in range(rng.randint(low_count, high_count)):
        angle = heading + rng.uniform(-spread, spread)
        base = root_offset if index == 0 else rng.uniform(-55, 55)
        flow = rng.uniform(flow_low, flow_high)
        phase = rng.uniform(-3, 3)
        bend = rng.uniform(4, 13)
        taper = rng.uniform(.4, 1.65)
        along = (cos(angle), sin(angle))
        across = (-along[1], along[0])
        drift = rng.uniform(-.18, .18)
        pivot = rng.uniform(-40, 40)
        kink = rng.uniform(-.29, .29) if pattern == 2 else rng.uniform(-.12, .12)

        def ridge(t: float) -> float:
            return (
                base + bend * sin(t * flow + phase) + ripple * sin(t * .22 - phase)
                + t * drift + kink * max(0, t - pivot)
            )

        def point(t: float, width: float) -> tuple[float, float]:
            return (50 + along[0] * t + across[0] * width, 50 + along[1] * t + across[1] * width)

        samples = list(range(-90, 91, 12))
        data = vein_path([point(t, ridge(t) + rng.uniform(-1.1, 1.1)) for t in samples])
        weight = rng.uniform(.76, 1.25) if index == 0 else rng.uniform(.37, .86)
        profile = ((8.4, .078), (3.35, .14), (.75, .23)) if pale else ((7.8, .075), (2.8, .105), (.65, .16))
        for layer, (band, opacity) in enumerate(profile):
            ET.SubElement(veins, NS + "path", {
                "id": f"ader-{square}-{index}-{layer}", "d": data,
                "stroke-width": f"{band * taper:.2f}", "opacity": f"{opacity * weight:.3f}",
            })

        origin = rng.randint(-37, 29)
        growth = rng.uniform(.23, .55) * rng.choice((-1, 1))
        branch = [point(origin + length, ridge(origin + length) + growth * length)
                  for length in (0, 7, 15, 23, 33, 45, 58, 74)]
        ET.SubElement(veins, NS + "path", {
            "id": f"nebenader-{square}-{index}", "d": vein_path(branch),
            "stroke-width": f"{rng.uniform(.38, 1.0):.2f}",
            "opacity": f"{weight * (.23 if pale else .16):.3f}",
        })


def board_svg() -> ET.Element:
    root = ET.Element(NS + "svg", {"width": "320mm", "height": "320mm", "viewBox": "0 0 864 864"})
    ET.SubElement(root, NS + "title").text = "Chess & Chains – Spielbrett aus kühlem Marmor"
    ET.SubElement(root, NS + "desc").text = "64 editierbare, einzeln geäderte Marmorfelder mit umlaufenden Koordinaten."
    defs = ET.SubElement(root, NS + "defs")
    clip = ET.SubElement(defs, NS + "clipPath", id="feldschnitt")
    ET.SubElement(clip, NS + "rect", width="100", height="100")
    for name, shade in (("hell", "#f5f7f9"), ("dunkel", "#767f89")):
        gradient = ET.SubElement(defs, NS + "radialGradient", id=f"mineralwolke-{name}")
        ET.SubElement(gradient, NS + "stop", {"offset": "0", "stop-color": shade, "stop-opacity": ".72"})
        ET.SubElement(gradient, NS + "stop", {"offset": "1", "stop-color": shade, "stop-opacity": "0"})

    ET.SubElement(root, NS + "rect", id="rahmen", width="864", height="864", fill="#1b1e24")
    ET.SubElement(
        root, NS + "rect",
        {"x": "29", "y": "29", "width": "806", "height": "806", "fill": "#565a61"},
    )
    fields = ET.SubElement(root, NS + "g", id="brettfelder")
    for row in range(8):
        for column in range(8):
            file = chr(ord("a") + column)
            square = f"{file}{8 - row}"
            field = ET.SubElement(fields, NS + "g", {
                "id": f"feld-{square}", "transform": f"translate({32 + 100 * column} {32 + 100 * row})",
            })
            cropped = ET.SubElement(field, NS + "g", {"clip-path": "url(#feldschnitt)"})
            field_marble(cropped, square, row, column, pale=(row + column) % 2 == 0)
            ET.SubElement(field, NS + "rect", {
                "x": ".55", "y": ".55", "width": "98.9", "height": "98.9",
                "fill": "none", "stroke": "#85848a", "stroke-opacity": ".32", "stroke-width": "1.1",
            })

    coordinates = ET.SubElement(root, NS + "g", {
        "id": "koordinaten", "fill": "#ecedf0", "font-family": "sans-serif",
        "font-size": "17", "text-anchor": "middle", "dominant-baseline": "central",
    })
    for index in range(8):
        x = y = 82 + 100 * index
        for at_x, at_y, angle, label in (
            (x, 848, 0, "abcdefgh"[index]), (x, 16, 180, "abcdefgh"[index]),
            (16, y, 0, str(8 - index)), (848, y, 180, str(8 - index)),
        ):
            text = ET.SubElement(coordinates, NS + "text", {"x": str(at_x), "y": str(at_y)})
            if angle:
                text.set("transform", f"rotate({angle} {at_x} {at_y})")
            text.text = label
    return root


def build(source: Path, target: Path) -> None:
    if (source / "Figuren").is_dir():
        files = [(letter, (source / "Figuren" / f"w{letter}.svg").read_bytes()) for letter, _ in FIGURES]
        sheet_path = source / "Weisser-Satz.svg"
    else:
        files = [(letter, (source / f"{index:02}-{name}.svg").read_bytes())
                 for index, (letter, name) in enumerate(FIGURES, 1)]
        sheet_path = source / "00-raster-3x2.svg"
    black_sheet = invert(ET.parse(sheet_path).getroot())
    black_sheet.find(NS + "title").text = "Schachfiguren auf schwarzem Marmor"
    black_sheet.set("aria-label", "Schachfiguren auf schwarzem Marmor")
    dark = [(letter, invert(ET.fromstring(content))) for letter, content in files]

    target.mkdir(parents=True)
    pieces = target / "Figuren"
    pieces.mkdir()
    for letter, content in files:
        (pieces / f"w{letter}.svg").write_bytes(content)
    for letter, root in dark:
        title = root.find(NS + "title")
        title.text = title.text.replace("kühlem Marmor", "schwarzem Marmor")
        root.set("aria-label", title.text)
        write(root, pieces / f"b{letter}.svg")
    write(board_svg(), target / "Brett.svg")
    (target / "Weisser-Satz.svg").write_bytes(sheet_path.read_bytes())
    write(black_sheet, target / "Schwarzer-Satz.svg")
    (pieces / "PROVENANCE.md").write_text(
        "# Lokaler Marmorsatz\n\n"
        "Die Figurenpfade stammen aus dem vom Owner bereitgestellten STL-Entwurf.\n"
        "Der helle Satz ist der im Chat gewählte kühle Vektor-Marmor. Der dunkle\n"
        "Satz verwendet identische Pfade mit invertierter Tonwertpalette.\n"
        "Die Marmorflächen wurden lokal prozedural erzeugt und vektorisiert.\n"
        "Die Rechte zur öffentlichen Auslieferung bleiben gemäß Q-003 offen.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Ordner mit dem hellen Marmor-Master oder veröffentlichten Spiels­atz")
    parser.add_argument("target", type=Path, help="Neuer Ausgabeordner für die Vektor-Master")
    args = parser.parse_args()
    build(args.source, args.target)
