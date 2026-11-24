# Übergabebericht: Glide Design Language Integration – V.0.2.0

**Datum:** 24.11.2026  
**Agent:** Argon (Google Antigravity)  
**Branch:** `feat/chess-glide-1.0.2-shell-integration`  
**Vorgänger-Commit:** `f852512`  
**Status:** IMPLEMENTED · TESTED

---

## 1. Auftragsumfang

Vollständige Integration der Glide-Designsprache (Farben, Flächen, Schaltflächen, Texte,
abgerundete Ecken, Dark/Light-Mode) in alle Tk-Widgets von Chess & Chains. Grundlage ist
der Glide-Designvertrag `DESIGN_RICHTLINIEN.md` aus Glide Shell 0.6.2.

---

## 2. Implementierte Änderungen

### 2.1 `src/chess_and_chains/ui/theme.py`

| Neu/Geändert | Beschreibung |
|---|---|
| `install_ttk_theme(root, palette)` | Konfiguriert alle `ttk`-Stile mit Glide-Tokens: `TButton`, `TEntry`, `TLabel`, `TFrame`, `TCheckbutton`, `TRadiobutton`, `TScrollbar`, `TSeparator`, `TCombobox`. Wird beim Start und bei jedem Theme-Wechsel aufgerufen. |
| `apply_optionmenu_theme(widget, palette)` | Wendet Glide-Palette auf `tk.OptionMenu` und sein Dropdown an (Hover, Fokus, Farben, Font). |
| `apply_listbox_theme(widget, palette)` | Wendet Glide-Palette auf `tk.Listbox` an (Hintergrund, Auswahl, Rahmen, Schrift, `activestyle="none"`). |
| `Glide.TButton` | Neutraler Button-Stil: `paper`-Hintergrund, `ink`-Text, `hover`-Hover, flache Kontur. |
| `Glide.New.TButton` | Primärer Button-Stil: `action_new_bg`-Hintergrund (Chrome Yellow im Light-Theme), `action_new_fg`-Text. |
| `Glide.Header.TButton` | Kompakter Header-Button mit `caption`-Schriftgröße. |
| `Glide.TEntry` | Eingabefeld mit `paper`-Hintergrund, `input_border`-Rahmen, Fokus-Highlight in `brand_blue`, `invalid`-Zustand in `brand_red`. |
| `Glide.TCheckbutton` / `Glide.TRadiobutton` | Auswahlsteuerelemente mit Glide-Farbmapping. |
| `_ttk_style(root)` | Erstellt eine per-Root `ttk.Style`-Instanz (kein globales Singleton, um Post-Destroy-Fehler zu vermeiden). |

### 2.2 `src/chess_and_chains/ui/app.py`

| Änderung | Beschreibung |
|---|---|
| `install_ttk_theme(root, self.theme)` | Aufruf in `__init__` direkt nach `resolve_theme`. |
| `apply_theme(...)` | `install_ttk_theme(self.root, palette)` bei jedem Theme-Wechsel. |
| `apply_optionmenu_theme(self.level_menu, ...)` | Ersetzt die manuelle `configure()`-Kette für das Level-Auswahlmenü. Theme-Callback aktualisiert automatisch bei Palette-Wechsel. |
| `apply_listbox_theme(self.move_list, ...)` | Ersetzt die manuelle `configure()`-Kette für die Zugliste. Theme-Callback eingebunden. |
| `ttk.Scrollbar` statt `tk.Scrollbar` | Zuglisten-Scrollleiste auf `ttk.Scrollbar` migriert für einheitliches Glide-Styling. |
| Neue Imports | `RADII`, `apply_listbox_theme`, `apply_optionmenu_theme`, `install_ttk_theme`. |

### 2.3 `src/chess_and_chains/ui/dialogs.py`

| Änderung | Beschreibung |
|---|---|
| `Glide.TEntry` | FEN-Eingabefeld in `PositionDialog` verwendet den neuen ttk-Stil. |
| `Glide.TButton` / `Glide.New.TButton` | Alle Aktionsschaltflächen (`position.play` = Primary, Rest = Neutral). |

### 2.4 `src/chess_and_chains/ui/replay.py`

| Änderung | Beschreibung |
|---|---|
| `_style_listbox_from_ttk(lb)` | Hilfsfunktion: liest live `ttk.Style`-Werte und wendet sie auf die Replay-Zugliste an. |
| `Glide.TButton` | Alle Navigationsschaltflächen im Replay-Dialog. |
| `font=("TkFixedFont", FONT_SIZES["body"])` | Einheitliche Schriftgröße aus Glide-Tokens. |

