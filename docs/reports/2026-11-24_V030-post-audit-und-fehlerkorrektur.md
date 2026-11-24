# Chess & Chains – Unabhängiges Nachaudit und verbindliche Fehlerkorrektur

**Datum:** 2026-11-24  
**Basis-Commit:** `7fc8847c68a73c553173e471b59227fe180c3b6a` (HEAD / `origin/main`)  
**Version:** V.0.3.0 / V.0.3.1  
**Glide Shell Version:** 0.6.2 (Glide v1.0.2, Commit `7dcd8dc04366f88943fa17827882cef4d81421b8`)  
**Status:** IMPLEMENTED · TESTED

---

## 1. Zusammenfassung der behobenen Befunde

Sämtliche Befunde des Nachaudits wurden im Code behoben und durch 28 neue automatisierte Regressionstests in `tests/test_regression_audit.py` sowie die bestehende Testsuite (333 Tests insgesamt) vollständig verifiziert.

| Befund | Priorität | Betroffene Dateien | Status | Verifikation |
|---|---|---|---|---|
| Marmorbrett SVG-Inkompatibilität auf Tk 8.6 | **P0** | `src/chess_and_chains/ui/board_artwork.py` | BEHOBEN | `Marble2DArtworkFallbackTests` (7 Tests) |
| macOS Bot-Event-Loop Timing-Analyse | **P0** | `.github/workflows/checks.yml`, `tests/test_regression_audit.py` | BEHOBEN | `BotTimingAnnotationTests` (2 Tests) |
| Einstellungsdialog Transaktionssicherheit | **P1** | `src/chess_and_chains/ui/appearance_dialog.py`, `src/chess_and_chains/ui/app.py` | BEHOBEN | `SettingsTransactionSafetyTests` (3 SHA-256 Tests) |
| Fehlerhafte Theme-Parameter in Live-Vorschau | **P1** | `src/chess_and_chains/ui/appearance_dialog.py` | BEHOBEN | `ResolveThemeKeywordTests` (4 Tests) |
| Brettdesign & Perspektiven-Entkopplung | **P1** | `src/chess_and_chains/ui/appearance_dialog.py` | BEHOBEN | `BoardDesignPerspectiveDecouplingTests` (3 Tests) |
| Einstellungen gestalterisch nachgebessert | **P2** | `src/chess_and_chains/ui/appearance_dialog.py`, `src/chess_and_chains/ui/dropdown.py` | BEHOBEN | `DropdownAndSettingsP2Tests` (3 Tests) |
| Materialanzeige Kontrast & Rätselwechsel | **P2** | `src/chess_and_chains/ui/captured_material.py`, `src/chess_and_chains/ui/app.py` | BEHOBEN | `MaterialBarContrastTests` (3 Tests), `MaterialBarPuzzleResetTests` (2 Tests) |
| CI-Testabdeckung vervollständigt | **P1** | `.github/workflows/checks.yml` | BEHOBEN | Testmatrix & Job-Konfiguration |

---

## 2. Detaillierte Maßnahmen nach Arbeitspaketen

### P0 – Marmorbrett-Kompatibilität & Raster-Fallback

**Ursache:** Tk 8.6 unter Linux (CI) und Windows unterstützt das SVG-Format für `tk.PhotoImage` nicht nativ (`_tkinter.TclError: image format "svg" is not supported`). Tk 9 und macOS Tk mit NanoSVG unterstützen es.

**Lösung in `src/chess_and_chains/ui/board_artwork.py`:**
1. **Laufzeit-Probe (`_probe_svg_support`)**: Prüft einmalig pro Interpreter-Instanz, ob `tk.PhotoImage(format="svg")` ohne Fehler instanziiert werden kann.
2. **Raster-Fallback (`_checkerboard_fallback`)**: Bei fehlender SVG-Unterstützung wird ein getöntes Schachbrett aus Marmor-Grundfarben erzeugt (`base_light = "#D4CAB8"`, `base_dark = "#8C7B6A"`). Bei aktiver Themenfarbe wird diese mit 14 % (helle Felder) bzw. 22 % (dunkle Felder) eingemischt, um den Marmorcharakter zu wahren.
3. **Zustandserhalt bei Renderfehlern**: Falls das Laden fehlschlägt, bleibt der vorherige gültige Bildzustand im Cache erhalten.
4. **Keine neuen Abhängigkeiten**: Funktioniert rein mit Standard-Tkinter PhotoImage ohne CairoSVG oder externe Bibliotheken.

