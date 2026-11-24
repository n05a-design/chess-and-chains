# Chess & Chains – Designvertrag (Connected System × Glide Shell)

Stand 23.11.2026 · Chess & Chains V.0.0.1 · Glide Shell 0.6.2 (Glide v1.0.2, Commit `7dcd8dc04366f88943fa17827882cef4d81421b8`)

Dieses Dokument verbindet den portablen Gestaltungs- und Interaktionsvertrag der **Glide Shell** ([`src/glide_shell/DESIGN_RICHTLINIEN.md`](../../src/glide_shell/DESIGN_RICHTLINIEN.md)) mit der Marken- und Produktidentität von **Chess & Chains** ([`CONNECTED_SYSTEM.md`](CONNECTED_SYSTEM.md)).

---

## 1. Übernommene Grundsätze der Glide Shell (P1–P6)

| Grundsatz | Bedeutung für Chess & Chains | Konkrete Umsetzung |
|---|---|---|
| **P1 Funktioniert selbstverständlich** | Systemkonventionen gelten ohne Umwege | 6 barrierefreie Themes (`light`, `dark`, `contrast-light`, `contrast-dark`, `minimal-light`, `minimal-dark`) plus `system_appearance`; `Escape` schließt modale Dialoge; `Tab`/`Shift+Tab` navigiert zyklisch vom Brett auf den linken Reiter und zurück; Standardkürzel (`Strg`/`Cmd+Z`, `Y`, `N`) über `app_host` |
| **P2 Form folgt Funktion** | Farbe = Rolle, Größe = Wichtigkeit | `theme.ThemePalette` trennt `window`, `paper`, `acetate`, `ink`, `muted_ink`, `brand_blue`, `chrome_yellow` (Primäraktion), `confirm`, `delete`, `line`, `input_border`, `hover`, `selection` |
| **P3 Keine Funktion doppelt** | Ein führender Aktionsweg pro Absicht | Menüleiste (`desktop_adapter.build_menu_tree`) und `action_picker` lesen denselben Menübaum mit ausgerichteten Häkchen (`action_picker.check_label`) |
| **P4 Kein Platz verschwenden** | Spielfeld dominiert die Fläche | 2-Fenster-Layout: Linke Seitenleiste (`column=0`, minsize=328) mit Schmalmodus (64-px-Symbolleiste mit Schnellaktionen) oder vollständigem Ausblenden; rechtes Brettarbeitsblatt (`column=1`, `weight=1`) spannt bei ausgeblendeter Leiste auf 100 % der Fensterbreite |
| **P5 Nur das Wesentliche** | Ruhiger Standardzustand | Klare Trennung in *Play*, *Moves* und *Puzzles*; Kompaktmodus (`480 × 560`) für paralleles Arbeiten neben anderen Fenstern mit Geometriewiederherstellung |
| **P6 Geringe Komplexität** | Stabile Begriffe und Muster | Durchgängige DE/EN-Kataloge (`i18n/catalog.py`), 24-Zeichen-Knopfbeschränkung (`clip_button_text`), einheitliche Dialogführung über `modal_session` |

---

## 2. Verbindliche Einzelvorgaben (B-Regeln)

- **B15 – Bedienelemente schützen:** Hauptfenster mindestens `860 × 700` (`NORMAL_MIN`), im Kompaktmodus mindestens `480 × 560` (`COMPACT_MIN`). Schaltflächen im Play-Panel schalten bei schmaler Breite oder hoher Schrift-Skalierung (150–200 %) automatisch von zwei auf eine Spalte um und stellen Fokussichtbarkeit per Scrollbar sicher.
- **B11 – Informationshierarchie:** Statuszeile und Brett behalten Priorität; Fehlermeldungen und Metadaten in Dialogen werden mit `text_fit.clip` / `wraplength` sauber gekürzt statt abgeschnitten. Knopfbeschriftungen sind auf 24 Zeichen begrenzt (`clip_button_text`), Titellängen auf 40 Zeichen (`TITLE_MAX_CHARS`).
- **B05 / B07 – In-App-Logo & Kopfleisten-Anatomie:** Das Connected-System-Kettensignet ist klickbar und öffnet den barrierefreien Info-Dialog (`AboutDialog`). Darunter befinden sich bündig der Ansichtstitel (`theme.view_title`) und die Modus-Statuszeile (`self.subtitle_row`). Rechts liegen einheitlich 38-px hohe Bedienelemente mit 8-px Abstand und bündigem rechtem Abschluss.
- **D55 / D61 / D66 / D68 – Responsive Dichtestufen & Breakpoints:**
  - Breite: `≥ 1120 px` vollständige Kopfleiste mit allen Aktionen; `900..1119 px` Kompaktknöpfe mit Mehr-Aktions-Menü (`⋯`); `< 900 px` Minimalkopf (Logo ausgeblendet für linksbündigen Titel, Menü `⋯`).
  - Automatische Verschmälerung: Unterhalb von `760 px` Fensterbreite wechselt eine sichtbare Seitenleiste automatisch auf die 64-px-Symbolleiste und kehrt ab `≥ 860 px` in die volle Breite zurück.
  - Höhe: `≥ 850 px` volle Innenabstände (`12 px`); `780..849 px` kompakte Abstände (`8 px`); `< 780 px` Minimalabstände (`6 px`).
- **B01 / B16 – Unmittelbare Rückmeldung:** Keine `time.sleep`-Blockade im Tk-Thread; Engine-Berechnungen und lokale Paketimporte laufen in Hintergrund-Threads und melden über `GameController.poll()` im `window_lifetime.AfterScope`-Takt.
- **B03 – Reduzierte, unterbrechbare Bewegung:** Übergänge verwenden `motion.Transitions` (≤ 150 ms) innerhalb von `app.scope` und enden sauber bei Fensterabbau.
- **B10 / B12 / B14 – Semantische Symbole & Hover:** Eindeutige Tastaturnavigation auf der 64-px-Leiste (`♟`, `≡`, `◈`, `＋`, `↶`, `↷`, `⇅`, `»`) mit Pfeiltasten, Eingabetaste und Leertaste. Neutrale Schaltflächen bieten visuelles Hover-Feedback über `theme.hover`.
- **WCAG 2.2 AA & Kontrast:** `theme.contrast_ratio` sichert mindestens **4,5:1** für Fließtext und Titel auf allen Trägerflächen (`window`, `paper`, `acetate`, `hover`) über alle 6 Themes (`light`, `dark`, `contrast-light`, `contrast-dark`, `minimal-light`, `minimal-dark`). Alle modalen Dialoge (`PositionDialog`, `ReplayDialog`, `TextBoardDialog`, `EngineDialog`, `AboutDialog`, Auswahl- und Umwandlungsdialoge) nutzen `modal_session` zur Fokussicherung und -rückgabe.

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
