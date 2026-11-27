# Changelog

## Unveröffentlicht – Sitzung, Uhr, Analyse und Training (2026-11-27)

- Lokale Partien samt Undo/Redo und konfigurierbarer Fischer-Uhr automatisch sichern und fortsetzen. Beweisbare Ergebnisse nach Zeitablauf automatisch werten.
- Konfigurierte UCI-Engines prüfen und Stellungen oder Bibliothekspartien analysieren.
- Validierte Trainingsstellungen aus der Analyse speichern und fällige Puzzle-Wiederholungen anzeigen.
- SQLite-Schema v5 speichert vollständige Bibliotheksanalysen und die fortsetzbare Matt-Trainingskette. Die Rücksicherung prüft Berichte, Sitzungen und Fortschritt.
- Streaming für lokale Rätselpakete und automatische CI-Zuordnung einschließlich Figurensatztests ergänzen.

[Funktionsumfang und Prüfnachweise](docs/roadmap/FUNCTIONAL_CORE.md)

## Unveröffentlicht – Logo-Integration der drei Inhaber-Master (2026-11-26)

Aktiv sind die Master **V.2** des Inhabers (26.11.2026); V.1 (25.11.2026) liegt in `design/01_Logo/Archiv/Chess-&-Chains_V.1_2026-11-25/`. Keine Versionserhöhung. Vertrag: [`design/01_Logo/README.md`](design/01_Logo/README.md) · Bericht: [`docs/reports/2026-11-26_logo-integration.md`](docs/reports/2026-11-26_logo-integration.md).

- **Logo 01 (In-App-Signet):** ersetzt das orthogonale Connected-System-Signet in Kopfzeile und Themenfarben-Vorschau des Einstellungsdialogs. Beide Kettenglieder in der Themenrolle `view_title`, Trennbänder als transparente Aussparungen, Höhe = Versalhöhe Titel bis Grundlinie Unterzeile.
- **Logo 02 (Markenemblem):** vollfarbig im Info-Dialog.
- **Logo 03 (App-Symbol):** Fenster, Dialoge, Taskleiste/Alt-Tab (ICO), macOS-Dock und `.app`-Bundle (ICNS), README-Kopf, Social Preview, Favicon-Satz, Linux-`.desktop`-Vorlage.
- **`ui/brand_raster.py`:** Standardbibliotheks-SVG-Rasterer für die Master (Matrix-Transformationen, kubische Pfade, `evenodd`, Konturen, Erase), mit Sicherheitsprüfung; ersetzt den alten M/Q/V/H-Linienparser und die Pillow-Abhängigkeit des Dock-Icons.
- **`scripts/build_brand_assets.py`:** erzeugt 41 Ressourcen und das Herkunftsmanifest; `--check` vergleicht Pixel und läuft in der CI.
- **README.md / README.de.md:** zentrierter Markenkopf mit Logo 03, Claim, Badges, Navigation und echten Screenshots.
- **Tests:** `tests/test_brand_assets.py` (27 Tests inkl. Negativfälle), GUI-Test für Logo-Rollen über alle Themes und Themenfarben.
- **Asset-Register:** 5 Logo-Zeilen aktualisiert, 25 ergänzt (inkl. Archiv V.1). Figurensätze, Figurentests und Schachlogik unverändert.

## V.0.3.0 – Drei-Figurenset-Registry (Original V.03 / Draufsicht V.04 / Klassisch V.05) (2026-11-25)

### P0 – Figurenset-Registry (`ui/pieces.py`)
- **`PieceSetInfo`-Dataclass**: Stabile interne ID, Asset-Version, deutsche/englische Bezeichnung, Asset-Pfad, Perspektive, Herkunftsreferenz.
- **Drei eingetragene Sets**: `original` (V.03, Vorderansicht), `top` (V.04, Draufsicht), `classic` (V.05, Vorderansicht / klassische Silhouetten).
- **`get_piece_set(id)` / `list_piece_sets()`**: Zentrales Lookup; unbekannte IDs fallen sicher auf `original` zurück.
- **`OwnerSvgPieces`**: Akzeptiert `piece_set`-Kwarg neben dem bisherigen `top_view`-Argument; exposes `.piece_set` Property und `.set_piece_set()`.
- **V.03 als Standardfigurenset** für Neuinstallationen; `DEFAULT_PIECE_SET = "original"`.

