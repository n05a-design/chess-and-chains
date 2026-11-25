# Handoff-Bericht: W06 – Figurenset-Registry (Original V.03 / Draufsicht V.04 / Klassisch V.05)

**Datum:** 2026-11-25  
**Status:** IMPLEMENTED / TESTED  
**Paket:** W06 – Board, SVG, Interaction  
**Branch:** `main` (noch nicht committed; alle Änderungen liegen als unversioned/modified im Working Tree)  
**HEAD SHA vor diesem Auftrag:** `1f74088`

---

## 1. Umfang

Implementierung eines zentralen Drei-Figurenset-Registers für Chess & Chains:

| Interne ID | Bezeichnung (DE) | Bezeichnung (EN) | Asset-Version |
|------------|------------------|------------------|---------------|
| `original` | Original | Original | V.03 |
| `top` | Draufsicht | Top view | V.04 |
| `classic` | Klassisch | Classic | V.05 |

V.03 ist der neue Standard für Neuinstallationen (ersetzt V.02).  
V.02 bleibt in `assets/chess_pieces/archive/V.02/` erhalten, ist aber nicht mehr als auswählbares Set registriert.

---

## 2. Implementierte Dateien (geändert)

| Datei | Art | Inhalt |
|-------|-----|--------|
| `src/chess_and_chains/ui/pieces.py` | Kern | `PieceSetInfo`-Dataclass; `PIECE_SETS`-Registry; `get_piece_set()`, `list_piece_sets()`; `OwnerSvgPieces.set_piece_set()` |
| `src/chess_and_chains/ui/board.py` | Integration | `piece_set`-Property; `set_piece_set()`, `set_piece_view()` |
| `src/chess_and_chains/ui/marble_board.py` | Integration | `piece_set`-Property; `set_piece_set()`; Renderer-Cache nach `set_id` |
| `src/chess_and_chains/ui/captured_material.py` | Integration | `set_piece_renderer()`, `set_piece_set()` |
| `src/chess_and_chains/ui/app.py` | App | `set_piece_set()`, `_cycle_piece_set()`, Menü, `open_appearance_dialog()` |
| `src/chess_and_chains/ui/appearance_dialog.py` | Dialog | „Figurenset"-Dropdown, Live-Vorschau, `_snapshot()`, `_on_piece_set_change()` |
| `src/chess_and_chains/ui/__init__.py` | API | `launch(piece_set=…)` |
| `src/chess_and_chains/__main__.py` | CLI | `--piece-set original|top|classic`; `--piece-view` bleibt erhalten |
| `src/chess_and_chains/storage/settings.py` | Einstellungen | `Settings.piece_set`; `PIECE_SET_CHOICES`; `DEFAULT_PIECE_SET`; Migration aus `piece_view` |
| `src/chess_and_chains/i18n/catalog.py` | I18n | `board.piece_set.label/original/top/classic` in DE + EN |
| `docs/design/ASSET_REGISTER.csv` | Assets | SHA-256-Hashes für alle 24+12 SVGs + 3 Fallback-PNGs |
| `tests/test_app_integration.py` | Tests | Per-Figur-Bounds für V.03; angepasste Pixelkoordinaten |
| `tests/test_i18n.py` | Tests | `board.piece_set.original` zu `same_ok` ergänzt |

## 3. Neu hinzugefügte Dateien (untracked)

| Datei/Verzeichnis | Inhalt |
|-------------------|--------|
| `src/chess_and_chains/ui/piece_assets/original/` | 12 SVGs (wP wN wB wR wQ wK bP bN bB bR bQ bK) + fallback.png + PROVENANCE.md |
| `src/chess_and_chains/ui/piece_assets/classic/` | 12 SVGs + fallback.png + PROVENANCE.md |
| `assets/chess_pieces/masters/V.03/` | Editierbare Originale V.03 |
| `assets/chess_pieces/masters/V.04/` | Editierbare Originale V.04 |
| `assets/chess_pieces/masters/V.05/` | Editierbare Originale V.05 |
| `assets/chess_pieces/archive/V.02/` | Archivierte V.02-Dateien |
| `assets/chess_pieces/proof_sheets/` | SVG/PNG-Korrekturabzüge aller drei Sets |
| `design/V.03-*.svg/.jpg` | V.03-Quelldateien des Inhabers |
| `design/V.04-*.svg/.jpg/.af` | V.04-Quelldateien des Inhabers |
| `design/V.05-*.svg/.jpg` | V.05-Quelldateien des Inhabers |
| `design/V.06-*.svg/.jpg/.af` | V.06-Quelldateien des Inhabers (für spätere Überarbeitung) |
| `scripts/extract_piece_sets.py` | Extraktions-Skript für Einzel-SVGs aus Übersichtsdateien |
| `scripts/generate_piece_proof_sheets.py` | Korrekturabzug-Generator |
| `tests/test_piece_sets.py` | 11 neue Tests für die Registry |

---

## 4. Verifikation

```
pytest                                   # 347/347 passed, 1423 subtests (2× bestätigt)
python3 scripts/verify_starter.py        # PASS
python3 scripts/check_policy.py          # PASS
python3 scripts/verify_document_links.py # PASS
cd src && python3 -m glide_shell.selftest # 13/13 passed
```

Ausführungsumgebung: Python 3.14.5, Tk 9+, macOS (ARM), 2026-11-25.

---

## 5. Architektur-Entscheidungen

- **Stabile interne IDs** (`original`, `top`, `classic`) sind von Asset-Versionen entkoppelt. Eine Überarbeitung V.03 → V.06 erfordert keine Settings-Migration.
- **`PieceSetInfo`-Dataclass** ist die einzige Quelle für Figurenset-Metadaten; keine hartcodierten Fallunterscheidungen in Board- oder Dialog-Modulen.
- **Rückwärtskompatibilität**: `--piece-view top` und `set_piece_view()` bleiben funktionsfähig.
- **Einstellungs-Migration**: Alte JSON-Dateien mit `piece_view == "top"` werden transparent auf `piece_set = "top"` migriert.

---

## 6. Offene Punkte (nicht durch diesen Auftrag blockiert)

| ID | Beschreibung | Gate |
|----|--------------|------|
| – | Git commit + ggf. PR-Erstellung (erfordert explizite Owner-Freigabe, Q-019) | Q-019 |
| – | Native Sichtprüfung der drei Figurensets auf macOS und Windows durch den Inhaber | W06 |
| – | High-DPI-Verhalten der neuen SVGs auf Retina-Displays prüfen | W06 |
| – | V.06-Quelldateien des Inhabers vorhanden (design/V.06-*); Auftrag für Integration nicht erteilt | Backlog |

---

## 7. Nächste Aktionen (priorisiert)

1. **Git commit**: Alle geänderten und neuen Dateien in einem strukturierten Commit zusammenfassen (kein Push ohne Owner-Freigabe).
2. **Native Sichtprüfung** durch den Inhaber: App starten, alle drei Figurensets in Einstellungen > Darstellung wechseln, Spielbetrieb und Rätsel prüfen.
3. **V.06-Integration**: Falls der Inhaber V.06 als Nachfolger eines bestehenden Sets bestimmt, Auftrag erteilen.
4. **W06-Owner-Abnahme**: Ergebnis der Sichtprüfung als ACCEPTED/REJECTED dokumentieren.
