# Original chess pieces

**Copyright:** Tim von Trostorff. **SPDX-License-Identifier: MPL-2.0.** The owner approved distribution with Chess & Chains on 20 November 2026. [Original SVG and owner record](../../../../assets/chess_pieces/source_svg/masters/PROVENANCE.md) · [MPL-2.0 text](../../../../LICENSE)

The twelve editable front views use the [owner's revised SVG](../../../../design/source/chess_pieces/Schachfiguren-Vorderansicht-Inhaberfassung.svg). Each face has the original silhouette and collar path data, including the 1.14-unit stroke and collar transforms normalized to its 64 × 64 tile. The 2× rendering still occupies the same 78 × 108-pixel bounds. The shadows use original vector paths and linear gradients inside the figure, with light from the upper left and deeper tone at the right flank, under the collar and at the foot. The shade paths are grouped under `shadows`, and `surface` is the editable base gradient. [Editable shadow proof sheet](../../../../design/source/chess_pieces/Schachfiguren-Vorderansicht-Schatten.svg)

| Pieces | Group ID in the revised SVG |
| --- | --- |
| `wP.svg`, `bP.svg` | `wP-0-silhouette`, `wP-0-silhouette1` |
| `wR.svg`, `bR.svg` | `wR-0-silhouette`, `wR-0-silhouette1` |
| `wN.svg`, `bN.svg` | `wN-0-silhouette`, `wN-0-silhouette1` |
| `wB.svg`, `bB.svg` | `wB-0-silhouette`, `wB-0-silhouette1` |
| `wQ.svg`, `bQ.svg` | `wQ-0-silhouette`, `wQ-0-silhouette1` |
| `wK.svg`, `bK.svg` | `wK-0-silhouette`, `wK-0-silhouette1` |

The [top-view set](top/PROVENANCE.md) follows the top views of the original master. Tk 9 reads the SVGs directly. Tk versions without an SVG reader use each set's `fallback.png`, generated from the SVGs by [the build script](../../../../scripts/build_piece_fallback.py). After editing either set, run `python scripts/build_piece_fallback.py` with Tk 9 and a display. The packaged application reads only local resources.
