# Design System Brief – Chess & Chains

**Status: IDEA / DESIGN DISCOVERY.** Vorhandene SVG-Schachfiguren des Owners und zukünftiges Brett sind ausdrücklich **noch nicht im Repository enthalten**.

## Ziel

Eigenständige, hochwertige Desktop-UI zwischen konzentriertem Schachspiel und persönlicher Werkstatt, weder Standard-Chess.com- noch Lichess-Klon. `Chains` als möglicher abstrakter Leitgedanke für Varianten, taktische Muster und Lernprogression.

## Konzeptionelle Design-Tokens (nicht final)

- `color.surface`, `color.panel`, `color.board.light`, `color.board.dark`, `color.accent`, `color.focus`, `color.check`, `color.legalMove`, `color.hint`.
- `type.display`, `type.body`, `type.mono`; jede Schrift auf Lizenz und Runtime-Verfügbarkeit prüfen.
- `motion.quick`, `motion.board`, `motion.reduced`; System-Reduce-Motion respektieren.
- `spacing`, `radius`, `border`, `elevation`, `density`, `board.scale` als neutrale Settings.

## UI-Kernansichten

1. **Play:** Brett + Bot-Schwierigkeit + Zugliste + Undo/Pause/Neustart (nur zulässig); minimaler Fokusmodus.
2. **Puzzle Lab:** Brett + Rating/Theme-Filter + Fortschritt, Hinweise und Lösung getrennt.
3. **Game Library:** lokale Partien, PGN/FEN Import/Export, Such- und Filteransichten.
4. **Settings/Appearance:** Brett- und Figurenset, Theme, DPI, Sprache, Sound, Datenpfad, lokale Engine-Auswahl.
5. **Analysis** (später): Zugbewertungen und visualisierte Ketten, ausdrücklich nur im Nachspiel-/Analysemode.

## Grafikpipeline

- `design/source/` – editierbare Illustrator-/Affinity-/Figma-/SVG-/PDF-Quelldateien, soweit lizenzfrei für Veröffentlichung; keine vertraulichen Kundendateien.
- `assets/chess_pieces/source_svg/` – 12 grundlegende Figurensymbole als getrennte Dateien oder explizit dokumentierte Namespaces.
- `assets/boards/source/` – Brettmuster/Texture/Shape-Quellen, `assets/boards/runtime/` – optimierte Assets.
- `assets/branding/` – eigene Wort- und Bildmarke, App-Icons, Favicon, Avatar-Exports.
- `marketing/source/` – editable Social/Website/Store-Assets, `marketing/exports/` – erzeugte Ausgabe (aus .gitignore).
- `references/inspiration/` – URLs, Designanalysen, Rechtebeurteilung. Kein unlizenzierter Screenshot-Import.

## Visuelle QA

Vier Testauflösungen inkl. Retina, 100/150/200% DPI, Farbsehschwäche/Kontrast, Tastaturfokus, aktive Auswahl, Schachgebot und mögliche Züge, Dark/Light, alternativer Figurensatz, niedrige Animationsstufe. Im aktiven Spiel niemals UI-Funktionen verstecken, die Zugregeln betreffen.

## Fragen

Siehe Q-003, Q-004, Q-005, Q-014, Q-020. Exakte Brandfarben, Logo und Schriften bleiben Owner-Entscheidungen.