### P0 – SVG-Asset-Aufbereitung & Ablagestruktur
- **36 Einzel-SVGs** (12 Figuren × 3 Sets) in `src/chess_and_chains/ui/piece_assets/original/`, `.../top/`, `.../classic/`.
- **Einheitliche 128×128-ViewBox** innerhalb jedes Sets; transparenter Hintergrund; optisch konsistente Ausrichtung.
- **PNG-Fallback-Atlas** für jeden Satz (`fallback.png`) mit `scripts/build_piece_fallback.py`.
- **Masters-Ablage** in `assets/chess_pieces/masters/V.03/`, `V.04/`, `V.05/` und Archiv in `assets/chess_pieces/archive/V.02/`.
- **`PROVENANCE.md`** pro Satz mit SHA-256-Hashes, Asset-Version, Lizenzstatus (Connected-System-Originalwerk des Inhabers / Tim von Trostorff).
- **`docs/design/ASSET_REGISTER.csv`**: SHA-256 aller 24 SVGs (12 `original` + 12 `top`) und beider Fallback-PNGs aktualisiert; `classic`-Einträge ergänzt.

### P1 – Rendering-Integration
- **`board.py`**: `piece_set` / `piece_view`-Properties; `set_piece_set()` / `set_piece_view()` (rückwärtskompatible Hülle).
- **`marble_board.py`**: `piece_set`-Property; `set_piece_set()`; Renderer-Cache nach `set_id` statt `PieceView`-Literal.
- **`captured_material.py`**: `set_piece_renderer()` / `set_piece_set()` (löscht Bildcache bei Wechsel).

### P1 – App-Integration (`ui/app.py`)
- **`set_piece_set(piece_set, persist=True)`**: Schaltet Brett + beide Materialleisten gleichzeitig um.
- **`set_piece_view()` delegiert** zu `set_piece_set()` (Abwärtskompatibilität).
- **`_cycle_piece_set()`**: Zyklus original → top → classic → original; Tastaturkürzel erhalten.
- **Menü**: „Piece View"-Untermenü durch „Piece Set"-Untermenü (original / top / classic) ersetzt.
- **`_cycle_board_design()` / `_cycle_board_perspective()`** wiederhergestellt (waren versehentlich verloren gegangen).
- **`apply_appearance`** akzeptiert `piece_set`-Kwarg (hat Vorrang vor `piece_view`).

### P1 – Einstellungsdialog (`ui/appearance_dialog.py`)
- **„Figurenset"-Dropdown**: Ersetzt „Perspektive" für die Figurenauswahl; original / top / classic.
- **Live-Vorschau** der sechs weißen Figuren auf abwechselnden Feldern mit dem gewählten Satz.
- **`_snapshot()`** enthält `piece_set`; `_on_piece_set_change()` synchronisiert `piece_view_var`.

### P1 – Einstellungen & Migration (`storage/settings.py`)
- **`Settings.piece_set`-Feld** (Standard `"original"`); `PIECE_SET_CHOICES`, `DEFAULT_PIECE_SET`.
- **Migration**: Liest `piece_view == "top"` aus alten JSON-Dateien und erzeugt daraus `piece_set = "top"`.

### P1 – CLI (`__main__.py`)
- **`--piece-set original|top|classic`**: Neues Argument; Reihenfolge: `--piece-set` hat Vorrang vor `--piece-view`.
- **`--piece-view front|top`** bleibt für Abwärtskompatibilität erhalten.

### P1 – Lokalisierung (`i18n/catalog.py`)
- Neue Keys: `board.piece_set.label`, `board.piece_set.original`, `board.piece_set.top`, `board.piece_set.classic` in DE und EN.

### P2 – Testsuite
- **`tests/test_piece_sets.py`** (11 Tests): Registry-Metadaten, `get_piece_set`-Fallbacks, SVG-Vertragskonformität, Fallback-PNG-Existenz, Provenance-Dateien, Settings-Validierung, Legacy-Migration, CLI-Argumente, GameController-Invarianz.
- Bestehende Tests in `test_app_integration.py` an V.03-Bounds angepasst (nicht mehr uniform; per-Figur-Bounds gemessen).
- **`scripts/generate_piece_proof_sheets.py`**: Generiert SVG- und PNG-Korrekturabzüge für alle drei Sets.
- **Ergebnis: 347/347 Tests bestanden.**

