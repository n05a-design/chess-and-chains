# Connected System · Design- und Integrationsnachweis

**20.11.2026 · Codex · Windows 11 Pro x64, Build 26300 · Python 3.15.1 x64 · Tk 9.0.4 · Chrome 158.0.8127.37**

## Auftrag und Ausgangsstand

Direkter Auftrag „Markenkonstruktion → Variantenvergleich → deine Auswahl → Finalisierung der SVGs → Integration in die App“. Das angehängte Langbriefing diente als Designreferenz. Die Arbeitsauswahl wurde für die lokale App vorgenommen. Die Rechte- und Veröffentlichungsgates in ADR-005 bleiben offen.

| Inventar | Geprüfter Stand |
| --- | --- |
| Ursprünglicher Checkout | `OneDrive/Github/chess-and-chains` |
| Erste Arbeitsbasis | `codex/chess-and-chains-n02-functional-core` · `046bc2504c75126e2743e9ebbe41647bb4700ea1` |
| Remote | `origin` zeigt auf `n05a-design/chess-and-chains`. Die lokale Remote-Tracking-Referenz `origin/main` lag bei `df5e5d75922a85432a1cee645a89cb2be96f4c58`. |
| Arbeitsbaum vor Änderungen | 169 bereits sichtbare Modusänderungen `100755 → 100644` im Windows-Checkout und ein unversionierter Quellordner. Der inhaltliche Diff war vor Arbeitsbeginn mit `git -c core.filemode=false -c core.safecrlf=false status --short` leer außer diesem Quellordner. |
| Zielbasis nach GitHub-Abgleich | GitHub-`main` am bestätigten Merge `9249fca18194d1c66d23dd4f334954876b42aa87`. Der frühere N02-Remote-Branchstand `f8c30052a7e7115c55ae67f3e02f0d05029e7621` ist darin enthalten. |
| Integrations-Worktree | `codex/chess-and-chains-connected-system`. Enthält den Designkandidaten und die aktualisierten Tests, Layout-Sicherung und N02-Dokumentation aus `main`. |
| Rechte | Projekteigener Code unter MPL-2.0 nach Projektvertrag. Artwork und Marke separat nach ADR-005. Quellen, Hashes, Dateistatus und Schriftverweise im [Assetregister](../design/ASSET_REGISTER.csv). |

Das angehängte Langbriefing nannte abweichende Dateinamen. Tatsächlich lagen Link Lab, Atlas, Moodboard, Prompt und die Vektorübersicht vor. Affinity-Datei und Rasteransicht wurden ergänzend inventarisiert. Während der Arbeit erschien der PNG-Export im Ordner `Archiv` und ein JPG-Export am bisherigen Ort. Die sichtbaren Dateien wurden im Register erfasst. Änderungen im Referenzordner wurden nicht durch diesen Auftrag ausgeführt.

## Lieferstand

- **PROPOSED** · Fünf grafisch eigenständige [Brandboards und eine Vergleichstafel](../../design/concepts/connected-system-v01/) mit vergleichbaren Signets, App-Icons, Knoten, Brett und Bedienfläche. Die [Designentscheidung](../design/CONNECTED_SYSTEM.md) dokumentiert Synthese, Geometrie und Trade-offs.
- **PROPOSED** · [Editierbare SVG-Master](../../design/source/connected-system/), [Farb-, Geometrie- und Typografie-Tokens](../design/brand-tokens.json) und vier [Marketing-Anwendungen](../../marketing/source/). SVG-Texte bleiben editierbar. PNG-Vorschauen verwenden die verfügbaren System-Fallbacks.
- **Lokal im Arbeitsbaum implementiert** · [Tk-App](../../src/chess_and_chains/ui/app.py) mit sichtbarem Signet, Fenster-Icon, horizontalen nativen Register-Buttons, harmonisierter Palette und [Atlas](../../src/chess_and_chains/ui/atlas.py) mit lokalen Zustandsdaten. Die bestehenden Platzhalterfiguren und Brettkoordinaten werden relativ zur Pixelgröße der Felder gesetzt. Der Spiel- und Rätselbereich nutzt dieselbe Scroll-/Fokuslogik. Die Paneele stammen aus der bestehenden Tk-App.
- **OPEN** · Owner-Review, Marken-, Artwork- und Veröffentlichungsrechte, Originalfiguren, native macOS-/Linux-Prüfung, Betriebssystem- und Monitor-DPI-Wechsel, Screenreader und öffentliche Release-Abnahme. Dark Mode, Appearance und Home liegen als Designstudien vor.

