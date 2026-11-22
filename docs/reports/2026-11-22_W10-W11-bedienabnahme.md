# W10/W11 – Spielaktionen und Bedienprüfung bei großer Schrift

**V.0.0.1 · 22.11.2026 · KI-gestützt.** Basis ist der
[Merge von PR #21](https://github.com/n05a-design/chess-and-chains/pull/21)
in `main` (`8d5bcc6d732d6de6d622aa2cf55d4981daf3b834`).

## Nachweis für den Merge

Der [Workflow auf main](https://github.com/n05a-design/chess-and-chains/actions/runs/44972693793)
lief nach dem Merge mit 14 erfolgreichen Jobs. Die beiden macOS-Kernjobs
bestanden. Je 69 GUI-Tests bestanden unter
[Python 3.11 / Aqua Tk 8.6.13](https://github.com/n05a-design/chess-and-chains/actions/runs/44972693793/job/137055703496)
und [Python 3.14 / Aqua Tk 9.0.5](https://github.com/n05a-design/chess-and-chains/actions/runs/44972693793/job/137055703412).
Beide Logs zeigen den bestandenen Test
`test_marble_switch_preserves_game_and_uses_projected_move_targets`.
Er prüft die laufende Partie, einen weiteren Zug in der Projektion,
Zugliste, Orientierung und Rückgängig/Wiederholen. Die separaten
AppKit-Prüfschritte für die FEN-Dateidialoge waren ebenfalls erfolgreich.

## Umsetzung

Im kleinen Fenster lagen beim deutschen Spielpanel mit 200 % Tk-Textskalierung
mehrere Textanforderungen über der Breite ihrer Schaltflächen. Der Platzbedarf
der längsten Wörter entscheidet nun anhand der Tk-Schriftmetriken über eine
oder zwei Spalten. Die Reihenfolge der Widgets bleibt gleich. Der vorhandene
Fokusmechanismus scrollt die fokussierte Aktion in den sichtbaren Bereich.

Die bestehende GUI-Matrix führt zwei zusätzliche Regressionen aus.

- **DE, 192 Tk-DPI, 860 × 700.** Wiederholen, Partiebibliothek und
  Engine-Auswahl in einer Partie mit vorhandenem Wiederholen-Verlauf
  nacheinander fokussieren. Breite für den Buttontext und vollständige
  Sichtbarkeit im scrollbaren Spielpanel prüfen.
- **EN, 144 Tk-DPI, 860 × 700.** Marmoransicht mit Enter aktivieren,
  `e2e4` mit der Bretttastatur spielen und mit Tab und Pfeiltaste in die
  Zugliste wechseln. Den ausgeführten Zug in der sichtbaren Liste prüfen.

## Lokaler Nachweis

Auf dem Implementierungscommit `b576fedfcc20ce57d43e561f56e2e4d65f930ef1`
bestand `py -3.14 -m unittest discover -s tests -q` mit **253 Tests**,
Exitcode 0 und 130,832 Sekunden. Umgebung Windows 11 Pro x64
(Build 26300), Python 3.14.7, Tk 9.0.4, verpflichtendes Tk-Display,
`ResourceWarning` als Fehler und Fault Handler aktiv. Der Volltest
enthält beide neuen Regressionen und den ursprünglichen
Marmor-Ansichtswechsel. Die neue Implementierung ist lokal geprüft.

## Native Abnahme

Die automatisierten Tk-DPI-Tests verwenden eine feste Fenstergröße und
eingestellte Tk-Textskalierung. Die Betriebssystemskalierung, physische
Tastatur und Screenreader-Ansagen werden auf den Zielgeräten abgenommen.
Je Durchgang Build-Commit, OS, Tk-Version, Auflösung, native Skalierung,
Fenstergröße, Sprache, Eingabegerät und gegebenenfalls Screenreader-Version
notieren. Die folgenden Schritte für Normal- und Marmorbrett sowie für DE
und EN ausführen. Auf macOS die angebotenen nativen Skalierungsstufen
protokollieren.

| Ablauf | Erwartete Beobachtung | Ergebnis auf Zielgerät |
| --- | --- | --- |
| Im kleinsten Fenster per Tab und Shift+Tab durch die Spielaktionen gehen. | Text bleibt lesbar. Jede fokussierte Aktion scrollt vollständig ins Bild. | Offen |
| Eine Partie per Tastatur beginnen. In die Marmoransicht wechseln, weiterziehen, zurückwechseln und Rückgängig/Wiederholen ausführen. | Sichtbarer Feldfokus, korrekte Züge, unveränderter Verlauf beim Wechsel. | Offen |
| Zugliste per Tab erreichen. Textbrett und Bibliothek öffnen und per Escape schließen. | Die Listen lassen sich per Tastatur bedienen. Nach dem Schließen eines Dialogs kehrt der Fokus zum Auslöser zurück, sofern er sichtbar ist. | Offen |
| Legalen Zug, Unterverwandlung und ein Demo-Rätsel mit physischem Ziffernblock prüfen. | Eingabe und Fokus stimmen mit der normalen Tastatur überein. | Offen |
| Mit NVDA unter Windows und VoiceOver auf macOS Feldbelegung, Zugstatus und Dialoge prüfen. | Tatsächliche Ansagen für Canvas und Textbrett getrennt protokollieren. Unangesagte Informationen mit Reproduktionsschritten festhalten. | Offen |

1. Die zusätzlichen GUI-Regressionen nach beauftragter Veröffentlichung
   in den Windows-, macOS- und Linux-Jobs auswerten.
2. Die manuellen Durchgänge auf den Zielgeräten protokollieren. Den
   Abnahmestatus erst anhand der beobachteten Ergebnisse aktualisieren.
3. Danach die nächsten ausführbaren Punkte aus der
   [Roadmap](../roadmap/ROADMAP.md) aufnehmen.

Datenformat und Laufzeitabhängigkeiten bleiben unverändert. Die Anpassung
der Spielaktionen lässt sich ohne Migration zurückbauen.
