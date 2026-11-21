# Original chess pieces

**Copyright:** Tim von Trostorff. **SPDX-License-Identifier: MPL-2.0.** The owner approved distribution with Chess & Chains on 20 November 2026. [Original SVG and owner record](../../../../assets/chess_pieces/source_svg/masters/PROVENANCE.md) · [MPL-2.0 text](../../../../LICENSE)

The twelve editable front views use the [owner's V.02 SVG](../../../../design/source/chess_pieces/V.02-Schachfiguren-Vorderansicht-Masspruefung.svg) as their source. The pawn, rook, bishop and king have local width and shoulder adjustments for optical balance. Knight and queen retain the supplied contour and collar paths. All exports use the 1.14-unit stroke on the same 64 × 64 tile and cover 78 × 108 pixels at 2× rendering. The shadow paths model the right flank, collar and foot with light from the upper left. Dark pieces use a lighter graphite lit surface and a deeper flank shadow than the preceding set. The shade paths are grouped under `shadows`, and `surface` is the editable base gradient. [Editable V.02 proof sheet](../../../../design/source/chess_pieces/V.02-Schachfiguren-Vorderansicht-Schatten.svg)

| Pieces | Group ID in the revised SVG |
| --- | --- |
| `wP.svg`, `bP.svg` | `wP-0-silhouette`, `wP-0-silhouette1` |
| `wR.svg`, `bR.svg` | `wR-0-silhouette`, `wR-0-silhouette1` |
| `wN.svg`, `bN.svg` | `wN-0-silhouette`, `wN-0-silhouette1` |
| `wB.svg`, `bB.svg` | `wB-0-silhouette`, `wB-0-silhouette1` |
| `wQ.svg`, `bQ.svg` | `wQ-0-silhouette`, `wQ-0-silhouette1` |
| `wK.svg`, `bK.svg` | `wK-0-silhouette`, `wK-0-silhouette1` |

The [top-view set](top/PROVENANCE.md) follows the top views of the original master. Tk 9 reads the SVGs directly. Tk versions without an SVG reader use each set's `fallback.png`, generated from the SVGs by [the build script](../../../../scripts/build_piece_fallback.py). After editing either set, run `python scripts/build_piece_fallback.py` with Tk 9 and a display. The packaged application reads only local resources.
