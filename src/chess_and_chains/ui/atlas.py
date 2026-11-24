"""A non-interactive route through the current filtered puzzle selection."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import tkinter as tk
from collections.abc import Sequence, Set

from ..puzzles import PuzzleSession
from ..puzzles.model import Puzzle
from .theme import LIGHT_THEME, ThemePalette


class PuzzleAtlas(tk.Canvas):
    """Draw nearby stations alongside the textual puzzle status and pack totals."""

    def __init__(self, master: tk.Misc, theme: ThemePalette = LIGHT_THEME) -> None:
        self._theme = theme
        super().__init__(master, height=66, width=1, background=theme.paper, highlightthickness=0, takefocus=False)
        self._stations: tuple[tuple[int, str, bool], ...] = ()
        self.bind("<Configure>", self._draw)

    def set_theme(self, theme: ThemePalette) -> None:
        self._theme = theme
        self.configure(background=theme.paper)
        self._draw()

    def update_route(
        self, puzzles: Sequence[Puzzle], index: int, session: PuzzleSession | None, solved: Set[str],
    ) -> None:
        count = min(len(puzzles), 5)
        start = max(0, min(index - count // 2, len(puzzles) - count))
        stations = []
        for position in range(start, start + count):
            current = position == index and session is not None
            if puzzles[position].puzzle_id in solved or (current and session.solved):
                state = "solved"
            elif current and session.revealed:
                state = "revealed"
            else:
                state = "open"
            stations.append((position + 1, state, current))
        self._stations = tuple(stations)
        self._draw()

    def _draw(self, _event: tk.Event | None = None) -> None:
        self.delete("all")
        width = self.winfo_width()
        if not self._stations or width < 45:
            return
        t = self._theme
        step = (width - 24) / len(self._stations)
        points = [(12 + (offset + .5) * step, 18 + 12 * (offset % 2)) for offset in range(len(self._stations))]
        for (left, top), (right, bottom) in zip(points, points[1:]):
            middle = (left + right) / 2
            self.create_line(left, top, middle, top, middle, bottom, right, bottom,
                             fill=t.atlas_line, width=2, joinstyle=tk.ROUND)
        for (x, y), (number, state, current) in zip(points, self._stations):
            if current:
                self.create_oval(x - 12, y - 12, x + 12, y + 12, outline=t.focus_ink, width=2, tags=("atlas-current",))
            marker = t.brand_blue if state == "solved" else t.brand_red if state == "revealed" else t.ink
            fill = t.brand_blue if state == "solved" else t.action_new_bg if current and state == "open" else t.paper
            self.create_oval(x - 8, y - 8, x + 8, y + 8, fill=fill, outline=marker, width=2,
                             tags=(f"atlas-{state}",))
            if state == "solved":
                self.create_line(x - 4, y, x - 1, y + 3, x + 4, y - 3, fill=t.selection_text, width=2)
            elif state == "revealed":
                self.create_line(x - 3, y - 3, x + 3, y + 3, fill=t.brand_red, width=2)
                self.create_line(x - 3, y + 3, x + 3, y - 3, fill=t.brand_red, width=2)
            self.create_text(x, 53, text=str(number), fill=t.ink, font=("TkFixedFont", 9))