---

## V.0.3.0 – Full Glide v1.0.2 Design Language, Post-Audit Bugfixes & Appearance Customization (2026-11-24)

### P0 – Marmorbrett-Kompatibilität & SVG-Fallback (`ui/board_artwork.py`)
- **Laufzeit-SVG-Erkennung (`_probe_svg_support`)**: Prüft einmalig pro Interpreter, ob `tk.PhotoImage` das Format `svg` nativ unterstützt (Tk 9 / Tk 8.6 mit NanoSVG).
- **Vollständiger Raster-Fallback (`_checkerboard_fallback`)**: Bei fehlender SVG-Unterstützung (vanilla Tk 8.6 unter Linux/Windows) wird ein dynamisch getöntes Schachbrett in Marmor-Grundfarben (`#D4CAB8` / `#8C7B6A`) mit korrekter Themenfarben-Mischung erzeugt.
- **Fehlerbehandlung & Zustandserhalt**: Bei Fehlern bleibt der letzte gültige Bildzustand im Cache erhalten (`test_previous_state_preserved_on_render_error`). Keine externen Abhängigkeiten (kein CairoSVG).
- **Behebt CI-Fehler**: `_tkinter.TclError: image format "svg" is not supported` unter Linux py3.11/py3.14 und Windows py3.11.

### P1 – Einstellungsdialog Transaktionssicherheit & Persistenz-Trennung (`ui/appearance_dialog.py`, `ui/app.py`)
- **Strikte Trennung von Vorschau und Speicherung**: Live-Vorschau ruft `apply_appearance(..., persist=False)` auf und verändert ausschließlich den In-Memory-Laufzeitzustand. Einstellungen werden nicht auf die Festplatte geschrieben.
- **Garantiertes Speichern bei unverändertem Laufzeitzustand**: Beim Klick auf „Übernehmen“ / `_save_and_close()` wird `persist=True` erzwungen, sodass auch dann auf Festplatte gespeichert wird, wenn die Werte durch die Vorschau bereits dem Laufzeitzustand entsprechen.
- **Verlustfreier Abbruch (`_cancel`)**: Stellt den ursprünglichen Zustand (`_initial_snapshot`) über `_emit_preview` mit `persist=False` wieder her, ohne die Einstellungsdatei auf Festplatte zu modifizieren.
- **SHA-256-Dateisystem-Regressionstest**: `SettingsTransactionSafetyTests` in `tests/test_regression_audit.py` belegt per Hash, dass die Datei vor und während der Vorschau sowie nach Abbruch bytegenau identisch bleibt und erst nach „Übernehmen“ persistiert wird.

### P1 – Theme-Parameterkorrektur & Perspektiven-Entkopplung (`ui/appearance_dialog.py`)
- **Theme-Parameter**: Aufruf von `resolve_theme()` in `_apply_live_preview()` korrigiert (Hintergrundauswahl wird als Schlüsselwortargument `background=...` übergeben, nicht fälschlich als Positionsargument `root`).
- **Perspektiven-Entkopplung**: Perspektiven-Dropdown wird für alle Nicht-Marmor-Brettdesigns (inkl. benutzerdefinierte SVG-Bretter) deaktiviert und auf 2D arretiert. Ein benutzerdefiniertes SVG-Brett kann nicht versehentlich durch Perspektivenwahl zum Marmorbrett werden.

### P2 – Einstellungen gestalterisch nachgebessert (`ui/appearance_dialog.py`, `ui/dropdown.py`)
- **Abschlussbuttons rechtsbündig**: „Abbrechen“ und „Übernehmen“ sind gemeinsam unten rechts nebeneinander im Footer platziert (`column=1` und `column=2`, `column=0` als Abstandhalter).
- **GlideDropdown Lesbarkeit & Textmessung**: Pauschale 24-Zeichen-Kürzung (`clip_button_text`) durch pixelgenaue Textmessung (`_fit_text`) ersetzt. Dropdown-Popup passt seine Mindestbreite responsiv an die längste Option an.
- **Bildschirmbegrenzung für Popups**: Horizontale (`screen_w`) und vertikale (`screen_h`) Bildschirmbegrenzung verhindert das Hineinragen in oder Hinausragen aus dem Bildschirmrand.
- **Glide Shell Lifecycle-Vertrag**: Timer und Fokusprüfungen in `GlideDropdown` nutzen `glide_shell.window_lifetime.AfterScope` und werden bei Widget-Abbau sauber beendet.
- **Vollständige Lokalisierung**: Alle Dropdowns, Sektionsüberschriften und Abschlussbuttons sind vollständig DE/EN-lokalisiert.