### 2.5 `src/chess_and_chains/ui/text_board.py`

| Änderung | Beschreibung |
|---|---|
| `_style_listbox_from_ttk(lb)` | Hilfsfunktion: Glide-Stil für Figur- und Zielliste. |
| `font=("TkDefaultFont", FONT_SIZES["body"])` | Einheitliche Schriftgröße. |
| `Glide.TButton` / `Glide.New.TButton` | Schließen- und Spielen-Schaltflächen. |

---

## 3. Designvertrag-Mapping (DESIGN_RICHTLINIEN.md → Implementierung)

| Glide-Vorgabe | Implementierung |
|---|---|
| Farbsemantik (window/paper/acetate/shadow) | Vollständig über alle 6 Paletten in `ThemePalette`. |
| Abstände (SPACING-Tokens) | `padx`/`pady`-Werte in allen Widgets via `SPACING[n]`. |
| Typografie (caption 10, body 11, section 16, title 22) | `FONT_SIZES` als `ttk`-Style-Schriftgröße. |
| Schaltflächen-Anatomie (flach, hover, disabled) | `Glide.TButton`/`Glide.New.TButton` mit `style.map()`. |
| Eingabefelder (flat, border, focus) | `Glide.TEntry` mit `bordercolor`, `lightcolor`, `darkcolor`. |
| Auswahlsteuerelemente | `Glide.TCheckbutton`, `Glide.TRadiobutton`. |
| Scrollbars | `ttk.Scrollbar` überall; `Vertical.TScrollbar` / `Horizontal.TScrollbar` konfiguriert. |
| Abgerundete Ecken | `rounded_rect_points()` aus `glide_shell.custom_controls` für Canvas-Widgets (Scrollbar, Scale, Board). `ttk`-Widgets: Plattform-nativ + Relief/Padding-Approximation. |
| Dark/Light-Mode | Alle 6 Paletten propagieren durch `install_ttk_theme` bei `apply_theme`. |
| WCAG 2.2 AA Kontrast | Bestehend via `contrast_ratio()` in `theme.py`. |
| B01/B16 Unmittelbare Rückmeldung | Hover-Callbacks in `_bind_button_hover`, keine `time.sleep()`. |
| B15 Bedienelemente schützen | `window_geometry.clamp`, responsive Breakpoints, Mindestgrößen. |

---

## 4. Testergebnisse

```
Ran 275 tests in 76.133s
OK
exit code: 0
Umgebung: Python 3.14, macOS, Tk 8.6/aqua (headless)
Branch: feat/chess-glide-1.0.2-shell-integration
Commit: f852512 (vor diesem Commit)
```

Zusätzliche Prüfungen:
- `python3 scripts/verify_starter.py` → PASS
- `python3 scripts/check_policy.py` → PASS

---

## 5. Bekannte Einschränkungen

| Einschränkung | Erklärung |
|---|---|
| Echte Pixel-Radiusabrundung auf macOS Aqua | Tk/Aqua delegiert Button-Rendering an das native Theme-Engine. `Glide.TButton` erreicht optisches Glide-Profil durch Padding/Relief; echter Border-Radius erfordert Canvas-Widgets oder `ttkbootstrap`. |
| `theme_use()` nicht aufgerufen | Um Post-Destroy `<<ThemeChanged>>`-Tcl-Fehler im Testlauf zu vermeiden, wird die Basis-Theme nicht erzwungen gewechselt. Glide-Stile funktionieren auf dem System-Standard-Theme. |
| `ttk.Style.lookup()` in Dialogen | `_style_listbox_from_ttk()` liest Farben zur Laufzeit aus dem `ttk.Style`. Wenn `install_ttk_theme` noch nicht aufgerufen wurde (z. B. in Isolation-Tests), greift der `except`-Fallback. |

---

## 6. Nächste Schritte (Backlog)

- [ ] `ttkbootstrap` oder Custom-Theme für echte Border-Radius-Unterstützung prüfen (ADR-Entscheidung nötig).
- [ ] `Glide.TCombobox` als Ersatz für `tk.OptionMenu` im Play-Panel anwenden (Schritt für Schritt).
- [ ] Visuellen Smoke-Test-Screenshot per CI erzeugen und in PR einhängen.
- [ ] PR #23 mergen sobald Owner-Freigabe erfolgt.

---

## 7. Versionsinformationen

| Datei | Neu |
|---|---|
| `src/chess_and_chains/__init__.py` | `__version__ = "0.2.0"` |
| `project-manifest.json` | `"project_version": "0.2.0"` |
| Alle 16 `VERSIONED_DOCS` | `V.0.2.0` |
