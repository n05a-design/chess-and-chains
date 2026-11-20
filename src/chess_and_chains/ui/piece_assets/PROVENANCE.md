# Original chess pieces

**Copyright:** Tim von Trostorff. **SPDX-License-Identifier: MPL-2.0.** The owner approved distribution with Chess & Chains on 20 November 2026. [Original SVG and owner record](../../../../assets/chess_pieces/source_svg/masters/PROVENANCE.md) · [MPL-2.0 text](../../../../LICENSE)

The editable front-view SVGs use a 64 × 64 canvas, a half-unit grid and a two-unit stroke. The visible front-view bounds are 39 × 54 including the outline, from `(12.5, 5)` to `(51.5, 59)`, with a baseline at `y=59`. The stepped edges in the source were redrawn with straight lines and Bézier curves. White and black versions use the same paths with reversed ivory and ink colors. The bishop's side notch is deeper, and the king has a raised cross derived from the cross motif in the owner's top view. The queen retains its rounded crown.

| Pieces | Master group |
| --- | --- |
| `wP.svg`, `bP.svg` | `vector-0062` |
| `wR.svg`, `bR.svg` | `vector-0094` |
| `wN.svg`, `bN.svg` | `vector-0128` |
| `wB.svg`, `bB.svg` | `vector-00941` |
| `wQ.svg`, `bQ.svg` | `vector-0193` |
| `wK.svg`, `bK.svg` | `vector-0225` |

The [top-view set](top/PROVENANCE.md) follows the separate top views in the same master. Tk 9 reads the SVGs directly. Tk versions without an SVG reader use each set's `fallback.png`, generated from the SVGs by [the build script](../../../../scripts/build_piece_fallback.py). After editing either set, run `python scripts/build_piece_fallback.py` with Tk 9 and a display. The packaged application reads only local resources.
