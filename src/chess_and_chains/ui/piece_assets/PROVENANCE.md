# Original chess pieces

**Copyright:** Tim von Trostorff. **SPDX-License-Identifier: MPL-2.0.** The owner approved distribution with Chess & Chains on 20 November 2026. [Original SVG and owner record](../../../../assets/chess_pieces/source_svg/masters/PROVENANCE.md) · [MPL-2.0 text](../../../../LICENSE)

The twelve editable 64 × 64 SVGs retain the original front-view paths. The exports use the same scale and baseline. The white and black versions place a contrasting fill under the original outline.

| Pieces | Master group |
| --- | --- |
| `wP.svg`, `bP.svg` | `vector-0062` |
| `wR.svg`, `bR.svg` | `vector-0094` |
| `wN.svg`, `bN.svg` | `vector-0128` |
| `wB.svg`, `bB.svg` | `vector-00941` |
| `wQ.svg`, `bQ.svg` | `vector-0193` |
| `wK.svg`, `bK.svg` | `vector-0225` |

Tk 9 reads the SVGs directly. Tk versions without an SVG reader use `fallback.png`, generated from these same SVGs by [the build script](../../../../scripts/build_piece_fallback.py). After editing the SVGs, run `python scripts/build_piece_fallback.py` with Tk 9 and a display. The packaged application reads only local resources.