### P2 – Materialanzeige-Kontrast & Rätselwechsel (`ui/captured_material.py`, `ui/app.py`)
- **WCAG 2.2 AA Kontrast ≥ 4,5:1**: Die `+N`-Vorteilskapsel verwendet `tab_idle` als Hintergrund und wählt automatisch eine Vordergrundfarbe mit mindestens 4,5:1 Kontrast über alle 10 Glide-Themes.
- **Rätsel-Reset**: Bei leerer Rätselauswahl (`self.puzzle is None`) werden die Materialanzeigen zuverlässig auf `None` zurückgesetzt.

### P1 – CI-Testabdeckung vervollständigt (`.github/workflows/checks.yml`)
- Fehlende Testmodule integriert: `tests.test_captured_material`, `tests.test_final_audit`, `tests.test_glide_shell_integration`, `tests.test_regression_audit`.
- Glide-Shell-Selbsttest (`python -m glide_shell.selftest`) und Manifestprüfung in GUI-Jobs integriert.
- Timeout für `gui-native` auf 5 Minuten erhöht, um Runner-Lastspitzen auf macOS abzufangen.

## V.0.3.0 – Full Glide v1.0.2 Design Language, Rounded Canvas Cards & Appearance Customization (2026-11-24)

### Design & Tokens
- **`ui/theme.py` updated to Glide v1.0.2 / Glide Shell 0.6.2 neutral design tokens**: removed pre-Glide yellow-white/parchment defaults (`#FAF6EC`, `#EFE8D8`, `#FFFCF4`, `#F4C400`) from UI palettes and `docs/design/brand-tokens.json`; primary accent is Cobalt blue (`#086FD6` light / `#2C95FF` dark), keeping `#9E4AC8` excluded.
- **All 10 Glide themes + `system` + `w06-provisional` alias**: `light`, `dark`, `glass-light`, `glass-dark`, `dopamine`, `pixel`, `contrast-light`, `contrast-dark`, `minimal-light`, `minimal-dark`, each verified at >= 4.5:1 WCAG 2.2 AA contrast.
- **Full customization API**: 8 `ACCENT_CHOICES`, 10 `BACKGROUND_CHOICES` (`with_accent`, `with_background`, `customize_palette`), 4 `RADIUS_CHOICES` (`18`, `12`, `6`, `0` px), 3 `FONT_SCALE_CHOICES` (`0.9`, `1.0`, `1.15`), and 3 `FONT_WEIGHT_CHOICES` (`auto`, `standard`, `bold`), plus `animations_enabled` and `hints_visible` persisted in `settings.py` and localized in `i18n/catalog.py` (DE/EN).

### Canvas Components & UI Widgets
- **`RoundedSurfaceCard` (`ui/theme.py`)**: rounded Canvas surfaces with `fill_color`, `outline_color`, dynamic `radius`, and `bg_color` matching the parent window/paper for `header_card`, `_side_slot`, `_board_slot`, `_rail_slot`, and `atlas_section` (replacing rectangular `_sheet_pair` frames).
- **`RoundedButton` (`ui/theme.py`)**: seamless `carrier_bg` Canvas corner blending, `button_colors`, natural auto-height, and stretched/un-stretched modes across sidebar action buttons, header buttons, and `TabRail` tabs (with `takefocus=False` on header buttons and focus handoff preserved on `TabRail`).
- **`AppearanceDialog` (`ui/appearance_dialog.py`)**: modal customization dialog (`Cmd/Ctrl+,`, header button, View menu) with live `RoundedSurfaceCard`/`RoundedButton` preview calling `ChessApp.apply_appearance()`.
- **Full component theming**: `board.py`, `marble_board.py`, `atlas.py`, `dialogs.py`, `replay.py`, and `text_board.py` adopt `ThemePalette`; `ReplayDialog` and `TextBoardDialog` adopt `ThemedAutoScrollbar`.