## Ausgeführte Prüfungen

Alle Befehle liefen im oben genannten Arbeitsbaum auf dem genannten Windows-System. Die erste Arbeitsbasis und die aktualisierte Integrationsbasis sind gesondert ausgewiesen.

| Zeitpunkt | Befehl / Verfahren | Exitcode und Ergebnis |
| --- | --- | --- |
| Baseline vor Änderungen | `python -m unittest discover -s tests -v` | 1. 170 Tests, 1 Fehler. `test_tk_event_loop_keeps_running_while_bot_thinks` maß ein Maximum von 0,316 s gegen 0,250 s. |
| Frühe Integration | `python -m unittest discover -s tests -p test_app_integration.py -v` | 0. 25 Tests erfolgreich. |
| Zwischenstand vor Lebenszykluskorrektur | `python -m unittest discover -s tests -v` | 1. 172 Tests, 2 Fehler. `test_close_terminates_engine_process` überschritt 3 s mit 13,932 s, begleitet von Tk-Destruktorwarnungen im Worker. Der Bot-Zeittest maß 0,721 s. |
| Nach Lebenszykluskorrektur, parallel zum visuellen Smoke | `python -m unittest tests.test_app_integration -v` | 1. 27 Tests, 1 Fehler. Der Bot-Zeittest maß 0,726 s. Der Engine-Shutdown-Test bestand. |
| Isolierter Gegencheck | `python -m unittest tests.test_app_integration.BotVerticalSliceTests.test_tk_event_loop_keeps_running_while_bot_thinks tests.test_app_integration.BotVerticalSliceTests.test_close_terminates_engine_process -v` | 0. Beide Tests erfolgreich. |
| Wiederholung vor Wechsel auf GitHub-Basis | `python -m unittest discover -s tests -v` auf `046bc25` plus Designänderungen und Lebenszykluskorrektur, sichtbarer Tk-Display erforderlich, `ResourceWarning` als Fehler | 0. 172 Tests in 94,176 s erfolgreich. |
| Neue Baseline nach Fetch | Drei gezielte Tk-Tests für Bot-Zeitverhalten, Shutdown und Filter auf unverändertem `9249fca` | 0. 3 Tests erfolgreich. |
| Windows-Vorschaulauf auf `9249fca` plus Designänderungen | `python %TEMP%/chess-chains-brand-smoke.py` | 0. Tk-Fenster in Deutsch, Registerwechsel mit Pfeiltaste, Haken nach gelöster Aufgabe, Kreuz nach aufgedeckter Lösung und Fokus-Scrollen im Rätselpanel. Mit je neuer Tk-Instanz wurden 100/150/200 % Tk-Skalierung bei 860 × 700 geprüft. |
| Integrationsstand auf `9249fca` | `python -m unittest discover -s tests -v` · Python 3.15.1, Tk 9.0.4 · `CHESS_AND_CHAINS_REQUIRE_DISPLAY=1`, `PYTHONWARNINGS=error::ResourceWarning` | 0. 172 Tests in 88,956 s erfolgreich. Kein Skip, kein gemeldeter Tcl-Destruktorfehler. |
| Zweite Python-Version auf `9249fca` plus Designänderungen | `py -3.14 -m unittest tests.test_board_ui tests.test_app_integration -v` · Python 3.14.7, Tk 9.0.4 · dieselben Umgebungsvariablen | 0. 38 Tests in 11,322 s erfolgreich. |
| Paketprüfung auf `9249fca` plus Designänderungen | `python -m pip wheel --no-build-isolation --no-deps --no-index --wheel-dir <Temp> .`, `python -m pip install --no-deps --no-index --target <Temp> <Wheel>`, Tk-Start mit importiertem Zielpaket, danach `python app/main.py --headless-check` mit Zielpaket im `PYTHONPATH` | 0. Wheel enthält beide SVGs und beide PNGs. Fenster-Icon, Signet und Atlas im installierten Paket geladen. Wheel-SHA-256 `f78c60ab78ba319b8ac59baf969fc3b4df12ef865748cd8c4cafcaed66edb385`. PNG-Fallback im Integrationstest durch simulierten fehlenden SVG-Decoder geprüft. |
| Statische Prüfungen im Integrations-Worktree | `python scripts/verify_document_links.py`, `python scripts/verify_starter.py`, `python scripts/check_policy.py`, `python -m compileall -q src app scripts tests`, `git -c core.filemode=false -c core.safecrlf=false diff --check` | Jeweils 0. |
| Abschließender Remote-Abgleich | `git ls-remote origin refs/heads/main` und `git rev-parse HEAD` | Beide meldeten `9249fca18194d1c66d23dd4f334954876b42aa87`. |

