# Design System Brief – Chess & Chains

**Status: PARTIALLY DECIDED.** [Connected System](CONNECTED_SYSTEM.md) und Manufacturing Consent für Wortmarke und große Überschriften sind vom Inhaber festgelegt. Die Figuren sind für die App unter MPL-2.0 freigegeben. Die folgende W06-Exploration dokumentiert die Entstehung. Weitere Einzelfreigaben stehen im [Owner-Review](OWNER_DESIGN_REVIEW.md).

## Ziel

Eigenständige, hochwertige Desktop-UI zwischen konzentriertem Schachspiel und persönlicher Werkstatt, weder Standard-Chess.com- noch Lichess-Klon. `Chains` als möglicher abstrakter Leitgedanke für Varianten, taktische Muster und Lernprogression.

## Konzeptionelle Design-Tokens (nicht final)

- `color.surface`, `color.panel`, `color.board.light`, `color.board.dark`, `color.accent`, `color.focus`, `color.check`, `color.legalMove`, `color.hint`.
- `type.display`, `type.body`, `type.mono`; jede Schrift auf Lizenz und Runtime-Verfügbarkeit prüfen.
- `motion.quick`, `motion.board`, `motion.reduced`; System-Reduce-Motion respektieren.
- `spacing`, `radius`, `border`, `elevation`, `density`, `board.scale` als neutrale Settings.

## W06-Prototyp und Gestaltungsverlauf

- **Layered reference manual** war die ursprüngliche W06-Studie für Brett und Steuerblatt. Der aktuelle Prototyp integriert Connected System, Wortmarke und Atlas of Moves. Q-003 ist für Rechte und App-Lizenz entschieden. Konkrete Brettmotive und weitere Freigaben laufen über Q-004/Q-014.
- Als verbindliches UI-Fundament nutzt Chess & Chains **Glide Shell 0.6.2** (Glide `v1.0.2`, Commit `7dcd8dc04366f88943fa17827882cef4d81421b8`) gemäß [ADR-002](../decisions/ADR-002_SHELL_REUSE.md). Der portable Gestaltungs- und Interaktionsvertrag steht in [`src/glide_shell/DESIGN_RICHTLINIEN.md`](../../src/glide_shell/DESIGN_RICHTLINIEN.md) und wird durch den projekteigenen Vertrag [`GLIDE_DESIGN_CONTRACT.md`](GLIDE_DESIGN_CONTRACT.md) (P1–P6, B15, B11, B01/B16, B03, B10/B12/B14, WCAG 2.2 AA Light/Dark) mit der **Connected System**-Markenidentität verbunden. Übernommen werden ausschließlich neutrale Shell-Mechanismen und Gestaltungsprinzipien; **keine Glide-Produktmodelle, Aufgabenlogik oder Glide-Markenassets**.
- Tk bietet hier keine echte Widget-Transparenz; die Acetat-Anmutung wird deshalb mit einer deckenden Tönung dargestellt (`ThemePalette` für Light und Dark in `ui/theme.py`). Systemschriften (`TkDefaultFont`, `TkFixedFont`) werden über `custom_controls`-Provider registriert.

## UI-Kernansichten

1. **Play:** Brett + Bot-Schwierigkeit + Zugliste + Undo/Pause/Neustart (nur zulässig); minimaler Fokusmodus.
2. **Puzzle Lab:** Brett + Rating/Theme-Filter + Fortschritt, Hinweise und Lösung getrennt.
3. **Game Library:** lokale Partien, PGN/FEN Import/Export, Such- und Filteransichten.
4. **Settings/Appearance:** Brett- und Figurenset, Theme, DPI, Sprache, Sound, Datenpfad, lokale Engine-Auswahl.
5. **Analysis** (später): Zugbewertungen und visualisierte Ketten, ausdrücklich nur im Nachspiel-/Analysemode.

## Grafikpipeline

- `design/source/` – editierbare Illustrator-/Affinity-/Figma-/SVG-/PDF-Quelldateien, soweit lizenzfrei für Veröffentlichung; keine vertraulichen Kundendateien.
- `assets/chess_pieces/source_svg/` – Provenienz und Einstieg zu den Figuren. Die 24 Laufzeit-SVGs und beide PNG-Atlanten liegen unter `src/chess_and_chains/ui/piece_assets/`. Die editierbaren V.02-Prüfbögen liegen unter `design/source/chess_pieces/`.
- `assets/boards/source/` – Brettmuster/Texture/Shape-Quellen, `assets/boards/runtime/` – optimierte Assets.
- `assets/branding/` – aus den drei Logo-Mastern generierte App-Icons (PNG, ICO, ICNS), Favicon, Emblem- und Signet-Exporte ([Logo-Vertrag](../../design/01_Logo/README.md)).
- `marketing/source/` – editable Social/Website/Store-Assets, `marketing/exports/` – erzeugte Ausgabe (aus .gitignore).
- `references/inspiration/` – URLs, Designanalysen, Rechtebeurteilung. Kein unlizenzierter Screenshot-Import.

