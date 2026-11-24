# Chess & Chains – Designvertrag (Connected System × Glide Shell)

Stand 24.11.2026 · Chess & Chains V.0.3.0 · Glide Shell 0.6.2 (Glide v1.0.2, Commit `7dcd8dc04366f88943fa17827882cef4d81421b8`)

Dieses Dokument verbindet den portablen Gestaltungs- und Interaktionsvertrag der **Glide Shell** ([`src/glide_shell/DESIGN_RICHTLINIEN.md`](../../src/glide_shell/DESIGN_RICHTLINIEN.md)) mit der Marken- und Produktidentität von **Chess & Chains** ([`CONNECTED_SYSTEM.md`](CONNECTED_SYSTEM.md)).

---

## 1. Übernommene Grundsätze der Glide Shell (P1–P6)

| Grundsatz | Bedeutung für Chess & Chains | Konkrete Umsetzung |
|---|---|---|
| **P1 Funktioniert selbstverständlich** | Systemkonventionen gelten ohne Umwege | 10 barrierefreie Themes (`light`, `dark`, `glass-light`, `glass-dark`, `dopamine`, `pixel`, `contrast-light`, `contrast-dark`, `minimal-light`, `minimal-dark`, plus `system` und Alias `w06-provisional`) über `system_appearance`; `Escape` schließt modale Dialoge; `Tab`/`Shift+Tab` navigiert zyklisch vom Brett auf den linken Reiter (`TabRail`) und zurück; Standardkürzel (`Strg`/`Cmd+Z`, `Y`, `N`, `,`) über `app_host` |
| **P2 Form folgt Funktion** | Farbe = Rolle, Größe = Wichtigkeit | `theme.ThemePalette` trennt `window`, `paper`, `acetate`, `tab_idle`, `ink`, `muted_ink`, `brand_blue`, `action_new_bg` (Primäraktion, Cobalt-Blau `#086FD6`/`#2C95FF` ohne Vor-Glide-Gelb/Weiß), `confirm`, `delete`, `line`, `input_border`, `hover`, `selection` sowie dynamische Anpassungen (`with_accent`, `with_background`, `customize_palette`) |
| **P3 Keine Funktion doppelt** | Ein führender Aktionsweg pro Absicht | Menüleiste (`desktop_adapter.build_menu_tree`) und `action_picker` lesen denselben Menübaum mit ausgerichteten Häkchen (`action_picker.check_label`); ein gemeinsamer Dialog [`AppearanceDialog`](../../src/chess_and_chains/ui/appearance_dialog.py) bündelt Design, Akzent, Hintergrund, Eckenradius, Schriftgröße, Schriftstärke und Verhalten |
| **P4 Kein Platz verschwenden** | Spielfeld dominiert die Fläche | 2-Fenster-Layout auf abgerundeten `RoundedSurfaceCard`-Flächen: Linke Seitenleiste (`column=0`, minsize=352) mit einzeiliger Spielsteuerung (bei schmalem Platz oder großer Schrift automatisch einspaltig), Schmalmodus (`_rail_slot`, 64-px-Symbolleiste) oder vollständigem Ausblenden; rechtes Brettarbeitsblatt (`_board_slot`, `column=1`, `weight=1`) spannt bei ausgeblendeter Leiste auf 100 % der Fensterbreite |
| **P5 Nur das Wesentliche** | Ruhiger Standardzustand | Klare Trennung in *Play*, *Moves* und *Puzzles*; Kompaktmodus (`480 × 560`) für paralleles Arbeiten neben anderen Fenstern mit Geometriewiederherstellung |
| **P6 Geringe Komplexität** | Stabile Begriffe und Muster | Durchgängige DE/EN-Kataloge (`i18n/catalog.py`), 24-Zeichen-Knopfbeschränkung (`clip_button_text`), einheitliche Dialogführung über `modal_session` |

---

## 2. Verbindliche Einzelvorgaben (B-Regeln)