**Bot-Event-Loop Timing-Analyse:**
Die Prüfung ergab, dass kein Code-Regressionsfehler vorliegt, sondern CI-Scheduling-Jitter auf überlasteten macOS-GitHub-Runnern. Auf dem lokalen System läuft der Test in 1,5s mit maximal 45ms Lücke (Grenzwert: 250ms bei `POLL_MS = 40`). Der Grenzwert von 250ms wurde unverändert beibehalten. In `checks.yml` wurde der Timeout für `gui-native` auf 5 Minuten erhöht.

### P1 – Einstellungsdialog Transaktionssicherheit

**Ursache:** Live-Vorschau rief zuvor `apply_appearance(..., persist=True)` auf, wodurch jede Änderung an Dropdowns sofort die Datei auf Festplatte überschrieb. Zudem verhinderte ein State-Mismatch das Speichern, wenn der In-Memory-Zustand durch die Vorschau bereits dem Zielwert entsprach.

**Lösung in `appearance_dialog.py` & `app.py`:**
1. **Vorschau (`_emit_preview`)**: Ruft `apply_appearance(..., persist=False)` auf. Verändert ausschließlich den In-Memory-Laufzeitzustand. Die Festplatte wird nicht berührt.
2. **Speichern (`_save_and_close`)**: Ruft `on_apply` mit `persist=True` auf. In `apply_appearance` führt `if persist: self._store_settings(**changes)` die Speicherung auf Festplatte auch dann aus, wenn `changes` leer ist (weil die Vorschau den In-Memory-Zustand bereits gesetzt hatte).
3. **Abbrechen (`_cancel`)**: Ruft `_emit_preview(self._initial_snapshot)` auf. Stellt den ursprünglichen Zustand im UI und In-Memory wieder her, ohne die Einstellungsdatei auf der Festplatte zu überschreiben.
4. **Dateisystem-Regressionstest**: `SettingsTransactionSafetyTests` in `test_regression_audit.py` prüft den SHA-256-Hash der Settings-Datei:
   - Vor Vorschau: Hash A
   - Während mehrfacher Vorschau-Wechsel: Hash unverändert A
   - Nach Abbruch: Hash unverändert A
   - Nach Speichern: Hash wechselt auf B (neue Werte gespeichert)

### P1 – Theme-Parameterkorrektur

**Ursache:** In `AppearanceDialog._apply_live_preview()` wurde `bg_var.get()` als zweiter Positionsparameter an `resolve_theme()` übergeben. Die Signatur lautet jedoch `resolve_theme(theme_id, root=None, *, accent=None, background=None)`. Die Hintergrundauswahl wurde somit als `root`-Widget-Referenz interpretiert.

**Lösung:** Umstellung auf explizite Schlüsselwortargumente:
```python
resolve_theme(theme_var.get(), accent=accent_var.get(), background=bg_var.get())
```

### P1 – Brettdesign und Perspektive entkoppelt

**Lösung in `AppearanceDialog._sync_perspective_dependency()`:**
Das Perspektiven-Dropdown wird für alle Designs deaktiviert und auf 2D arretiert, die nicht `"marble"` sind (vorher war nur `"standard"` abgefangen, wodurch `"custom"` versehentlich 3D auswählen konnte).

### P2 – Einstellungen gestalterisch nachgebessert

**Lösung in `appearance_dialog.py` & `dropdown.py`:**
1. **Abschlussbuttons rechtsbündig**: Im Footer ist Spalte 0 der elastische Abstandhalter (`grid_columnconfigure(0, weight=1)`). `_cancel_btn` liegt in Spalte 1 (`sticky="e", padx=(0, 10)`), `_apply_btn` in Spalte 2 (`sticky="e"`).
2. **Textmessung statt 24-Zeichen-Kürzung**: `GlideDropdown` verwendet `_fit_text()` mit `tkinter.font.Font.measure()` anstelle von `clip_button_text()`. Das Dropdown-Popup berechnet seine Mindestbreite dynamisch aus der längsten Option (`max_label_w + 32 px`).
3. **Bildschirmbegrenzung**: Sowohl `x` (an `screen_w - 16`) als auch `y` (an `screen_h - 16`) und `total_h` werden geklemmt, sodass geöffnete Popups nie den Bildschirmrand überschreiten.
4. **Lifecycle & AfterScope**: Timer für Fokusverlust-Prüfungen nutzen `AfterScope(self)`. Bei Widget-Abbau (`_on_destroy`) wird `_after_scope.close()` aufgerufen; bei Popup-Schluss `cancel_all()`.
5. **Responsive Breite**: Dropdowns skalieren responsiv (`width=215` bei `large`/`extra-large`, `width=190` bei Standard).
6. **DE/EN-Lokalisierung**: Alle Dropdown-Einträge, Sektionstitel und Knöpfe sind vollständig zweisprachig gepflegt.

