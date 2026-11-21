# Chess & Chains – Einstieg

Der aktuelle Entwicklungsstand steht im [Mastermanifest](MANIFEST.md). Die
[deutsche README](README.de.md) erklärt den Start der Tk-App. Mit
`python -m chess_and_chains --version` lässt sich die Version nach der
Installation prüfen. Für neue Arbeit im vorhandenen Repository gelten
[AGENTS.md](AGENTS.md) und die Prioritäten der [Roadmap](docs/roadmap/ROADMAP.md).
Die [Agentenberichte](docs/reports/README.md) enthalten Git- und Testnachweise.

## Historische Foundation-Anleitung (F0)

**Stand:** 19.11.2026 · **Status:** Planungs-/Repository-Baseline, **kein spielbares Produkt** · **Sprache:** Deutsch (intern), Englisch + Deutsch (öffentlich).

Dieses ZIP ist für die **Neuanlage** von `n05a-design/chess-and-chains` bestimmt. Es ist **nicht** als bereits erstelltes GitHub-Repository, implementierte Schach-App, getestete Engine-Integration oder freigegebene Installer-Version zu verstehen.

## In 10 Schritten verwenden

1. ZIP entpacken. Den **Inhalt dieses Ordners**, nicht das ZIP und nicht den übergeordneten Ordner, in ein neues GitHub-Repository `n05a-design/chess-and-chains` auf Branch `main` übernehmen.
2. Vor Veröffentlichung `docs/legal/LICENSE_STRATEGY.md`, `THIRD_PARTY_NOTICES.md` und `docs/questions/OPEN_QUESTIONS.md` lesen. Keine fremden Binärdateien oder geschützte Assets unbesehen hinzufügen.
3. `README.md`, `README.de.md`, `LICENSE`, `AGENTS.md`, `.github/copilot-instructions.md` bereits enthalten.
4. Projektstruktur und Aufgaben in `MANIFEST.md`, `project-manifest.json` und `docs/roadmap/ROADMAP.md` prüfen.
5. Terminal: `python -m unittest discover -s tests -v` und `python scripts/verify_starter.py` ausführen (benötigt kein Internet und keine externen Python-Pakete).
6. Copilot in **Agent-/Workspace-Kontext** öffnen und `prompts/00_MASTER_BOOTSTRAP.md` vollständig ausführen lassen.
7. Erst dann nacheinander die einzelnen Prompts `01` bis `12` beauftragen; jeder Prompt hat ein klar definiertes Freigabe-Gate.
8. Eigene SVG-Originale nach `assets/chess_pieces/source_svg/` kopieren, Brettgestaltung nach `assets/boards/source/`. Rechte und Quellen in `docs/design/ASSET_REGISTER.csv` dokumentieren. Rohentwürfe bleiben in `design/source/`.
9. Aus Glide/Steps **nur nach dokumentierter Freigabe** komponentenweise übernehmen; `integrations/glide_shell/` ist absichtlich reserviert, aber leer.
10. Weitere Fragen mit ID in `docs/questions/OPEN_QUESTIONS.md` sammeln; Entscheidungen ausschließlich über ADRs unter `docs/decisions/` bestätigen.

## Erste, bereits vorgeschlagene Produktregeln

- Offline-first (kein Konto, kein Pflichtserver, keine Telemetrie), kostenloser offizieller Vertrieb.
- Desktop Windows/macOS zuerst, Linux als Ziel mit separat nachzuweisender Abnahme.
- Zunächst ein vollständig legales Standard-Schachspiel gegen lokal angebundene UCI-Engine; weitere Engines später.
- Puzzle-Lab mit **Lichess-Puzzle-Rating >= 1000** (nicht identisch mit Spieler-Elo). Daten zunächst separat importierbar, nicht im Starterpaket.
- Die vorhandenen SVG-Figuren und das noch entstehende Brett sind primäre Designinputs; keine Fremd-Screenshots in die Repo kopieren.
- **Lizenzentscheidung ist ausdrücklich NICHT abgeschlossen.** Eigener Quellcode zunächst unter MPL-2.0; Stockfish/`python-chess` GPL und die Auslieferungsarchitektur sind vor einem gebündelten Release rechtlich zu prüfen.

## Dokumententypen

`[BESCHLOSSEN]` = nur durch ausdrückliche Owner-Entscheidung. `[VORGESCHLAGEN]` = Arbeitsrichtung, noch keine Freigabe. `[OFFEN]` = Frage/Gate. `[NACHGEWIESEN]` = mit Commit/Test/Artefakt belegt. **Keine automatische Hochstufung** durch Copilot.

**Startpunkt für Copilot:** [`prompts/00_MASTER_BOOTSTRAP.md`](prompts/00_MASTER_BOOTSTRAP.md)