- **B15 – Bedienelemente schützen:** Hauptfenster mindestens `860 × 700` (`NORMAL_MIN`), im Kompaktmodus mindestens `480 × 560` (`COMPACT_MIN`). Schaltflächen im Play-Panel schalten bei schmaler Breite oder hoher Schrift-Skalierung (150–200 %) automatisch von zwei auf eine Spalte um und stellen Fokussichtbarkeit per `ThemedAutoScrollbar` sicher.
- **B11 – Informationshierarchie:** Statuszeile und Brett behalten Priorität; Fehlermeldungen und Metadaten in Dialogen werden mit `text_fit.clip` / `wraplength` sauber gekürzt statt abgeschnitten. Knopfbeschriftungen sind auf 24 Zeichen begrenzt (`clip_button_text`), Titellängen auf 40 Zeichen (`TITLE_MAX_CHARS`).
- **B05 / B07 – In-App-Logo & Kopfleisten-Anatomie:** Das Connected-System-Kettensignet ([`branding.py`](../../src/chess_and_chains/ui/branding.py)) wird ohne Hintergrund, Outline oder Kachel direkt als einfarbig getöntes `HeaderLogoCanvas` (`tk.Canvas`) in der WCAG-geprüften Themen-Akzentfarbe (`theme.view_title`, abgeleitet über `legible_accent()`) auf `header_card` (`theme.paper`) gerendert — exakt zugeschnitten auf die sichtbare SVG-Fläche (`signet_bounding_box`, ohne leere ViewBox-Ränder) und optisch zwischen Versalhöhe von *Chess & Chains* (`theme.view_title`) und Grundlinie der Unterzeile (`self.subtitle_row`) ausgerichtet (inklusive About-Dialog-Funktion). Bei Tk ohne SVG-Unterstützung liefert `render_signet_rgba_png()` einen transparenten, einfarbigen PNG-Fallback; die Original-SVGs und mehrfarbigen OS-App-Icons (`brand_assets/app-icon.*`) bleiben unverändert. Rechts liegt der `⚙ Einstellungen`-Knopf (`RoundedButton`, `Cmd/Ctrl+,`).
- **D55 / D61 / D66 / D68 – Responsive Dichtestufen & Breakpoints:**
  - Breite: `≥ 1120 px` vollständige Kopfleiste mit allen Aktionen; `900..1119 px` Kompaktknöpfe mit Mehr-Aktions-Menü (`⋯`); `< 900 px` Minimalkopf (Logo ausgeblendet für linksbündigen Titel, Menü `⋯`).
  - Automatische Verschmälerung: Unterhalb von `760 px` Fensterbreite wechselt eine sichtbare Seitenleiste automatisch auf die 64-px-Symbolleiste und kehrt ab `≥ 860 px` in die volle Breite zurück.
  - Höhe: `≥ 850 px` volle Innenabstände (`12 px`); `780..849 px` kompakte Abstände (`8 px`); `< 780 px` Minimalabstände (`6 px`).
- **B01 / B16 – Unmittelbare Rückmeldung:** Keine `time.sleep`-Blockade im Tk-Thread; Engine-Berechnungen und lokale Paketimporte laufen in Hintergrund-Threads und melden über `GameController.poll()` im `window_lifetime.AfterScope`-Takt.
- **B03 – Reduzierte, unterbrechbare Bewegung:** Übergänge verwenden `motion.Transitions` (≤ 150 ms) innerhalb von `app.scope` (abschaltbar über `animations_enabled`) und enden sauber bei Fensterabbau.
- **B10 / B12 / B14 – Semantische Symbole & Hover:** Eindeutige Tastaturnavigation auf der 64-px-Leiste (`♟`, `≡`, `◈`, `＋`, `↶`, `↷`, `⇅`, `»`) mit Pfeiltasten, Eingabetaste und Leertaste. Neutrale `RoundedButton`-Flächen bieten visuelles Hover-Feedback über `theme.hover`.
- **WCAG 2.2 AA & Kontrast:** `theme.contrast_ratio` sichert mindestens **4,5:1** für Fließtext und Titel auf allen Trägerflächen (`window`, `paper`, `acetate`, `hover`) sowie `selection`/`action_new_bg` über alle 10 eigenständigen Glide-Themes (`light`, `dark`, `glass-light`, `glass-dark`, `dopamine`, `pixel`, `contrast-light`, `contrast-dark`, `minimal-light`, `minimal-dark`). Alle modalen Dialoge (`AppearanceDialog`, `PositionDialog`, `ReplayDialog`, `TextBoardDialog`, `EngineDialog`, `AboutDialog`, Auswahl- und Umwandlungsdialoge) nutzen `modal_session` zur Fokussicherung und -rückgabe.

