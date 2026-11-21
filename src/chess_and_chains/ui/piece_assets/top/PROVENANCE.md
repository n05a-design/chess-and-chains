# Original chess pieces · top view

**Copyright:** Tim von Trostorff. **SPDX-License-Identifier: MPL-2.0.** The owner approved distribution with Chess & Chains on 20 November 2026. [Unmodified SVG master and owner record](../../../../../assets/chess_pieces/source_svg/masters/PROVENANCE.md) · [MPL-2.0 text](../../../../../LICENSE)

These editable 64 × 64 SVGs redraw the six top views from the master on a shared half-unit grid. The discs have a center at `(32, 32)` and an outside diameter of 52 units, including the two-unit outline. White and black share the same geometry with reversed colors. The inner circle, double line, wedge, radial divisions and diagonal cross follow the source motifs.

| Pieces | Master group | Motif |
| --- | --- | --- |
| `wP.svg`, `bP.svg` | `vector-0078` | Two concentric circles |
| `wR.svg`, `bR.svg` | `vector-0109` | Eight outer segments |
| `wN.svg`, `bN.svg` | `vector-0144` | Tapered wedge |
| `wB.svg`, `bB.svg` | Third child group in `_04-·-Figuren-01-06`, no ID | Offset double line |
| `wQ.svg`, `bQ.svg` | `vector-0208` | Ten outer segments and a small inner circle |
| `wK.svg`, `bK.svg` | `vector-0241` | Ten outer segments and a diagonal cross |

Use `--piece-view top` to preview this set in the app. Tk 9 reads the SVGs directly. Regenerate `fallback.png` after edits with `python scripts/build_piece_fallback.py`. [Front-view set and runtime notes](../PROVENANCE.md)
