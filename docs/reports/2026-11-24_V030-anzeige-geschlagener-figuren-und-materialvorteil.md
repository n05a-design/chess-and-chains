# Abnahmebericht – Anzeige geschlagener Figuren & Materialvorteil (Prompt 4)

**Datum:** 2026-11-24  
**Version:** V.0.3.0  
**Status:** IMPLEMENTED / TESTED  
**Commit:** anstehend auf `main`  
**Referenz:** Prompt 4 (`# CHESS & CHAINS – Anzeige geschlagener Figuren und Materialvorteil`)

---

## 1. Übersicht & Zielerreichung

In Chess & Chains V.0.3.0 wurde das Schachbrett um eine dynamische, platzsparende Anzeige der geschlagenen gegnerischen Figuren und der daraus resultierenden Materialdifferenz (`+N`) erweitert.

### Kernanforderungen & Abnahme

1. **Fachliche Domänenlogik (`chess.material`):**
   - Reine, Tk-freie Berechnung (`calculate_captured_material`) in [`src/chess_and_chains/chess/material.py`](../../src/chess_and_chains/chess/material.py).
   - Punktwerte: Bauer 1, Springer 3, Läufer 3, Turm 5, Dame 9; König ungeschlagen.
   - Differenzberechnung: `capture_score_white` vs `capture_score_black`.
   - Ausschließlich der führende Spieler erhält `+N` (bei 0 bzw. Gleichstand entfällt die Zahl; niemals negative Zahlen oder Gesamtsummen als Vorteil).
   - Vollständige Abdeckung aller Sonderfälle: En passant, Schlagumwandlungen, geschlagene zuvor umgewandelte Damen (9 Pkt), Undo/Redo, PGN-Import, FEN ohne Zughistorie (keine erfundenen Schläge).
2. **Kompakte Benutzeroberfläche (`CapturedMaterialBar`):**
   - Zwei Leisten im Brettbereich oberhalb und unterhalb des Bretts in [`src/chess_and_chains/ui/captured_material.py`](../../src/chess_and_chains/ui/captured_material.py).
   - Figuren erscheinen auf der Seite des schlagenden Spielers in ihrer Originalfarbe (White = hell, Black = dunkel mit Rand).
   - Eindeutige Spielerzuordnung: `○ Weiß` bzw. `● Schwarz`.
   - Platzsparende Multiplikatoren (z. B. `×2`, `×4`) bei gehäuften Schlägen; Sortierung Bauer → Springer → Läufer → Turm → Dame.
   - Vorteilspille (`+N`) in aktiver Themenfarbe (Themenfarben-Kontrast >= 3:1).
   - Vollständige Hell- und Dunkelmodus-Unterstützung über alle 10 Glide-Themes.
   - Tooltip mit Aufschlüsselung der Punktewerte (`material.advantage_tooltip` / `material.no_advantage_tooltip`).
3. **Brettdrehung & Partiewiedergabe:**
   - Normalorientierung (`white`): Schwarz oben, Weiß unten.
   - Gedrehte Orientierung (`black`): Weiß oben, Schwarz unten.
   - In [`src/chess_and_chains/ui/replay.py`](../../src/chess_and_chains/ui/replay.py) laufen die Materialleisten Zug für Zug synchron mit der Historie.

---

## 2. Testabdeckung & Prüfprotokoll

- **Unit-Tests (`tests/test_captured_material.py`):** 17/17 Tests erfolgreich:
  - Keine Schläge / Ausgangsstellung
  - Weiß schlägt Bauer (+1)
  - Weiß schlägt Bauer, Schwarz schlägt Läufer (Schwarz +2)
  - Gleichwertige Schläge (keine Zahl)
  - Weiß schlägt Dame, Schwarz Turm (Weiß +4)
  - En passant
  - Reine Umwandlung (0 Schläge)
  - Schlagumwandlung (Punkte der geschlagenen Figur)
  - Geschlagene umgewandelte Dame (9 Punkte)
  - Undo & Redo von Schlagzügen
  - Importierte FEN ohne Historie
  - PGN-Import
  - Partieneustart (`new_game`)
  - Initialzustand im GUI
  - Brettdrehung und dynamischer Leistentausch im GUI
  - Undo/Redo im GUI
  - Partiewiedergabe (`ReplayDialog`)
- **Regressionsprüfung (`tests/test_glide_shell_integration.py`):** `test_36` verifiziert die vollständige End-to-End-Integration inklusive Theme-Vererbung, dynamischem Canvas-Rendering und Vorteilspille.
- **Selbsttest Glide Shell 0.6.2:** 13/13 Checks bestanden.
- **Starter-, Richtlinien- und Link-Prüfungen:** Alle PASS.