---

## 3. Schutz der Connected-System-Markenidentität

Glide Shell ist ausschließlich technisches Desktop-Fundament. Die visuelle Produktidentität bleibt vollständig bei **Connected System – Think in connections**:

- **Markenzeichen:** Orthogonales Kettensignet, App-Icon und Wortmarke in *Manufacturing Consent Regular* ([`src/chess_and_chains/ui/brand_assets/`](../../src/chess_and_chains/ui/brand_assets/)).
- **Schachfiguren & Bretter:** Inhaber-SVGs V.02 (Vorderansicht), Draufsicht-SVGs, PNG-Fallbacks und 3D-Marmorbrett ([`src/chess_and_chains/ui/piece_assets/`](../../src/chess_and_chains/ui/piece_assets/)).
- **Puzzle Atlas:** Kartografische Routenansicht im Puzzle Lab (`ui/atlas.py`) mit Knoten- und Statusrollen.
- **Ausdrücklich ausgeschlossen:** Glide-Logos, Gismo-Maskottchen, Glide-To-do-Aufgabenlayouts oder Glide-Violett (`#9E4AC8`).

---

## 4. Prüf- und Abnahmerahmen

- **Automatisierte Prüfungen:** Kontrastprüfung (`theme.contrast_ratio`), Fenstergeometrie (`window_geometry.clamp`), 2-Fenster-Layout-/Knopfschutz bei `860 × 700` und `1280 × 800`, 64-px-Symbolleiste, Kompaktmodus (`480 × 560`), Dichtestufen (1200 / 1000 / 800 / 700), Hover-Zustände, 24-Zeichen-Beschriftung und hohe Tk-Schriftskalierung in `tests/test_glide_shell_integration.py` und `tests/test_app_integration.py`.
- **Manuelle Sichtabnahme (getrennt ausgewiesen):** Physische Prüfung unter Windows/macOS/Linux bei 100/150/200 % Systemskalierung und mit Screenreader (NVDA/VoiceOver).

---

## 5. Vollständige Glide-Designsprache, Canvas-Komponenten & Anpassung (V.0.3.0)

**Stand: 24.11.2026 · Implementierungsstatus: IMPLEMENTED · TESTED**

### 5.1 Glide v1.0.2 Themes, Akzente, Hintergründe & Typografie

In [`src/chess_and_chains/ui/theme.py`](../../src/chess_and_chains/ui/theme.py) sind sämtliche Vor-Glide-Pergament-/Gelb-Weiß-Standards (`#FAF6EC`, `#EFE8D8`, `#FFFCF4`, `#F4C400`) vollständig durch die neutralen Glide-v1.0.2-Paletten ersetzt (`light`: `#F5F5F7`/`#FFFFFF`, `dark`: `#111113`/`#1C1C1E`, Primärakzent Cobalt `#086FD6`/`#2C95FF`):