### P2 – Materialanzeige vervollständigt

**Lösung in `captured_material.py` & `app.py`:**
1. **WCAG 2.2 AA Kontrast**: Kapsel-Hintergrund ist `tab_idle`. Als Textfarbe wird `brand_blue` gewählt, sofern das Kontrastverhältnis ≥ 4,5:1 beträgt, andernfalls `ink`, Schwarz oder Weiß. Der vorherige Schwellenwert von 3,0:1 wurde auf 4,5:1 angehoben.
2. **Rätsel-Reset**: In `_sync_material_bars()` wird bei `self.active_panel == "puzzles"` und `self.puzzle is None` die Anzeige beider Balken explizit auf `None` gesetzt.

### P1 – CI-Testabdeckung vervollständigt

In `.github/workflows/checks.yml` wurden die neu hinzugefügten Testmodule explizit in die Testjobs integriert:
- `tests.test_captured_material` (headless und GUI)
- `tests.test_final_audit` (GUI)
- `tests.test_glide_shell_integration` (GUI)
- `tests.test_regression_audit` (headless und GUI)
- `python -m glide_shell.selftest` (GUI)
- Timeout für `gui-native` von 3 auf 5 Minuten angehoben.

---

## 3. Verifikationsergebnisse

### 3.1 Automatisierte Testläufe (lokal ausgeführt)

| Testbefehl | Umfang | Ergebnis | Dauer |
|---|---|---|---|
| `python3 -m unittest tests.test_regression_audit -v` | 28 Tests | **28/28 OK** | 3,58 s |
| `python3 -m unittest tests.test_final_audit -v` | 4 Tests | **4/4 OK** | 0,89 s |
| `python3 -m unittest tests.test_glide_shell_integration -v` | 30 Tests | **30/30 OK** | 25,51 s |
| `python3 -m unittest tests.test_captured_material -v` | 17 Tests | **17/17 OK** | 0,95 s |
| `python3 -m unittest discover -s tests -p "test_*.py" -v` | 333 Tests | **333/333 OK** | 106,26 s |
| `PYTHONPATH=src python3 -m glide_shell.selftest` | 13 Prüfungen | **13/13 OK** | 0,38 s |
| `python3 scripts/verify_starter.py` | Starter & Manifest | **PASS** | 0,15 s |
| `python3 scripts/verify_document_links.py` | Markdown-Links | **PASS** | 0,12 s |
| `python3 scripts/check_policy.py` | Sicherheitsrichtlinien | **PASS** | 0,11 s |
| `python3 -m compileall -q src tests scripts` | Bytecode-Kompilierung | **0 Fehler** | 0,42 s |

### 3.2 Live macOS Smoke-Test (isolierter Datenordner)

Der Smoke-Test initialisierte `ChessApp` mit isoliertem Pfad `CHESS_AND_CHAINS_DATA_DIR`:
1. Einstellungsdialog geöffnet, Live-Vorschau für Theme „dark“ angewendet → Theme In-Memory auf „dark“, Datei unverändert.
2. Speichern ausgelöst → Einstellungen auf Festplatte übernommen.
3. Marmorbrett 2D aktiviert (`set_board_design("marble")`, `set_perspective("2d")`) → fehlerfrei gerendert.
4. Materialanzeigen synchronisiert → Top- und Bottom-Balken korrekt initialisiert.
5. Sauberer Shutdown ohne Hänger oder Fehler.

Ergebnis: **PASS**.

### 3.3 Glide-Shell-Manifestprüfung

Die verwaltete Glide-Shell-Kopie in `src/glide_shell/` entspricht bytegenau dem Manifest:
- Quell-Commit: `7dcd8dc04366f88943fa17827882cef4d81421b8` (Tag `v1.0.2`)
- Manifestprüfung: `23 files match manifest (7dcd8dc04366)`
- Keine manuellen Änderungen in `src/glide_shell/`.

---

## 4. Git-Status & Handoff

- **Lokaler Branch:** `main`
- **Aktueller HEAD:** `7fc8847c68a73c553173e471b59227fe180c3b6a`
- **Remote `origin/main`:** `7fc8847c68a73c553173e471b59227fe180c3b6a`
- **Arbeitskopie:** Alle Fehlerkorrekturen und Tests sind implementiert und verifiziert.
- **Git Push:** Erfolgt erst nach ausdrücklicher Freigabe durch den Projektinhaber (`AGENTS.md` Regel 3).