Die erste Sichtprüfung bei 150/200 % zeigte abgeschnittene Registertexte und bei 200 % übergroße Figurenbuchstaben. Größere Registerflächen, gemischte Schreibweise und feldbezogene Pixelgrößen wurden im Wiederholungslauf geprüft. [Spielansicht](../../design/concepts/connected-system-v01/previews/app-windows-spiel.png), [Atlas](../../design/concepts/connected-system-v01/previews/app-windows-atlas.png), [200-%-Vorschau](../../design/concepts/connected-system-v01/previews/app-windows-200.png)

Der erste GitHub-Push und der erste PR-Lauf für `0b3419ed47d09329c750190987672f46a44ec123` waren im nativen macOS-Job mit Python 3.11.9 rot. Der Test `test_play_panel_scrolls_to_focused_engine_settings_in_small_window` beobachtete `canvas.yview()[1] == 1.0`. Der einzeilige Hinweis mit automatischem Umbruch erzeugte dort keinen Überlauf. Die Testdaten verwenden jetzt explizite Zeilenumbrüche, damit der Test eine überlaufende Ansicht unabhängig von Schriftmaßen überprüft. Die Assertions zum Fokus und Scrollen bleiben erhalten. [Push-Job](https://github.com/n05a-design/chess-and-chains/actions/runs/44790177465/job/136475465581), [PR-Job](https://github.com/n05a-design/chess-and-chains/actions/runs/44790362800/job/136476101455)

## SVG- und Kontrastprüfung

- `python %TEMP%/chess-chains-brand-svg-qa.py` · Tk 9.0.4 und Chrome Headless 158.0.8127.37 · Exitcode 0 nach Korrektur der Screenshot-Pfade. Alle 23 SVGs als größenrichtige PNGs gerendert. XML, positive viewBoxes, eindeutige IDs je Datei, lokale Vektorgeometrie ohne Rastereinbettung und Textgrenzen geprüft. Sichtprüfung der Brandboards, kompakten Wortmarken, Atlas- und UI-Studien sowie Marketingmotive.
- Signet und App-Icon jeweils mit Tk 9 bei 16, 24, 32, 64, 128, 256 und 512 px geladen. Das Markenzeichen bleibt sichtbar, die beiden Durchgänge sind bei 16 px weniger deutlich. [Größenvergleich](../../design/concepts/connected-system-v01/previews/icon-groessen.png)
- Rechenprüfung der sRGB-Kontrastpaare · Text auf Creme 16,26:1, Text auf Gold 10,65:1, Creme auf Blau 6,56:1, Rot auf Creme 6,10:1, helle zu dunklen Brettfeldern 3,26:1. Die JSON-Farbrollen stimmen mit dem bestehenden Tk-Theme überein.

## Übergabe

1. [Owner-Review](../design/OWNER_DESIGN_REVIEW.md) am Variantenvergleich und in der App durchführen. Abnahme und Nutzungsrechte je Asset in ADR-005 dokumentieren.
2. Nach Rechteentscheidung ein Figurenset mit getrennten Ressourcen je Figur und Seite ausarbeiten und gegen die 12-Dateien-Schnittstelle prüfen. Lesbarkeit von Turm/Läufer und Dame/König in realen kleinen Feldern prüfen.
3. Vor öffentlicher Übernahme die native Windows/macOS/Linux-Matrix ausführen und die Markenassets im tatsächlichen Lieferformat inventarisieren.

**Git-Übergabe** · Der Owner hat den Push des Design-Branches und einen Pull Request gegen `main` beauftragt. Die nach Commit ausgeführten Prüfungen und der CI-Stand sind aus dem Pull Request nachvollziehbar. Bei Rückbau den Commit des Designkandidaten gezielt revertieren. Der erste Entwurfsstand mit den Originalreferenzen liegt im ursprünglichen Checkout.
