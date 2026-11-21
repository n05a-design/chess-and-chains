"""Headless validation of a candidate SVG chess-piece set."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import re
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from pathlib import Path


PIECE_FILE_NAMES = tuple(f"{c}{k}.svg" for c in "wb" for k in "KQRBNP")
MAX_SVG_BYTES = 256 * 1024
_FORBIDDEN_ELEMENTS = {"script", "foreignObject", "iframe", "object", "embed"}
_EXTERNAL_REF = re.compile(r"^\s*(?!#)(?:[a-z][a-z0-9+.-]*:|//|/|\.\.)", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class SvgContractReport:
    directory: Path
    problems: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.problems


def validate_svg_piece_set(directory: Path) -> SvgContractReport:
    """Check a candidate owner piece set: 12 files, safe SVG, provenance file present."""
    problems: list[str] = []
    if not (directory / "PROVENANCE.md").is_file():
        problems.append("PROVENANCE.md (author, licence, source file) is missing")
    for name in PIECE_FILE_NAMES:
        path = directory / name
        if not path.is_file():
            problems.append(f"{name}: missing")
            continue
        if path.stat().st_size > MAX_SVG_BYTES:
            problems.append(f"{name}: larger than {MAX_SVG_BYTES} bytes")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "<!ENTITY" in text or "<!DOCTYPE" in text:
            problems.append(f"{name}: DTD/entities are not allowed")
            continue
        try:
            root = ElementTree.fromstring(text)
        except ElementTree.ParseError as error:
            problems.append(f"{name}: not well-formed XML ({error})")
            continue
        if not root.tag.endswith("svg"):
            problems.append(f"{name}: root element is not <svg>")
        if not root.get("viewBox"):
            problems.append(f"{name}: viewBox is required for scaling")
        for element in root.iter():
            local = element.tag.rsplit("}", 1)[-1]
            if local in _FORBIDDEN_ELEMENTS:
                problems.append(f"{name}: forbidden element <{local}>")
            for attribute, value in element.attrib.items():
                attr = attribute.rsplit("}", 1)[-1]
                if attr.lower().startswith("on"):
                    problems.append(f"{name}: event handler attribute {attr}")
                if attr in ("href",) and _EXTERNAL_REF.match(value):
                    problems.append(f"{name}: external reference {value!r}")
    extra = sorted(p.name for p in directory.glob("*.svg") if p.name not in PIECE_FILE_NAMES) if directory.is_dir() else []
    problems.extend(f"{name}: unexpected file" for name in extra)
    return SvgContractReport(directory, tuple(problems))
