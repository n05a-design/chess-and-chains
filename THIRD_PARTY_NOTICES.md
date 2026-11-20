# Third-party notices and provenance ledger

**No third-party engines, chess libraries, downloaded puzzle datasets, fonts or competitor assets are included in this starter ZIP.** The only LICENSE file applies to original starter code/text, not implicitly to assets added later.

| Component / source | Current status | License reported by source | Release obligation |
| --- | --- | --- | --- |
| Stockfish 19 (`sf_19`) | Research candidate; no binary downloaded or bundled | GPLv3 per official README/Copying | Exact binary/source/NNUE inventory and legal review before redistribution |
| python-chess | Candidate; NOT installed | GPLv3 or later per source | Incompatible with simply assuming own-only MPL terms |
| Chessnut | Candidate; NOT installed | Unlicense | Functional qualification plus provenance |
| Lichess puzzle CSV | Candidate; NOT downloaded | CC0 | Preserve dataset source/date and apply rules carefully |
| Glide Shell modules | Proposed only; NOT copied | Original files often MPL-2.0, dependencies may differ | Verify source/version/third-party assets individually |
| User SVG pieces | NOT delivered in ZIP | OWNER TO CONFIRM | Register file-level rights before publication |
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
