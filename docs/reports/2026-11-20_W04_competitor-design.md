# W04 – Konkurrenz-, Design- und Assetrecherche

**Stand:** 2026-11-20 · **Work Package:** W04 · **Status:** Research-Proposal,
nicht Owner-abgenommen

## Auftrag und Quellenbasis

W04 verlangt belegte Wettbewerbsbeobachtungen, drei eigene Designrichtungen,
textuelle Wireframes, vorsichtige Marketingtexte und nachvollziehbare
Assetprovenienz. Die Recherche wurde auf offizielle Produktseiten und
GitHub-Projektmetadaten beschränkt; URLs und SHAs stehen in
`docs/research/SOURCES.md`.

Geprüfte Produkte: Lucas Chess, En Croissant, ChessX, Scid vs. PC, PyChess,
Lichess und Chess.com. Für En Croissant und PyChess wurden außerdem die
GitHub-Metadaten am jeweils genannten Upstream-Commit aufgenommen. Die
Lichess-Puzzle-Seite nennt CC0, 6,193,530 rated puzzles, das Update vom
2026-11-11 und das CSV-/FEN-Schema, in dem FEN vor dem gegnerischen Zug steht.
Es wurden keine Datensätze heruntergeladen.

## Befunde und Grenzen

- Die Wettbewerbsanalyse trennt direkt auf Seiten sichtbare Angaben von
  Vermutungen und nicht verifizierten Funktionen. Insbesondere wurden keine
  Apps installiert und Offline-Nutzung, Bot-Auswahl, Puzzle-Suche, Themes,
  Export, Accessibility oder Usability nicht praktisch getestet.
- Lucas Chess bewirbt 57 vorbereitete Engines und verschiedene Trainingsarten;
  En Croissant beschreibt Analyse, Datenbank und Downloadmanager; ChessX und
  Scid vs. PC beschreiben Datenbank-/Engine-Funktionen; PyChess wird als
  Desktop-Client beschrieben. Diese Produktseiten belegen keine aktuelle
  Offline-Erstabnahme.
- Die Hypothese „offline, fokussiert, visuell anpassbar“ ist nicht als
  Wettbewerbsvorteil oder Marktlücke nachgewiesen. Die tabellarischen
  Featurelücken heißen „nicht verifiziert“, nicht „Funktion fehlt“.
- Es wurden keine fremden Screenshots, Logos, Markennamen als Assets, Texte,
  Quelltexte oder Puzzledateien ins Projekt übernommen.

## Designvorschläge

`docs/design/DESIGN_SYSTEM_BRIEF.md` enthält drei nicht ausgewählte
Designrichtungen: minimal/präzise, modern/expressiv und Chains/analytisch.
Farbwerte, Wort-/Bildmarke und Fonts bleiben unentschieden. Die vier textuellen
Wireframes behandeln Play, Puzzle Lab, Appearance und Settings; spätere
Implementierung soll Keyboard, Fokus, Kontrast, 100/150/200-%-Scaling und
Reduced Motion abnehmen.

Die Quellenbeobachtungen in `references/inspiration/REFERENCE_BOARD.md` sind
textuell und abstrakt; `docs/design/ASSET_REGISTER.csv` vermerkt explizit,
dass keine Wettbewerbermedien übernommen wurden. Eigene SVG-Figuren und
Owner-Assets bleiben bis zur Bestätigung von Autor, Quelle und Rechten
gesperrt. Kein Mockup oder Screenshot wurde erzeugt.

## Marketingvorschläge

`docs/marketing/LAUNCH_COPY.md` enthält einen aktuellen GitHub-About-/Topics-
und SEO-Vorschlag, der das Repository als Planungsstand und nicht als
spielbare App beschreibt. Frühere Aussagen zu kostenloser Distribution,
Offline-Funktion, lokalen Engines, SVG-Anpassbarkeit und Rätseln sind sichtbar
als noch zu konkret gekennzeichnet. Es werden keine Downloads, Bot-Elo oder
100-%-Offline-Funktion behauptet.

## Offene Fragen und Gates

Q-003, Q-004, Q-014 und Q-020 bleiben offen; ihre Vorschlagsnotizen wurden
geschärft, nicht als Owner-Entscheidungen gesetzt. Keine Marken-/Font-
Entscheidung, Assetfreigabe, Produktpositionierung oder UI-Richtung wurde
angenommen. ADR-001/ADR-002 und deren unabhängige Lizenz-/Shell-Gates bleiben
unverändert. Kein Code, Produktasset oder Glide-Modul wurde hinzugefügt.

Die Foundation- und W00–W03-Arbeit bleibt lokal. `project-manifest.json` und
die Work-Package-Matrix führen weiterhin die Starterstatuswerte; W04 wird erst
nach Projekt-Abnahme dort aktualisiert.

## Nachweise

Die Recherche selbst ist dokumentarisch. Nach den Dokumentänderungen wurden
folgende lokale Prüfungen ausgeführt:

- `python3 -m unittest discover -s tests -v` — Exit 0, 4 Tests bestanden
- `python3 scripts/verify_starter.py` — Exit 0, Strukturprüfung bestanden
- `python3 scripts/verify_document_links.py` — Exit 0 (relative Markdown-Links;
  Anker und externe URLs werden nicht validiert)
- `python3 -m compileall -q src app scripts tests` — Exit 0
- `git diff --check` — Exit 0 nach Entfernen nicht notwendiger
  Markdown-Hardbreak-Leerzeichen aus den Wireframes

Kein CI-Lauf, Release-, Offline- oder Plattformtest wurde ausgeführt. Branch:
`it568-chess-chains-bootstrap`; Basis-HEAD zum Arbeitsbeginn:
`e50494a151576caad9d37dd4f62903d782846bb3`. Änderungen bleiben lokal; kein
Commit, Push, PR oder Merge zum Zeitpunkt der Berichterstellung.