- **Borderless Monochrome In-App Header Logo (`ui/branding.py`, `ui/app.py`, `ui/theme.py`)**: replaced the framed multi-color square `tk.Button` in the header with `HeaderLogoCanvas` (`tk.Canvas`), rendering the cropped inked bounding box (`signet_bounding_box`) of `signet.svg` transparently in the WCAG-verified active theme accent color (`theme.view_title`, via `legible_accent()`) with pure-Python transparent RGBA PNG fallback (`render_signet_rgba_png`), aligned optically to cap-top and subtitle baseline across font scales while keeping original master SVGs and OS icons intact.
- **Uniform 12 px Glide Card Spacing & Standalone Startup**: enforced constant `PANEL_GAP = 12 px` across all panels and unified Glide Settings (`AppearanceDialog` + `start_chess_and_chains.py` / `build_app.py`).
- **Orthogonal Board Design, Perspective & Piece View Decoupling (`ui/board_artwork.py`, `ui/marble_board.py`, `ui/app.py`, `storage/settings.py`)**: decoupled `board_design` (`standard`, `marble`, `custom`), `perspective` (`2d` bird's-eye / `3d` spatial), `piece_view` (`front`, `top`), and `orientation` (`white`, `black`). Added `Marble2DArtwork` rendering the orthogonal 8×8 marble field grid (`board_2d.svg` derived from `Brett.svg`) in 2D bird's-eye view without perspective distortion or game state resets.
- **„Themenfarbe“ / „Theme color“ & Dynamic Chessboard Color Inheritance (`i18n/catalog.py`, `ui/theme.py`, `ui/appearance_dialog.py`)**: renamed user-facing labels from „Akzentfarbe“ to „Themenfarbe“ / „Theme color“ (preserving backwards-compatible `accent_choice` JSON keys), implemented `derive_board_colors()` deriving graduated `square_light`, `square_dark`, `last_move`, `legal_mark`, and `atlas_line` tokens across all 10 Glide themes × 8 theme colors plus subtle marble stone tinting while leaving custom SVG boards untouched.
- **Exact Board & Move Marker Centering (`ui/board.py`, `ui/marble_board.py`)**: snapped 2D square bounds to integer coordinates (`square_bounds`, `square_center`), eliminated sub-pixel/asymmetric Tk oval rounding drift across all concentric move circles, capture rings, selection/focus/hint/check indicators, and projected 3D normal/capture rings via `projected_square_center()` and `_projected_circle_points()`.
- **Dark-Mode Dialog & Promotion Rendering Fix (`ui/app.py`, `ui/theme.py`, `ui/dialogs.py`, `ui/replay.py`, `ui/text_board.py`, `ui/appearance_dialog.py`)**: fixed illegible white-on-light promotion buttons in Dark Mode by replacing native `tk.Button` (whose macOS Aqua bezel ignored custom dark `background` colors) with uniformly sized Glide `RoundedButton` cards honoring `ThemePalette`, `font_spec`, `radius`, keyboard navigation, and `modal_session` focus restoration; switched `install_ttk_theme()` to `clam` so `PositionDialog`, `ReplayDialog`, `TextBoardDialog`, and `_choose_item` dialogs honor Dark Mode contrast (`>= 4.5:1`), and fixed invalid `focus=` kwargs on `modal_session.run_modal` calls.
- **Shortened Labels, Unclipped Header & Single-Line Play Buttons (`i18n/catalog.py`, `ui/app.py`, `ui/theme.py`)**: shortened `"button.claim_draw"` (`"Remis"` / `"Draw"`) and `"button.retry_bot"` (`"Bot erneut"` / `"Retry bot"`), removed header button ellipsis truncation (`"Leiste ausblenden"` / `"Schmale Leiste"`) with Glide hover tooltips, widened default sidebar (`SIDEBAR_WIDTH = 352`) and updated play-panel full-label width measurement so all play/bot buttons render single-line with uniform heights at standard size and stack responsively into one column at larger font scales.
- **Dynamic Captured Pieces & Material Advantage Display (`chess/material.py`, `ui/captured_material.py`, `ui/app.py`, `ui/replay.py`, `i18n/catalog.py`)**: pure Tk-free domain calculation (`calculate_captured_material`) computing captured pieces and material differences (Pawn 1, Knight 3, Bishop 3, Rook 5, Queen 9) directly from game move history, with full support for en passant, quiet/capture promotions, captures of promoted pieces, undo/redo, PGN import, and uninvented FEN history. Built `CapturedMaterialBar` displaying authentic SVG miniatures grouped with multipliers (e.g. `×2`, `×4`), clear side indicators, and active Themenfarbe `+N` advantage pills (shown only for the leader; omitted on tie) with informative tooltips; integrated two bars above/below the board that swap on orientation flips (`white` / `black`) in live play, puzzles, and `ReplayDialog`.

### Verification
- **Full test suite**: `PYTHONPATH=src python3 -m unittest discover -s tests -q` passing (including WCAG contrast checks across all 10 Glide themes and 8 Themenfarben, `test_30` panel spacing/Settings parity/standalone launchers, `test_31` monochrome header logo, `test_32` decoupled board/perspective/piece-view state preservation, `test_33` Themenfarbe rename & board square contrast >= 3.0, `test_34` Dark Mode promotion dialog across White/Black quiet & capture promotions and all 4 pieces, `test_35` Dark Mode dialog theme inheritance + single-line/responsive play controls, and `BoardMarkerCenteringTests` across all 64 squares in 2D/3D).
- **Governance & Policy checks**: `scripts/verify_starter.py`, `scripts/check_policy.py`, and `scripts/verify_document_links.py` passing.

## V.0.2.0 – Full Glide Design Language (ttk Styles, Tokens, Dark/Light) (2026-11-24)

(Former V.0.3.0 content — see above for the definitive V.0.3.0 changelog.)



- **`install_ttk_theme(root, palette)`** in `theme.py`: configures all `ttk` widget styles
  (`TButton`, `TEntry`, `TLabel`, `TFrame`, `TCheckbutton`, `TRadiobutton`, `TScrollbar`,
  `TSeparator`, `TCombobox`) with Glide design tokens — called on startup and on every theme switch.
- **`apply_optionmenu_theme(widget, palette)`**: applies Glide palette to `tk.OptionMenu` and its
  dropdown, used for the bot-level selector.
- **`apply_listbox_theme(widget, palette)`**: applies Glide palette (paper background, semantic
  selection colors, flat border, Glide font) to `tk.Listbox` widgets — used for the move-list panel.
- **`RADII`** spacing tokens now explicitly imported in `app.py`; `SPACING` tokens consistently
  applied to all widget padding/margins.
- **Button styles**: `Glide.TButton` (neutral) and `Glide.New.TButton` (primary/chrome yellow)
  applied to all `ttk.Button` instances in `dialogs.py`, `replay.py`, `text_board.py`.
- **`Glide.TEntry`**: applied to FEN entry in `PositionDialog` with flat border, field background,
  and Glide-aligned focus highlight.
- **`move_list` scrollbar**: migrated from plain `tk.Scrollbar` to `ttk.Scrollbar` for consistent
  Glide styling across all scroll areas.
- **Replay & TextBoard dialogs**: Glide listbox defaults applied via `_style_listbox_from_ttk()`;
  `Glide.TButton`/`Glide.New.TButton` styles used throughout.
- **Dark/Light mode**: all six palettes (`light`, `dark`, `contrast-light`, `contrast-dark`,
  `minimal-light`, `minimal-dark`) correctly propagate through `install_ttk_theme` on `apply_theme`.
- **Test suite**: 275/275 passing (exit 0), zero regressions.

## V.0.1.0 – Glide Shell 0.6.2 Framework Integration & 2-Pane Responsive UI (2026-11-24)

- Migrate entire desktop runtime onto **Glide Shell 0.6.2** (`AppHost`, `window_lifetime.AfterScope`, `modal_session`, `motion.Transitions`, `desktop_adapter`, `action_picker`, `system_appearance`, `window_geometry`, `runtime_paths`, `text_fit`).
- Implement Glide-aligned **2-Pane Layout**: navigation/controls sidebar on the left (`column=0`, minsize=328) with a 64-px narrow symbol rail (`SIDEBAR_RAIL_WIDTH = 64`) and complete hide/show toggle; right board workspace (`column=1`) dynamically expands to 100% width.
- Implement **Compact Mode** (`COMPACT_MIN = (480, 560)`) with separate geometry persistence (`compact_window`) and automatic geometry restoration, without exiting on Escape.
- Implement responsive **Header Density & Height Density Breakpoints** (Width: `>= 1120` full, `900..1119` compact with overflow menu `⋯`, `< 900` minimal; Height: `>= 850` / `780..849` / `< 780`; auto-narrow rail `< 760`).
- Incorporate **Glide Design Guidelines & Themes**: 6 WCAG 2.2 AA (`>= 4.5:1`) palettes (`light`, `dark`, `contrast-light`, `contrast-dark`, `minimal-light`, `minimal-dark`, `system`), Okabe-Ito CVD-safe palette, interactive button hover feedback (`theme.hover`), 24-char button label clipping (`clip_button_text`), and aligned menu checkmarks (`action_picker.check_label`).
- Implement interactive in-app header logo (Connected System signet) opening the accessible `AboutDialog` modal session.

## V.0.0.1 – Development snapshot (2026-11-23)

- Integrate **Glide Shell 0.6.2** from Glide `1.0.2` (`v1.0.2`, commit `7dcd8dc04366f88943fa17827882cef4d81421b8`, MPL-2.0) into `src/glide_shell/` with `SHELL_MANIFEST.json`, packaging support in `pyproject.toml`, and 13/13 selftest verification.
- Migrate `ChessApp` startup, menu bar, keyboard shortcuts, and macOS quit handling to `AppHost` and `desktop_adapter`; migrate timers to `window_lifetime.AfterScope` and `motion.Transitions`; migrate modal dialogs (`PositionDialog`, `ReplayDialog`, `TextBoardDialog`, `EngineDialog`, promotion, and item chooser) to `modal_session`.
- Integrate Connected System Light/Dark/System theme resolution (`system_appearance`, WCAG 2.2 AA contrast), `window_geometry` clamping/validation, `runtime_paths` storage resolution, portable design contract (`docs/design/GLIDE_DESIGN_CONTRACT.md`), and multi-agent skills (`.agents/skills/`, `.claude/skills/`).
- Establish `0.0.1` as the package version and `V.0.0.1` as the display label. The CLI and window title expose the same version as the package metadata. Foundation CI checks the manifest and current documentation.
- Integrate Connected System branding and the optically balanced V.02 front-view pieces with stronger shading for dark pieces. Keep the separate top-view set, editable SVG masters, offline PNG fallbacks, and the Tk 9 session preview for custom SVG boards.
- Test configured local UCI engines through `readyok`, show the advertised name and option count, and clean up the process and the Tk poll independently.
- Stabilize Tk test cleanup and enable crash diagnostics. Branch, PR and post-merge CI for PR #7 passed on Windows, macOS and Linux.
- Reconcile the current documentation with the code, archive prior planning snapshots, and record the next tasks and owner decisions. This is a development version.
- Show keyboard focus when entering the board, localize square and selection feedback, and support Enter on action buttons, including promotion choices.
- Clear the board focus message when keyboard focus leaves the board. Preserve newer action feedback and reject package acceptance records with unresolved blockers.
- End live games automatically when every legal reply is a capture leading to insufficient material. Preserve the recorded moves in older games and supplied puzzle lines.
- Recognize dead positions reached by short forced continuations into stalemate or insufficient material.
- Validate saved games on a temporary copy of an SQLite backup before replacing the active library.
- Show the preserved filename when the app creates a new library after database corruption. Verify repository asset paths and recorded hashes in the Foundation check.
- Show localized demo puzzle themes in the filter and puzzle details. Keep custom theme identifiers visible and preserve the original identifiers used for filtering.
- Add optional quality thresholds and rejection reasons to the offline puzzle builder. Record the origin of each puzzle and correct the source metadata of the bundled demo pack.
- Add an optional seed for repeatable selection from a fully validated puzzle source. Report the source checksum and the number of selected puzzles.
- Keep valid CSV records around malformed UTF-8 bytes and verify the checksums of the archived OneDrive snapshots in Foundation CI.
- Support Enter on library and draw-claim dialog buttons and restore the previous keyboard focus when the chooser closes.
- Reuse SVG board backgrounds for both orientations at the current size and reuse rendered tiles when changing perspective.
- Import verified local puzzle packs from the Puzzle Lab. Keep progress by pack and restore the last selected pack on restart.
- Accept platform aliases above the local puzzle-pack library and reject redirected library and pack directories.
- Exchange the current position via FEN text or a local `.fen` file and start a two-player game from a validated position.
- Browse occupied squares and legal destinations in a text board, with keyboard play for games, promotions and puzzles.
- Find saved games by player, event, result or game number. Keep the selected game consistent when opening or exporting a filtered result.
- Recognize closed pawn barriers as dead positions when neither king can open the barrier or reach the other king.
- Audit the local storage and documentation: restructure the roadmap with decision levers and proposed milestones, add next steps per work package and the MVP fulfilment status, index all reports, archive the F0 start guide, and add GitHub issue and pull request templates.
- Fix the asset register path check on macOS, where temporary directories resolve through `/private`, and run the Foundation tests on every platform in CI.
- Filter puzzles by unsolved or attempted without a clean solve. Show the latest attempt and best solve time from local history.
- Replay current or saved games on a separate board. Browse individual plies while keeping the active game and stored record intact.
- Restart the current puzzle and reveal the source piece and target square in two stages. Wrap the piece label at high text scaling.
- Add PGN import and FEN exchange to the local 3D marble board.
- Replay the 3D marble position history with a keyboard-adjustable timeline and return to the live game.
- Switch between the normal board and the projected 3D marble board inside Tk while preserving the live game and move history.
- Stack play actions when large text needs more room so the labels and focused controls remain visible in compact windows.

The dated entries below preserve the development history incorporated into this snapshot.

## Unreleased – Saved game endings and history (2026-11-20)

- Keep local resignation and draw-claim details when reopening a game. SQLite v3 migrates existing libraries after creating a backup.
- Fix saving games that ended before the first move.
- Store individual history entries for undo and redo instead of copying the entire move list and repetition table.
- Keep the play controls reachable in small windows with vertical scrolling and automatic focus visibility.

## Unreleased – PGN exchange and puzzle filters (2026-11-20)

- Import and export a single UTF-8 PGN game from the local library. Bound input size and move count and replace export files atomically.
- Filter Puzzle Lab by theme and rating and show saved solves in the current selection.
- Score resignation against a lone king as a draw, preserving the outcome through undo and redo.

## Unreleased – N02 follow-up (2026-11-20)

- Added draw claims in the Tk app for the current position and for a declared legal move.
- Reset the UCI engine once per game and skip cancelled searches before they can reach the engine.
- Reopen stored games and recorded PGN results in the local two-player interface.
- Validate and, if needed, migrate a backup before restoring it. Preserve the active database on invalid input.
- Reject normalized duplicate puzzle IDs and validate loaded packs beyond their checksum.
- Added external Perft fixtures and a Tk underpromotion regression. Run native Tk CI on Python 3.11 and 3.14.

## Unreleased – N02 Functional Core (2026-11-20, merged in PR #2)

- Evidence-based work-package status model; F0 baseline preserved.
- Chess core: structural SAN parser (PGN import ~14× faster), PGN result
  consistency checks, promotion without `=`, new golden/perft/property tests.
- Game controller with asynchronous bot worker, stale-result protection and
  engine fault handling; project-owned mock UCI engine (not a chess AI).
- Six data-driven bot presets with handshake-based option negotiation.
- Puzzle Lab: streaming Lichess CSV importer (Rating ≥ 1000), versioned
  packs, solving sessions, five project-authored demo puzzles.
- Local storage: platform data paths, SQLite migrations, backup/restore,
  corruption quarantine, atomic JSON settings.
- Tk app: bot modes, levels, engine settings dialog, puzzle tab, save game,
  copy PGN, shortcuts, DE/EN UI, exchangeable piece renderer, SVG contract.
- CI split into foundation/docs, policy, headless OS×Python matrix, GUI jobs.

## Unreleased – Foundation F0 (2026-11-19)

- Initial repository starter, product brief, licensing decision gate and prompt work orders.
- Source scaffolding and standard-library-based validation scripts.
- No chess UI, engine, puzzles or public installers implemented.
