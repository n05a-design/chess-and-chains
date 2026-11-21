"""Tk desktop interface for the local Chess & Chains prototype."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .board_artwork import BoardDesign


def launch(*, board_design: BoardDesign | None = None, top_pieces: bool = False) -> None:
    from .app import launch as run

    run(board_design=board_design, top_pieces=top_pieces)


__all__ = ["launch"]
