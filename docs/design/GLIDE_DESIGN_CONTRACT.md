# Chess & Chains – Designvertrag (Connected System × Glide Shell)

Stand 23.11.2026 · Chess & Chains V.0.0.1 · Glide Shell 0.6.2 (Glide v1.0.2, Commit `7dcd8dc04366f88943fa17827882cef4d81421b8`)

Dieses Dokument verbindet den portablen Gestaltungs- und Interaktionsvertrag der **Glide Shell** ([`src/glide_shell/DESIGN_RICHTLINIEN.md`](../../src/glide_shell/DESIGN_RICHTLINIEN.md)) mit der Marken- und Produktidentität von **Chess & Chains** ([`CONNECTED_SYSTEM.md`](CONNECTED_SYSTEM.md)).

---

## 1. Übernommene Grundsätze der Glide Shell (P1–P6)

| Grundsatz | Bedeutung für Chess & Chains | Konkrete Umsetzung |
|---|---|---|
| **P1 Funktioniert selbstverständlich** | Systemkonventionen gelten ohne Umwege | Hell/Dunkel (`system_appearance`), `Escape` schließt modale Dialoge, `Tab`/`Shift+Tab` und Pfeiltasten navigieren Brett und Listen, Standardkürzel (`Strg`/`Cmd+Z`, `Y`, `N`) über `app_host` |
| **P2 Form folgt Funktion** | Farbe = Rolle, Größe = Wichtigkeit | `theme.ThemePalette` trennt `window`, `paper`, `acetate`, `ink`, `muted_ink`, `brand_blue`, `chrome_yellow` (Primäraktion), `brand_red` (aufgelöste Rätsel) |
| **P3 Keine Funktion doppelt** | Ein führender Aktionsweg pro Absicht | Menüleiste (`desktop_adapter.build_menu_tree`) und `action_picker` lesen denselben Menübaum |
| **P4 Kein Platz verschwenden** | Spielfeld dominiert die Fläche | Schachbrett in Spalte 0 (`weight=7`, `minsize=450`), kompakte Kopfleiste, seitliche Steuerkarte einspaltig/zweispaltig adaptiv |
| **P5 Nur das Wesentliche** | Ruhiger Standardzustand | Klare Trennung in *Play*, *Moves* und *Puzzles*; optionale Ansichten (*Textbrett*, *Replay*, *3D-Marmorbrett*) auf Anforderung |
| **P6 Geringe Komplexität** | Stabile Begriffe und Muster | Durchgängige DE/EN-Kataloge (`i18n/catalog.py`) und einheitliche Dialogführung über `modal_session` |

---

## 2. Verbindliche Einzelvorgaben (B-Regeln)

- **B15 – Bedienelemente schützen:** Hauptfenster mindestens `860 × 700` über `window_geometry.clamp`. Schaltflächen im Play-Panel schalten bei schmaler Breite oder hoher Schrift-Skalierung (150–200 %) automatisch von zwei auf eine Spalte um und stellen Fokussichtbarkeit per Scrollbar sicher.
- **B11 – Informationshierarchie:** Statuszeile und Brett behalten Priorität; Fehlermeldungen und Metadaten in Dialogen werden mit `text_fit.clip` / `wraplength` sauber gekürzt statt abgeschnitten.
- **B01 / B16 – Unmittelbare Rückmeldung:** Keine `time.sleep`-Blockade im Tk-Thread; Engine-Berechnungen und lokale Paketimporte laufen in Hintergrund-Threads und melden über `GameController.poll()` im `window_lifetime.AfterScope`-Takt.
- **B03 – Reduzierte, unterbrechbare Bewegung:** Übergänge verwenden `motion.Transitions` (≤ 150 ms) innerhalb von `app.scope` und enden sauber bei Fensterabbau.
- **B10 / B12 / B14 – Semantische Symbole:** Eindeutige Unicode-Marker und schachspezifische Vektorsymbole ohne rein dekorative Überladung.
- **WCAG 2.2 AA & Fokus:** `theme.contrast_ratio` sichert mindestens **4,5:1** für Fließtext und **3,0:1** für große Schriften sowohl im **Light-Theme** als auch im **Dark-Theme**. Alle modalen Dialoge (`PositionDialog`, `ReplayDialog`, `TextBoardDialog`, `EngineDialog`, Auswahl- und Umwandlungsdialoge) nutzen `modal_session` zur Fokussicherung und -rückgabe.

---

## 3. Schutz der Connected-System-Markenidentität

Glide Shell ist ausschließlich technisches Desktop-Fundament. Die visuelle Produktidentität bleibt vollständig bei **Connected System – Think in connections**:

- **Markenzeichen:** Orthogonales Kettensignet, App-Icon und Wortmarke in *Manufacturing Consent Regular* ([`src/chess_and_chains/ui/brand_assets/`](../../src/chess_and_chains/ui/brand_assets/)).
- **Schachfiguren & Bretter:** Inhaber-SVGs V.02 (Vorderansicht), Draufsicht-SVGs, PNG-Fallbacks und 3D-Marmorbrett ([`src/chess_and_chains/ui/piece_assets/`](../../src/chess_and_chains/ui/piece_assets/)).
- **Puzzle Atlas:** Kartografische Routenansicht im Puzzle Lab (`ui/atlas.py`) mit Knoten- und Statusrollen.
- **Ausdrücklich ausgeschlossen:** Glide-Logos, Gismo-Maskottchen, Glide-To-do-Aufgabenlayouts oder Glide-Violett (`#9E4AC8`).

---

## 4. Prüf- und Abnahmerahmen

- **Automatisierte Prüfungen:** Kontrastprüfung (`theme.contrast_ratio`), Fenstergeometrie (`window_geometry.clamp`), Layout-/Knopfschutz bei `860 × 700` und `1280 × 800`, Light/Dark/System-Theme-Auflösung und hohe Tk-Schriftskalierung in `tests/test_glide_shell_integration.py` und `tests/test_app_integration.py`.
- **Manuelle Sichtabnahme (getrennt ausgewiesen):** Physische Prüfung unter Windows/macOS/Linux bei 100/150/200 % Systemskalierung und mit Screenreader (NVDA/VoiceOver).
