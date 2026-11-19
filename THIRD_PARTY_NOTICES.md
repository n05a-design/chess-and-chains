# Third-party notices and provenance ledger

**No third-party engines, chess libraries, downloaded puzzle datasets, fonts or competitor assets are included in this starter ZIP.** The only LICENSE file applies to original starter code/text, not implicitly to assets added later.

| Component / source | Current status | License reported by source | Release obligation |
| --- | --- | --- | --- |
| Stockfish | Candidate; NOT bundled | GPLv3 | Source and legal review before redistribution |
| python-chess | Candidate; NOT installed | GPLv3 or later per source | Incompatible with simply assuming own-only MPL terms |
| Chessnut | Candidate; NOT installed | Unlicense | Functional qualification plus provenance |
| Lichess puzzle CSV | Candidate; NOT downloaded | CC0 | Preserve dataset source/date and apply rules carefully |
| Glide Shell modules | Proposed only; NOT copied | Original files often MPL-2.0, dependencies may differ | Verify source/version/third-party assets individually |
| User SVG pieces | NOT delivered in ZIP | OWNER TO CONFIRM | Register file-level rights before publication |

Sources: `docs/research/SOURCES.md`; decision: `docs/legal/LICENSE_STRATEGY.md`.

Before release, generate a complete third-party component list with versions, hashes, license texts, downloadable source links, origin commit, and actual inventory of the exact distributable archive. **Do not guess SPDX IDs for unknown assets.**
