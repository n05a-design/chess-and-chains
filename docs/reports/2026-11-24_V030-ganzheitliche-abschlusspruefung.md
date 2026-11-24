# Chess & Chains V.0.3.0 – Ganzheitliche Abschlussprüfung der UI-/UX-Optimierung

**Datum:** 2026-11-24  
**Branch:** `main` (4 Commits vor `origin/main`: `13e9658`, `cfc69d7`, `fea997f`, `8e333d6`; noch nicht gepusht gemäß `AGENTS.md` Regel 3)

## 1. Geprüfte Bereiche

- **Dynamische SVG-Logo-Integration:** Monochromes Signet in `branding.py` / `app.py` ohne weißen Hintergrund/Kachel, Themenfarben-gekoppelt.
- **macOS App-Icon (Apple HIG):** `build_icns()` in `packaging/macos/build_app.py` und `macos_dock_icon()` in `branding.py` skalieren den Icon-Körper auf `824 / 1024` (~80,47 %) zentriert auf transparenter Fläche.
- **Marmorbrett 2D/3D & Themenfarben:** Orthogonale Vogelperspektive (2D) und räumliche Perspektive (3D) entkoppelt von Brettdesign und Figurenansicht; exakte Markierungszentrierung.
- **Dialog-Rendering & Dark-Mode-Kontrast:** Bauernumwandlungsdialog, PositionDialog, ReplayDialog, TextBoardDialog und Einstellungsdialog übernehmen vollständig `ThemePalette`-Tokens.
- **Geschlagene Figuren & Materialvorteil:** `chess/material.py` (reine Domain-Logik ohne `tkinter`/`glide_shell`), `ui/captured_material.py`, integriert in Hauptbrett und `ReplayDialog`.
- **Dropdown-basierter Einstellungsdialog nach Glide:** `ui/dropdown.py` (`GlideDropdown`) + `ui/appearance_dialog.py` (flaches 2-Spalten-Layout, Sticky-Footer, Live-Vorschau mit Abbrechen-Rollback, Brettdesign→Perspektive-Abhängigkeit).

## 2. Glide-Shell-Wiederverwendung

- `src/glide_shell/` blieb vollständig unverändert (`manifest: 23 files match manifest (7dcd8dc04366)`).
- Wiederverwendet: `modal_session`, `rounded_rect_points`, `ThemedAutoScrollbar`, `window_geometry`, `ThemePalette`.
- Neu ergänzt (da nicht in `glide_shell.custom_controls` enthalten): `GlideDropdown` in `src/chess_and_chains/ui/dropdown.py` als neutraler Canvas-Adapter ohne Aqua-Dark-Mode-Defekt.

## 3. Verifikation & Nachweise

- `cd src && python3 -m glide_shell.selftest` → **13/13 checks passed**
- `python3 scripts/verify_starter.py` → **PASS**
- `python3 scripts/check_policy.py` → **PASS**
- `python3 scripts/verify_document_links.py` → **PASS**
- `PYTHONPATH=src python3 -m unittest tests.test_final_audit -v` → **4/4 OK** (Negativ-/Gegenproben: HIG-Transparenzrand, deaktiviertes Dropdown, Standard→2D-Abhängigkeit & Cancel-Rollback, unbekannte Theme-ID)
- `PYTHONPATH=src python3 -m unittest discover -s tests -q` → **308 Tests** (wird nach Abschlussbericht final bestätigt)
- Live-Screenshots unter macOS im isolierten Datenordner: `audit_settings_light.png`, `audit_settings_dark.png`.

## 4. Offene Punkte / Nächste Schritte

- **GitHub-Push:** Lokaler `main` ist 4+ Commits vor `origin/main`. Push erfolgt erst nach ausdrücklicher Freigabe durch den Owner.