## Visuelle QA

Vier Testauflösungen inkl. Retina, 100/150/200% DPI, Farbsehschwäche/Kontrast, Tastaturfokus, aktive Auswahl, Schachgebot und mögliche Züge, Dark/Light, alternativer Figurensatz, niedrige Animationsstufe. Im aktiven Spiel niemals UI-Funktionen verstecken, die Zugregeln betreffen.

## Fragen

Siehe Q-003, Q-004, Q-005, Q-014, Q-020. Exakte Brandfarben und Schriften bleiben Owner-Entscheidungen. Die Logos hat der Inhaber am 26.11.2026 als drei Master geliefert.

## Weitere eigenständige Richtungen (W04-Vorschläge, nicht ausgewählt)

1. **Minimal / präzise:** viel ruhige Fläche, klare Koordinaten, sparsame
   Zustandsfarben und eine zurückhaltende Statuszeile. Der Brettfokus ist
   wichtiger als Funktionsdichte.
2. **Modern / expressiv:** eigenes Figuren-/Brettset steht sichtbar im Zentrum;
   Akzent und Mikrofeedback werden erst mit den Owner-Assets und
   Accessibility-Kontrastwerten bestimmt.
3. **Chains / analytisch:** abstrakte Knoten-/Linienmetapher für Varianten,
   Taktikmotive und Lernpfade; keine Kettenillustration oder fremde
   Produktanordnung kopieren.

Dieser Vergleich dokumentiert die Exploration. Den gewählten Stand beschreibt [Connected System](CONNECTED_SYSTEM.md).

## Textuelle Wireframes (Vorschläge)

### Play

```text
[Play] [Puzzle Lab] [Games] [Appearance]
[Lokale Engine / Status] [Preset] [New game]
[Zugstatus] [8×8 Brett mit Koordinaten] [Zugliste]
[Undo] [Resign/Finish] [Save/Export]
```

Engine-Auswahl zeigt nur vorhandene lokale Engines; keine Auto-Installation
oder Netzwerkannahme. Bei fehlender Engine darf kein Bot-Spiel-CTA so wirken,
als sei es startbereit.

### Puzzle Lab

```text
[Lokales Puzzle-Pack / Herkunft] [Rating >= 1000] [Thema] [Filter]
[Aufgabenstatus] [8×8 Brett] [Hinweis] [Lösung / nächstes Puzzle]
[Lokal gespeicherter Fortschritt]
```

Pack-Metadaten und Offline-Verfügbarkeit sichtbar halten. Das Brett zeigt die
Position nach dem ersten Gegenzug der Puzzle-Zeile.

### Appearance

```text
[Brettvorschau] [Figurensatz] [Brettstil] [Theme] [Scale]
[Quelle/Rechte-Status] [Reset] [Preview / Apply]
```

Vorschau bleibt von Rechten freigegebener lokaler Assets abhängig. Ein leeres
Assetverzeichnis wird nicht mit Fremd-/Dummy-Bildern kaschiert.

### Settings

```text
[Language: DE/EN] [Data location: platform default]
[Local engine path: choose / validate] [Network: no required services]
[Accessibility: keyboard / contrast / motion] [About / Licenses]
```

Engine-Pfad und optionale Netzwerkfunktionen bleiben bis zu den jeweiligen
Owner-/Lizenzentscheidungen Vorschläge.

## Abnahmekriterien für spätere UI-Arbeit

- Kernaktionen per Tastatur, sichtbarer und assistiver Fokus, Escape-Verhalten
  bei Dialogen und klare Fehlermeldungen.
- Inhalte und Brett bleiben bei 100/150/200 % Skalierung nutzbar; keine
  kritischen Statusinformationen ausschließlich über Farbe vermitteln.
- Systemmodus und Reduced Motion respektieren; Animationen dürfen die
  Zuginteraktion nicht verzögern.
- Tests auf den tatsächlich unterstützten Windows-/macOS-Versionen; Screenshots
  nur von eigenen, realen Builds und mit dokumentiertem Datum.
