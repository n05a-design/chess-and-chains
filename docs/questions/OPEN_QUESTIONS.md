# Offene Rückfragen & Entscheidungsregister

**Single Source of Truth für offene Owner-Fragen.** Stand: 20.11.2026. Fragen zuerst sammeln, nicht durch Copilot als beschlossene Fakten ausgeben. Entscheidung nach Owner-Antwort in passendes ADR übertragen, danach hier als `CLOSED` mit Link markieren.

| ID | Priorität | Rückfrage an Owner | Vorgeschlagene Default-Richtung | Gate/Status |
| --- | --- | --- | --- | --- |
| Q-001 | BLOCKER | Ist **MPL-2.0 für den App-Quellcode** wichtiger als ein vollständig eingebauter Stockfish-Installer? Falls Konflikt: GPLv3 akzeptabel? | Owner wählte zunächst B als Implementierungsrichtung, danach A zur Prüfung eines möglichen GPL-konformen Gesamtvertriebs. Die endgültige Lizenz-/Vertriebsentscheidung bleibt offen. | ADR-001 / OPEN – A-Recherche; keine Bundle-/Release-Freigabe |
| Q-002 | BLOCKER | Ist **sofort gegen Bots spielen nach Erstinstallation** zwingend oder wäre eine separat zu installierende Engine akzeptabel? | Owner bestätigte am 20.11.2026: Bot muss direkt nach App-Installation offline spielbereit sein. A wird als möglicher Weg geprüft; keine Engine oder Downloads ohne weitere Freigabe. | ADR-001 / CLOSED für die Produktanforderung; Umsetzungsweg bleibt RELEASE BLOCKER |
| Q-003 | HIGH | Können deine bestehenden **SVG-Schachfiguren** samt grafischen Masterdateien öffentlich unter einer benannten Lizenz bereitgestellt werden? | Nicht verwenden oder veröffentlichen, bis Autor, Quelle und Änderungs-/Weitergaberechte je Datei bestätigt sind; Originale getrennt registrieren. | ADR-005 / OPEN |
| Q-004 | HIGH | Gibt es bereits **Brett-Design, Logo, Farbwerte, Schriftstile oder Brand-Guides**? | Zuerst Owner-Masterdateien inventarisieren; bis dahin neutrale austauschbare Tokens statt erfundener Markenwerte/Fonts. | ADR-005 / OPEN |
| Q-005 | HIGH | Tk/Tk9 strikt beibehalten oder bei klaren SVG-/DPI-Nachteilen nach prototypischem Vergleich Qt zulassen? | Owner wählte am 20.11.2026 Tk als W06-Basis und beauftragte die CairoSVG-Plattform-/Offline-Paketierungsprüfung; Qt wurde nicht gewählt. Die CairoSVG-Runtime bleibt bis zu vollständiger Paketierungs-, Plattform- und Lizenzprüfung ungeprüft. | ADR-002 / CLOSED für W06-Stackrichtung; CairoSVG-Integration weiterhin gesperrt bis Prüfung |
| Q-006 | HIGH | Soll die Glide-Shell später **eigenes Repository/Paket** werden oder aus Glide in Einzelmodulen übernommen werden? | Paket-Bridge ohne Kopie | ADR-002 / OPEN |
| Q-007 | MEDIUM | Welche Plattformen haben **Release-Priorität**: Windows x64, Mac ARM64, Mac Intel, Linux? | Windows + Mac zuerst | ADR-006 / OPEN |
| Q-008 | MEDIUM | Welche **Ratingspanne** oberhalb 1000 bevorzugst du (1000–2000 oder offen bis 3000+)? | Filter bis 3000+ | ADR-003 / OPEN |
| Q-009 | MEDIUM | Wieviele Aufgaben sollen direkt mitgeliefert werden (z. B. 20k/50k)? Wie groß darf der Download sein? | 20k initial; später Packs | ADR-003 / OPEN |
| Q-010 | MEDIUM | Möchtest du **deutsch/englisch ab Start**, welche Sprache ist Startstandard? | EN + DE; OS-Locale | W10 / OPEN |
| Q-011 | MEDIUM | Welche **Spielzeitmodi** für MVP: ohne Uhr, klassisch, Blitz? | ohne Uhr + 10/15 Minuten | MVP / OPEN |
| Q-012 | MEDIUM | Sind lokale **Spielerprofile** für eine Person oder mehrere Profile auf einem Rechner nötig? | 1 Profil + Erweiterung | ADR-004 / OPEN |
| Q-013 | MEDIUM | Darf es optionale **Online-Downloads für Updates/Assets** geben, oder muss jede Installation absolut netzwerkfrei sein? | Keine ungefragten Downloads | Produkt / OPEN |
| Q-014 | LOW | Soll die Wortmarke `Chess & Chains` ein `&`-Signet, ein Kettensymbol oder abstrakte Schach-Motive verwenden? | Drei eigenständige Richtungen erst mit Owner-Assets explorieren; kein Signet aus Wettbewerberdesigns ableiten. | Design / OPEN |
| Q-015 | HIGH | Wessen Name/Organisation steht im **Copyright-/Marken-/Impressum-Kontext**? | Bis zu einer Owner-Angabe keinen Rechtsträger oder Copyrightinhaber erfinden; vor Veröffentlichung belegen. | Legal / OPEN |
| Q-016 | MEDIUM | Ist eine bezahlte **Apple Developer ID** für signierten/notarisierten Mac-Vertrieb vorhanden? | Nicht voraussetzen | Release / OPEN |
| Q-017 | MEDIUM | Soll das Projekt erst privat in GitHub entstehen und später public werden? | Öffentlich erst nach Asset-/Lizenzprüfung | Repo / OPEN |
| Q-018 | MEDIUM | Gibt es einen bestimmten **OneDrive-Quellordner** für editierbare Artwork-/Marketing-Dateien, der ausschließlich verlinkt werden soll? | Local/Cloud nur per explizitem Pfad | Assets / OPEN |
| Q-019 | HIGH | Sollen Copilot/andere Agenten GitHub **pushen und PRs erstellen** dürfen oder nur lokal vorbereiten? | Keine externen Writes ohne Erlaubnis | Governance / OPEN |
| Q-020 | MEDIUM | Soll Chess & Chains im späteren Produktkatalog mit einer eigenen Website-/Downloadseite oder derselben Markenfamilie wie Glide/Steps auftreten? | Eigenständige Produktidentität als Arbeitshypothese; Zugehörigkeit zu anderen Marken weder behaupten noch voraussetzen. | Marketing / OPEN |
| Q-021 | HIGH | Darf der klar gekennzeichnete **Mock-Bot** (keine Schach-KI) in Entwicklungs-/Vorschau-Builds als Standard-Gegner erscheinen, solange ADR-001 offen ist, oder soll der Bot-Modus ohne echte Engine ausgeblendet werden? | Nur in Entwicklungsbuilds sichtbar, deutlich gekennzeichnet; in Releases ausblenden bis echte Engine geprüft ist. | ADR-001 / W07 / OPEN (N02) |
| Q-022 | MEDIUM | Darf ein Agent den **offiziellen Lichess-Puzzle-Export (CC0)** lokal herunterladen, um den Importer mit Realdaten zu prüfen (Pack außerhalb des Repos)? | Erst nach ausdrücklichem Owner-Opt-in; Download nicht im Repo, nur Prüfsumme und Importbericht versionieren. | ADR-003 / W08 / OPEN (N02) |
| Q-023 | MEDIUM | Sollen die sechs Bot-Stufen (Level 1–6) nach Kalibrierung mit **gemessenen Elo-Spannen** beschriftet werden oder dauerhaft neutral bleiben? | Neutral bis ein reproduzierbarer Benchmark (`docs/qa/BOT_CALIBRATION_PLAN.md`) vorliegt. | ADR-007 / OPEN (N02) |
| Q-024 | MEDIUM | Darf der Agent den Entwicklungsbranch **pushen und einen PR** nach `main` erstellen (Konkretisierung von Q-019 für N02)? | Nur nach ausdrücklicher Freigabe im Chat; kein Merge. | Governance / Freigabe galt PR #2. Für den lokalen Folgebranch offen. |

## Antwort-Format

`Q-XXX | Entscheidung: ... | Begründung: ... | Datum: ... | Entscheider: ... | ADR: ...`.

## Neue Fragen

Bei jeder neuen offenen Frage **ID + Priorität + konkreten Einfluss + Gate + Owner** hinzufügen. Es ist zulässig, mit nicht blockierenden Fragen weiterzuarbeiten; blockierende Fragen dürfen nicht durch Annahmen erledigt werden.