| Anpassungsdimension | Umfang & Optionen | API / Persistenz |
|---|---|---|
| **Themes (10 + System)** | `light`, `dark`, `glass-light`, `glass-dark`, `dopamine`, `pixel`, `contrast-light`, `contrast-dark`, `minimal-light`, `minimal-dark` (+ `system`, Alias `w06-provisional`) | `THEMES`, `resolve_theme()`, `settings.theme_id` |
| **Themenfarbe (8 Rollen)** | `accent`, `clear`, `due_action`, `export`, `flag`, `delete`, `import`, `muted` | `ACCENT_CHOICES`, `with_accent()`, `derive_board_colors()`, `settings.accent_choice` |
| **Brettdarstellung (entkoppelt)** | Design (`standard`, `marble`, `custom`), Perspektive (`2d`, `3d`), Figuren (`front`, `top`), Orientierung (`white`, `black`) | `MarbleBoardCanvas`, `Marble2DArtwork`, `settings.board_design_choice`, `settings.board_perspective`, `settings.piece_view` |
| **Hintergrundtönung (10 Rollen)** | `default`, `surface` sowie 8 abgeleitete Akzenttönungen | `BACKGROUND_CHOICES`, `with_background()`, `settings.background_choice` |
| **Eckenradius (4 Stufen)** | `large` (`18 px`), `standard` (`12 px`), `subtle` (`6 px`), `flat` (`0 px`) | `RADIUS_CHOICES`, `settings.radius_choice` |
| **Schriftgröße & -stärke** | Größe: `compact` (`0.9×`), `standard` (`1.0×`), `large` (`1.15×`); Stärke: `auto`, `standard`, `bold` | `FONT_SCALE_CHOICES`, `FONT_WEIGHT_CHOICES`, `font_spec()` |
| **Verhalten** | `animations_enabled`, `hints_visible` | `Settings`, `AppearanceDialog` |

### 5.2 `RoundedSurfaceCard` & `RoundedButton` mit Trägerflächen-Blending

- **`RoundedSurfaceCard` (`theme.py`):** Zeichnet abgerundete Kartenflächen (`fill_color`, `outline_color`, dynamisches `radius`) auf einem `tk.Canvas` mit Außenfarbe `bg_color` des jeweiligen Elternelements. Eingesetzt für `header_card`, `_side_slot`, `_board_slot`, `_rail_slot` (`bg_color=theme.window`) sowie `atlas_section` (`bg_color=theme.paper`).
- **`RoundedButton` (`theme.py`):** Zeichnet abgerundete Pill-Schaltflächen über `rounded_rect_points()`, aktualisiert beim Theme-Wechsel seinen äußeren Canvas-Hintergrund auf `carrier_bg` (statt der Knopffüllfarbe), sodass runde Ecken nahtlos in der umgebenden Karte verschwinden. Eingesetzt in Seitenleiste, Kopfleiste und im linken `TabRail`.
- **`GlideRadiobutton`, `GlideCheckbutton` & `ThemedAutoScrollbar` (`glide_shell.custom_controls`):** Steuern Spielmodus-Wahl, 3D-Marmoransicht sowie sämtliche Bildlaufleisten einschließlich `ReplayDialog` und `TextBoardDialog`.

### 5.3 `AppearanceDialog` & Live-Propagation

