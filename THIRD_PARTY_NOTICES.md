# Third-party notices and provenance ledger

**Runtime inventory for V.0.0.1.** The Python package uses the original rules and mock engine, the owner's pieces, and the Connected System runtime assets. Design sources and their individual attribution are recorded in the [asset register](docs/design/ASSET_REGISTER.csv).

| Component / source | Current status | License reported by source | Release obligation |
| --- | --- | --- | --- |
| Stockfish 19 (`sf_19`) | Owner-approved isolated local installation; external UCI process; excluded from repository and installer | GPLv3 per official README/Copying | Exact binary/source/NNUE inventory and legal review before redistribution |
| python-chess | Candidate; NOT installed | GPLv3 or later per source | Incompatible with simply assuming own-only MPL terms |
| Chessnut | Candidate; NOT installed | Unlicense | Functional qualification plus provenance |
| Lichess puzzle CSV | Candidate; NOT downloaded | CC0 | Preserve dataset source/date and apply rules carefully |
| Glide Shell modules | Proposed only; NOT copied | Original files often MPL-2.0, dependencies may differ | Verify source/version/third-party assets individually |
| User SVG pieces | Owner-created vector master, 24 derived SVGs in front and top views, two PNG atlases | MPL-2.0, approved by Tim von Trostorff on 20 November 2026 | Preserve the [master provenance](assets/chess_pieces/source_svg/masters/PROVENANCE.md) and [runtime attribution](src/chess_and_chains/ui/piece_assets/PROVENANCE.md) |
| Manufacturing Consent Regular | Wordmark source and derived SVG outline and PNG in the app. A separate version 3.000 font file is stored among the historical design sources. | OFL-1.1 per [upstream at 80c3d82](https://github.com/googlefonts/manufacturing-consent-font/blob/80c3d822c2459ac0d76f8cb9d7ca1ca89a068f3b/OFL.txt) | The repository archive includes the supplied license text. The installed application uses the rendered wordmark. Both font hashes are recorded in the [asset register](docs/design/ASSET_REGISTER.csv). |
| CairoSVG 2.9.1 | Research candidate; not a project dependency; temporary evaluation only | LGPL-3.0-or-later per PyPI | Runtime adoption requires dependency/license inventory and native Cairo packaging review |
| cairocffi 1.7.1 | Research candidate; not a project dependency; temporary evaluation only | BSD per PyPI | Native Cairo is separately required; verify exact bundled versions and notices |
| CairoSVG transitive Python dependencies | Temporary research environment only; not project dependencies | Not yet individually inventoried | Verify licenses and versions before any runtime integration |

Sources: `docs/research/SOURCES.md`; decision: `docs/legal/LICENSE_STRATEGY.md`.

## W02 source check (2026-11-20)

These are versioned research references only; none is a dependency or bundled
component in this repository:

| Candidate | Verified upstream commit | License-file/source result |
| --- | --- | --- |
| Stockfish | `5d03b6e578a5eedc822e4563bdbb89e762fc2a59` | `Copying.txt`: GPLv3; upstream README lists NNUE files in distributions and describes source/license obligations |
| python-chess | `0c6bdaccfcb3b09cdbe94b0f81e948cb2a356015` | `LICENSE.txt`: GPLv3 |
| Chessnut | `8af90b93f8a10437495c65733c25cde94b615bb7` | `UNLICENSE.txt`: Unlicense; still only a rules-library candidate pending technical qualification |

Do not treat this dated check as permission to redistribute, bundle or link
these components. Re-check the exact versions and artifacts for any proposed
release.

Before release, generate a complete third-party component list with versions, hashes, license texts, downloadable source links, origin commit, and actual inventory of the exact distributable archive. **Do not guess SPDX IDs for unknown assets.**
