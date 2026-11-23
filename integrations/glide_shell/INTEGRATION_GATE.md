# Glide Shell Integration Gate – APPROVED & INTEGRATED (Glide Shell 0.6.2)

**Status: DECIDED & IMPLEMENTED (23.11.2026) · Glide `1.0.2` (Tag `v1.0.2`) · Glide-System `V1.86` · Glide Shell `0.6.2` · Commit `7dcd8dc04366f88943fa17827882cef4d81421b8` · Lizenz `MPL-2.0`**

Die technische Integration der anwendungsneutralen **Glide Shell 0.6.2** in Chess & Chains wurde durch den Projektinhaber am 23.11.2026 ausdrücklich freigegeben (`ADR-002`, `Q-006`).

## 1. Quellenvalidierung & Abweichungsmatrix (Lokal vs. Tag `v1.0.2`)

- **Offizielle GitHub-Referenz:** `n05a-design/glide-to-do`, Tag `v1.0.2` (`160201387d7440c010916fbf35a98ec39ccd3e9b`), Commit `7dcd8dc04366f88943fa17827882cef4d81421b8` (`main` zeigt auf denselben Commit).
- **Lokale Quelle:** `/Github/steps/src/Glide-Shell-Framework/V.1.0.2 glide-to-do-main` (innerhalb des übergeordneten `steps`-Repos ohne eigenes `.git`).
- **Abgleich gegen `7dcd8dc04366f88943fa17827882cef4d81421b8` (1714 Dateien):**
  - `IDENTISCH`: **1714** (davon 1706 byte-exakt, 8 nur CRLF/LF in Windows-Skripten)
  - `GEÄNDERT`: **0**
  - `FEHLT`: **0**
  - `ZUSÄTZLICH`: **0**
  - Alle 22 Shell-Dateien (`01_Repository/Glide/src/glide/glide_shell/*`), `LICENSE`, `VERSION`, `GLIDE_SYSTEM_VERSION`, `DESIGN_RICHTLINIEN.md` und `shell_uebernehmen.py` sind 100 % byte-identisch mit Tag `v1.0.2`.

## 2. Übernommenes Paket & Integrität

- **Zielpfad:** `src/glide_shell/` (unveränderte Kopie über `shell_uebernehmen.py --commit 7dcd8dc04366f88943fa17827882cef4d81421b8 --agenten-bootstrap`)
- **Integritätsanker:** [`src/glide_shell/SHELL_MANIFEST.json`](../../src/glide_shell/SHELL_MANIFEST.json) (23 Dateien mit SHA-256)
- **Einzelmodul-Register:** [`REUSE_REGISTER.csv`](REUSE_REGISTER.csv)
- **Vertragsgrenzen:**
  - `src/glide_shell/` importiert nur Standardbibliothek, `tkinter` und eigene Module (kein `chess_and_chains`, kein `glide`).
  - `chess_and_chains.chess`, `game`, `engines` und `puzzles` bleiben frei von `tkinter` und `glide_shell`.
  - Keine Übernahme von Glide-Aufgabenmodellen, `app.pyw` oder Glide-Markenassets.

## 3. Migrationsmatrix Chess & Chains → Glide Shell 0.6.2

| Chess-Komponente | Vorher | Glide-Shell-Modul | Aktuelle Integration |
|---|---|---|---|
| Start & Lebenszyklus (`ui/app.py`) | Direktes `tk.Tk()` in `launch()` | `app_host` | `create_app_host` & `launch` nutzen `AppHost` (`before_tk`, `preflight`, `bind_shortcuts`, `primary_shortcuts`, `attach_menubar`, `install_close`) |
| Timer & Polling (`ui/app.py`, `EngineDialog`) | Rohes `root.after` / `window.after` | `window_lifetime`, `motion` | `AfterScope` (`self.scope`) auf Hauptfenster und `EngineDialog`; `motion.Transitions` innerhalb `self.scope` |
| Modale Dialoge (`dialogs.py`, `replay.py`, `text_board.py`, `app.py`) | Eigene `grab_set` / `wait_window` / Fokus-Logik | `modal_session` | `create_dialog`, `ensure_min_width`, `bring_to_front`, `wait_modal`, `remember_focus`, `return_focus` |
| Menüs & Zwischenablage (`ui/app.py`, `dialogs.py`) | Manuelles Clipboard, keine Menüleiste | `desktop_adapter`, `action_picker` | `build_menu_tree`, `copy_to_clipboard`, `available_menu_actions` via `action_picker` |
| Fenstergeometrie (`ui/app.py`, `storage/settings.py`) | Fester String `"1180x820"` | `window_geometry` | `parse`, `clamp`, `format_geometry` mit Mindestmaß `860x700`; Settings-Schema validiert `window_geometry` |
| Theme & Erscheinungsbild (`ui/theme.py`, `ui/app.py`) | Statische Light-Konstanten | `system_appearance`, `custom_controls` | `ThemePalette` für `light` / `dark` / `system` (`resolve_theme`), WCAG 2.2 AA Kontrast, `set_font_provider` / `set_ink_provider` |
| Fehlertext-Kürzung (`ui/dialogs.py`) | Manuelles Slicing | `text_fit` | `text_fit.clip(..., ellipsis="…")` |
| Datenpfade (`storage/paths.py`) | Eigene Plattformabfrage | `runtime_paths` | `platform_data_dir` & `resolve_base` unter Beibehaltung von `CHESS_AND_CHAINS_DATA_DIR` |
| Undo/Redo (`ui/app.py`, `game/controller.py`) | `GameController.undo/redo` | `command_history`, `redo_history` | `GameController` bleibt alleinige Schach-Zustandsquelle; `self.ui_history = CommandHistory(limit=50)` für UI-Aktionen |