Der modale Einstellungsdialog [`AppearanceDialog`](../../src/chess_and_chains/ui/appearance_dialog.py) (`Cmd/Ctrl+,`, Kopfleisten-Zahnrad, Ansicht-Menü) bietet Live-Vorschau (`RoundedSurfaceCard` + `RoundedButton`), ruft `ChessApp.apply_appearance()` auf und persistiert alle Werte atomar nach `settings.json`:
- `install_ttk_theme(root, palette)` färbt verbleibende `ttk`-Dialogsteuerelemente und Listen konsistent um.
- **`install_ttk_theme(root, palette)` (`theme.py`):** Aktiviert unter macOS/Desktop explizit das `clam`-Theme für `ttk.Style`, damit alle `ttk`-Dialogsteuerelemente (`TButton`, `Glide.TButton`, `Glide.New.TButton`, `TEntry`, `Glide.TEntry`, `Glide.TCombobox` inkl. Dropdown-Listen) im Dark Mode keine hellen nativen Aqua-Flächen mit weißem Text erzeugen (`contrast_ratio >= 4,5:1`).
- **Umwandlungsdialog (`app.py`, `_choose_promotion`):** Nutzt einheitlich breite Canvas-basierte `RoundedButton`-Karten statt nativer `tk.Button` (welche unter macOS Aqua dunkle Hintergründe verwarfen), inklusive voller `ThemePalette`-Farben, `font_spec`, `radius`, Links/Rechts/Return/Escape-Steuerung und Fokusrückgabe ans Brett über `modal_session`.
- `board.set_theme()`, `marble_board.set_theme()`, `atlas.set_theme()`, `RoundedSurfaceCard.set_theme()` und `RoundedButton.set_theme()` aktualisieren alle Zeichenflächen ohne Fenster-Neustart; `derive_board_colors()` leitet abgestimmte `square_light`-/ `square_dark`-Feldfarben aus der aktiven Themenfarbe und dem Theme-Modus ab und färbt Marmor-SVGs (`Marble2DArtwork`) dezent unter Erhalt von Maserung und Kontrast (benutzerdefinierte SVG-Bretter bleiben unverändert).
- **Exakte Markierungszentrierung (`board.py`, `marble_board.py`):** 2D-Felder werden ganzzahlig gerastert (`square_bounds`, `square_center`), sodass normale Zugpunkte, Schlagringe, Auswahl, letzter Zug, Tastaturfokus, Hinweise und Schachwarnungen konzentrisch und pixelgenau auf `(x0 + x1) / 2, (y0 + y1) / 2` sitzen (bzw. in 3D auf dem projizierten Feldmittelpunkt `projected_square_center()`).

### 5.4 Echte Pixel-Rundung statt eckiger Vor-Glide-Rahmen

Gegenüber V.0.2.0 entfallen die eckigen `tk.Frame`-Schattenkästen (`_sheet_pair`) und `tk.Button`-Reiter vollständig: Sowohl die großen Arbeitsflächen als auch sämtliche Primär-, Sekundär- und Navigationsknöpfe nutzen echte Pixel-Radien (`18 / 12 / 6 / 0 px`) auf Canvas-Basis und umgehen damit die native `ttk`-Radiusbeschränkung auf macOS Aqua, Windows und Linux.

### 5.5 Dynamische Anzeige geschlagener Figuren & Materialvorteil

Im Brettbereich (`board_sheet`) befinden sich oberhalb und unterhalb des Schachbretts zwei kompakte, ruhige Materialanzeigen ([`CapturedMaterialBar`](../../src/chess_and_chains/ui/captured_material.py)):
- **Fachberechnung (`chess/material.py`):** Reines Fachmodell (`calculate_captured_material`), abgeleitet aus der Zughistorie der `ChessGame`-Instanz (Punkte: Bauer 1, Springer 3, Läufer 3, Turm 5, Dame 9; König ungeschlagen). Deckt en passant, Schlagumwandlungen, geschlagene umgewandelte Damen, Undo/Redo und unhistorische FEN-Stellungen ab.
- **Darstellung:** Verwendet die originalen Chess-&-Chains-SVGs als 18-px-Miniaturen mit Originalfarben. Gleiche Figurentypen werden platzsparend gruppiert und mit Mengenangabe (z. B. `×2`) versehen; Sortierung nach Bauer → Springer → Läufer → Turm → Dame.
- **Themenfarbe-Vorteilspille (`+N`):** Zeigt ausschließlich beim führenden Spieler die relative Punktedifferenz (`+N`) in der aktiven Themenfarbe (WCAG >= 3:1) an; bei Gleichstand entfällt die Zahl.
- **Orientierung & Wiedergabe:** Schläge erscheinen immer auf der Seite des schlagenden Spielers (Normalorientierung: Schwarz oben, Weiß unten; bei Brettdrehung vertauscht); dieselbe Logik synchronisiert Zug für Zug in der Partiewiedergabe ([`ReplayDialog`](../../src/chess_and_chains/ui/replay.py)).
