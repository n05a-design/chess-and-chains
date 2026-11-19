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

## Eigenständige Richtungen (W04-Vorschläge, nicht ausgewählt)

1. **Minimal / präzise:** viel ruhige Fläche, klare Koordinaten, sparsame
   Zustandsfarben und eine zurückhaltende Statuszeile. Der Brettfokus ist
   wichtiger als Funktionsdichte.
2. **Modern / expressiv:** eigenes Figuren-/Brettset steht sichtbar im Zentrum;
   Akzent und Mikrofeedback werden erst mit den Owner-Assets und
   Accessibility-Kontrastwerten bestimmt.
3. **Chains / analytisch:** abstrakte Knoten-/Linienmetapher für Varianten,
   Taktikmotive und Lernpfade; keine Kettenillustration oder fremde
   Produktanordnung kopieren.

Kein Farbwert, Logo, Font oder Stil ist damit entschieden.

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
